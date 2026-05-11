"""
飞书多维表格一键建表脚本

用法：
  1. 先在飞书中手动创建一个多维表格（空白即可）
  2. 从 URL 中获取 APP_TOKEN：
     https://xxx.feishu.cn/base/APP_TOKEN?table=xxx
  3. 填写 .env 中的 FEISHU_APP_ID / FEISHU_APP_SECRET / BITABLE_APP_TOKEN
  4. python setup_bitable.py
  5. 将输出的 TABLE_ID 填回 .env

  ⚠️ 员工花名册表不会自动创建（通常对接现有 HR 表格），
     若需要新建，取消脚本末尾的注释即可。
"""

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")
BITABLE_APP_TOKEN = os.getenv("BITABLE_APP_TOKEN")
API_BASE = "https://open.feishu.cn/open-apis"

if not all([APP_ID, APP_SECRET, BITABLE_APP_TOKEN]):
    print("❌ 请先在 .env 中填写 FEISHU_APP_ID / FEISHU_APP_SECRET / BITABLE_APP_TOKEN")
    sys.exit(1)


async def get_token(client: httpx.AsyncClient) -> str:
    resp = await client.post(
        f"{API_BASE}/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
    )
    resp.raise_for_status()
    return resp.json()["tenant_access_token"]


async def create_table(
    client: httpx.AsyncClient,
    token: str,
    name: str,
    fields: list[dict],
) -> str:
    resp = await client.post(
        f"{API_BASE}/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables",
        headers={"Authorization": f"Bearer {token}"},
        json={"table": {"name": name, "fields": fields}},
    )
    if resp.status_code == 400 and "already exists" in resp.text:
        print(f"  ⚠️ 表 [{name}] 已存在，跳过")
        return ""
    resp.raise_for_status()
    data = resp.json()
    table_id = data.get("data", {}).get("table_id", "")
    print(f"  ✅ [{name}] → {table_id}")
    return table_id


async def main():
    # 表结构定义
    tables = {
        "员工花名册": [
            {"field_name": "feishu_open_id", "type": 1},
            {"field_name": "name", "type": 1},
            {"field_name": "department", "type": 1},
            {"field_name": "tenure_months", "type": 2},
        ],
        "轮次": [
            {"field_name": "round_id", "type": 1},
            {"field_name": "title", "type": 1},
            {"field_name": "status", "type": 1},
            {"field_name": "start_date", "type": 2},
            {"field_name": "end_date", "type": 2},
        ],
        "余额": [
            {"field_name": "round_id", "type": 1},
            {"field_name": "feishu_open_id", "type": 1},
            {"field_name": "coins_allocated", "type": 2},
            {"field_name": "coins_given", "type": 2},
            {"field_name": "coins_received", "type": 2},
        ],
        "明星墙": [
            {"field_name": "round_id", "type": 1},
            {"field_name": "department", "type": 1},
            {"field_name": "winner_name", "type": 1},
            {"field_name": "coins_received", "type": 2},
        ],
    }

    print(f"\n🔑 获取 tenant_access_token ...")
    async with httpx.AsyncClient(timeout=30) as client:
        token = await get_token(client)
        print(f"   ✅ 成功\n")

        results = {}
        for t_name, t_fields in tables.items():
            print(f"📦 创建表 [{t_name}] ...")
            tid = await create_table(client, token, t_name, t_fields)
            if tid:
                results[t_name] = tid

    print(f"\n{'='*50}")
    print(f"📋 建表完成！将以下内容写入 .env：\n")
    for t_name, tid in results.items():
        if t_name == "员工花名册":
            print(f"  EMPLOYEES_TABLE_ID={tid}")
        elif t_name == "轮次":
            print(f"  ROUNDS_TABLE_ID={tid}")
        elif t_name == "余额":
            print(f"  BALANCES_TABLE_ID={tid}")
        elif t_name == "明星墙":
            print(f"  STARWALL_TABLE_ID={tid}")
    print(f"\n{'='*50}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
