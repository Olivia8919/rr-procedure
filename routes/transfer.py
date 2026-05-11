import asyncio
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from settings import settings
from auth import get_user
from utils import parse_bitable_fields
from models.feishu import (
    get_active_round,
    get_user_balance_record,
    update_bitable_records,
)
from models.transaction import add_transaction, get_given_to
from models.rules import validate_transfer

router = APIRouter()
TEMPLATES = {}


@router.get("/transfer", response_class=HTMLResponse)
async def transfer_page(request: Request, user: dict = Depends(get_user)):
    open_id = user["open_id"]
    round_data = await get_active_round()
    if not round_data:
        return TEMPLATES["transfer"].render(
            user=user, round=None, balance=None, error="当前没有进行中的轮次"
        )

    round_fields = parse_bitable_fields(round_data)
    round_id = round_fields.get("round_id", str(round_data.get("record_id", "")))
    balance_rec = await get_user_balance_record(round_id, open_id)

    if not balance_rec:
        return TEMPLATES["transfer"].render(
            user=user, round=round_fields, balance=None, error="未找到你的 Coin 账户"
        )

    bf = parse_bitable_fields(balance_rec)
    balance = {
        "record_id": balance_rec.get("record_id"),
        "allocated": int(bf.get("coins_allocated", 0)),
        "given": int(bf.get("coins_given", 0)),
        "remaining": int(bf.get("coins_allocated", 0)) - int(bf.get("coins_given", 0)),
    }

    return TEMPLATES["transfer"].render(
        user=user, round=round_fields, balance=balance, error=None
    )


def _make_balance(balance_rec, allocated, given):
    return {
        "record_id": balance_rec.get("record_id"),
        "allocated": allocated,
        "given": given,
        "remaining": allocated - given,
    }


@router.post("/transfer", response_class=HTMLResponse)
async def transfer_submit(
    request: Request,
    user: dict = Depends(get_user),
    to_user_id: str = Form(...),
    to_user_name: str = Form(...),
    coins: int = Form(..., ge=1),
):
    open_id = user["open_id"]
    round_data = await get_active_round()

    if not round_data:
        return TEMPLATES["transfer"].render(
            user=user, round=None, balance=None, error="当前没有进行中的轮次"
        )

    round_fields = parse_bitable_fields(round_data)
    round_id = round_fields.get("round_id", str(round_data.get("record_id", "")))

    balance_rec, target_given = await asyncio.gather(
        get_user_balance_record(round_id, open_id),
        get_given_to(round_id, open_id, to_user_id),
    )

    if not balance_rec:
        return TEMPLATES["transfer"].render(
            user=user, round=round_fields, balance=None, error="未找到你的 Coin 账户"
        )

    bf = parse_bitable_fields(balance_rec)
    allocated = int(bf.get("coins_allocated", 0))
    given = int(bf.get("coins_given", 0))

    error = validate_transfer(allocated, given, target_given, coins, open_id, to_user_id)
    if error:
        return TEMPLATES["transfer"].render(
            user=user, round=round_fields,
            balance=_make_balance(balance_rec, allocated, given), error=error,
        )

    # 并发：更新转出者 + 查接收者
    await update_bitable_records(
        settings.BALANCES_TABLE_ID,
        [{"record_id": balance_rec["record_id"], "fields": {"coins_given": given + coins}}],
    )

    to_balance_rec = await get_user_balance_record(round_id, to_user_id)
    if to_balance_rec:
        to_bf = parse_bitable_fields(to_balance_rec)
        to_received = int(to_bf.get("coins_received", 0))
        await asyncio.gather(
            update_bitable_records(
                settings.BALANCES_TABLE_ID,
                [{"record_id": to_balance_rec["record_id"],
                  "fields": {"coins_received": to_received + coins}}],
            ),
            add_transaction(round_id, open_id, to_user_id, coins),
        )

    return RedirectResponse(url="/", status_code=303)
