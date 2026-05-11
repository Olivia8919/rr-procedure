import time
import httpx
from settings import settings

_client: httpx.AsyncClient | None = None
_token: tuple[str, float] | None = None  # (token, expires_at)


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30)
    return _client


async def close_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None


async def _get_tenant_token() -> str:
    global _token
    if _token and time.time() < _token[1]:
        return _token[0]
    client = await get_client()
    resp = await client.post(
        f"{settings.FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
        json={
            "app_id": settings.FEISHU_APP_ID,
            "app_secret": settings.FEISHU_APP_SECRET,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    _token = (data["tenant_access_token"], time.time() + data.get("expire", 7200) - 60)
    return _token[0]


async def get_user_info(code: str) -> dict:
    token = await _get_tenant_token()
    client = await get_client()
    resp = await client.post(
        f"{settings.FEISHU_API_BASE}/authen/v1/access_token",
        headers={"Authorization": f"Bearer {token}"},
        json={"grant_type": "authorization_code", "code": code},
    )
    resp.raise_for_status()
    return resp.json()["data"]


async def get_bitable_records(table_id: str, filter_expr: str = None) -> list[dict]:
    token = await _get_tenant_token()
    client = await get_client()
    all_records = []
    page_token = None
    while True:
        params: dict = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        if filter_expr:
            params["filter"] = filter_expr
        resp = await client.get(
            f"{settings.FEISHU_API_BASE}/bitable/v1/apps/{settings.BITABLE_APP_TOKEN}"
            f"/tables/{table_id}/records",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        all_records.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return all_records


async def add_bitable_records(table_id: str, records: list[dict]) -> dict:
    token = await _get_tenant_token()
    client = await get_client()
    resp = await client.post(
        f"{settings.FEISHU_API_BASE}/bitable/v1/apps/{settings.BITABLE_APP_TOKEN}"
        f"/tables/{table_id}/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"records": records},
    )
    resp.raise_for_status()
    return resp.json()


async def update_bitable_records(table_id: str, records: list[dict]) -> dict:
    token = await _get_tenant_token()
    client = await get_client()
    resp = await client.put(
        f"{settings.FEISHU_API_BASE}/bitable/v1/apps/{settings.BITABLE_APP_TOKEN}"
        f"/tables/{table_id}/records",
        headers={"Authorization": f"Bearer {token}"},
        json={"records": records},
    )
    resp.raise_for_status()
    return resp.json()


async def get_user_name(open_id: str) -> str:
    token = await _get_tenant_token()
    client = await get_client()
    try:
        resp = await client.get(
            f"{settings.FEISHU_API_BASE}/contact/v3/users/{open_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()["data"]["user"].get("name", open_id)
    except Exception:
        return open_id


# —— 业务级查询封装 ——

async def get_active_round() -> dict | None:
    records = await get_bitable_records(
        settings.ROUNDS_TABLE_ID, 'CurrentValue.[status]="active"'
    )
    return records[0] if records else None


async def get_user_balance_record(round_id: str, open_id: str) -> dict | None:
    records = await get_bitable_records(
        settings.BALANCES_TABLE_ID,
        f'AND(CurrentValue.[round_id]="{round_id}",CurrentValue.[feishu_open_id]="{open_id}")',
    )
    return records[0] if records else None


async def get_employee_map() -> dict[str, dict]:
    """返回 {feishu_open_id: parsed_fields} 的员工字典"""
    records = await get_bitable_records(settings.EMPLOYEES_TABLE_ID)
    from utils import parse_bitable_fields
    return {
        parse_bitable_fields(r).get("feishu_open_id", ""): parse_bitable_fields(r)
        for r in records
    }


async def get_user_names(open_ids: set[str]) -> dict[str, str]:
    """并发获取多个用户姓名"""
    import asyncio
    results = await asyncio.gather(*(get_user_name(uid) for uid in open_ids))
    return dict(zip(open_ids, results))
