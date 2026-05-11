import uuid
import asyncio
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from settings import settings
from auth import get_user, is_super_admin
from utils import parse_bitable_fields
from models.feishu import (
    get_bitable_records,
    add_bitable_records,
    update_bitable_records,
    get_employee_map,
    get_user_names,
)
from models.transaction import get_transactions_by_round
from models.rules import calc_coins

router = APIRouter()
TEMPLATES = {}


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, user: dict = Depends(get_user)):
    open_id = user["open_id"]
    super_admin = is_super_admin(open_id)

    rounds = await get_bitable_records(settings.ROUNDS_TABLE_ID)
    rounds_data = []
    for r in rounds:
        rf = parse_bitable_fields(r)
        rf["record_id"] = r.get("record_id")
        rounds_data.append(rf)

    return TEMPLATES["admin"].render(
        user=user, super_admin=super_admin, rounds=rounds_data,
    )


@router.post("/admin/create-round")
async def create_round(
    request: Request,
    user: dict = Depends(get_user),
    title: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
):
    if not is_super_admin(user["open_id"]):
        return HTMLResponse("<p>仅超级管理员可发起轮次</p>", status_code=403)

    round_id = str(uuid.uuid4())[:8]

    await add_bitable_records(
        settings.ROUNDS_TABLE_ID,
        [{"fields": {
            "round_id": round_id, "title": title, "status": "active",
            "start_date": int(start_date.replace("-", "")),
            "end_date": int(end_date.replace("-", "")),
        }}],
    )

    emp_map = await get_employee_map()
    balance_records = []
    for feishu_id, ef in emp_map.items():
        if not feishu_id:
            continue
        tenure = int(ef.get("tenure_months", 0))
        coins = calc_coins(tenure)
        balance_records.append({"fields": {
            "round_id": round_id, "feishu_open_id": feishu_id,
            "coins_allocated": coins, "coins_given": 0, "coins_received": 0,
        }})

    batch_size = 400
    for i in range(0, len(balance_records), batch_size):
        await add_bitable_records(
            settings.BALANCES_TABLE_ID, balance_records[i : i + batch_size]
        )

    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/close-round")
async def close_round(
    request: Request,
    user: dict = Depends(get_user),
    round_id: str = Form(...),
):
    if not is_super_admin(user["open_id"]):
        return HTMLResponse("<p>仅超级管理员可关闭轮次</p>", status_code=403)

    records = await get_bitable_records(
        settings.ROUNDS_TABLE_ID, f'CurrentValue.[round_id]="{round_id}"',
    )
    if records:
        await update_bitable_records(
            settings.ROUNDS_TABLE_ID,
            [{"record_id": records[0]["record_id"], "fields": {"status": "closed"}}],
        )

    # 并发获取员工字典和余额
    emp_map, balances = await asyncio.gather(
        get_employee_map(),
        get_bitable_records(
            settings.BALANCES_TABLE_ID,
            f'CurrentValue.[round_id]="{round_id}"',
        ),
    )

    dept_scores: dict[str, list[tuple[str, str, int]]] = {}
    for b in balances:
        bf = parse_bitable_fields(b)
        uid = bf.get("feishu_open_id", "")
        received = int(bf.get("coins_received", 0))
        e = emp_map.get(uid, {})
        dept = e.get("department", "未知")
        ename = e.get("name", uid)
        dept_scores.setdefault(dept, []).append((uid, ename, received))

    star_records = []
    for dept, users in dept_scores.items():
        users.sort(key=lambda x: x[2], reverse=True)
        winner = users[0]
        star_records.append({"fields": {
            "round_id": round_id, "department": dept,
            "winner_name": winner[1], "coins_received": winner[2],
        }})

    if star_records:
        await add_bitable_records(settings.STARWALL_TABLE_ID, star_records)

    return RedirectResponse(url="/admin", status_code=303)


@router.get("/admin/transactions", response_class=HTMLResponse)
async def admin_transactions(
    request: Request,
    user: dict = Depends(get_user),
    round_id: str = "",
):
    open_id = user["open_id"]
    if not is_super_admin(open_id):
        return HTMLResponse("<p>没有权限</p>", status_code=403)

    transactions = []
    if round_id:
        transactions = await get_transactions_by_round(round_id)

    if not transactions:
        return TEMPLATES["transactions"].render(
            user=user, round_id=round_id, transactions=[],
        )

    # 并发获取所有涉及用户的姓名（去重）
    unique_ids = {tx["from_user"] for tx in transactions} | {tx["to_user"] for tx in transactions}
    names = await get_user_names(unique_ids)

    enriched = []
    for tx in transactions:
        enriched.append({
            **tx,
            "from_name": names.get(tx["from_user"], tx["from_user"]),
            "to_name": names.get(tx["to_user"], tx["to_user"]),
        })

    return TEMPLATES["transactions"].render(
        user=user, round_id=round_id, transactions=enriched,
    )
