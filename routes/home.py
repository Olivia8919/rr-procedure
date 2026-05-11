import asyncio
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from settings import settings
from auth import get_user
from utils import parse_bitable_fields
from models.feishu import (
    get_active_round,
    get_user_balance_record,
    get_employee_map,
    get_bitable_records,
)

router = APIRouter()
TEMPLATES = {}


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: dict = Depends(get_user)):
    open_id = user["open_id"]
    round_data = await get_active_round()

    if not round_data:
        return TEMPLATES["home"].render(user=user, round=None, balance=None)

    round_fields = parse_bitable_fields(round_data)
    round_id = round_fields.get("round_id", str(round_data.get("record_id", "")))

    # 并发：用户余额 + 全体员工字典 + 全部余额
    balance_rec, emp_map, all_balances = await asyncio.gather(
        get_user_balance_record(round_id, open_id),
        get_employee_map(),
        get_bitable_records(
            settings.BALANCES_TABLE_ID,
            f'CurrentValue.[round_id]="{round_id}"',
        ),
    )

    balance = None
    if balance_rec:
        bf = parse_bitable_fields(balance_rec)
        allocated = int(bf.get("coins_allocated", 0))
        given = int(bf.get("coins_given", 0))
        received = int(bf.get("coins_received", 0))
        remaining = allocated - given

        my_emp = emp_map.get(open_id, {})
        dept = my_emp.get("department", "")

        if dept:
            dept_scores = []
            for record in all_balances:
                bf2 = parse_bitable_fields(record)
                rid = bf2.get("feishu_open_id", "")
                if rid == open_id:
                    continue
                e_f = emp_map.get(rid, {})
                if e_f.get("department") == dept:
                    dept_scores.append(int(bf2.get("coins_received", 0)))
            my_rank = sum(1 for s in dept_scores if s > received) + 1
        else:
            my_rank = None

        balance = {
            "record_id": balance_rec.get("record_id"),
            "allocated": allocated,
            "given": given,
            "received": received,
            "remaining": remaining,
            "department": dept,
            "rank": my_rank,
        }

    return TEMPLATES["home"].render(user=user, round=round_fields, balance=balance)
