from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from settings import settings
from auth import get_user
from utils import parse_bitable_fields
from models.feishu import get_bitable_records

router = APIRouter()
TEMPLATES = {}


@router.get("/starwall", response_class=HTMLResponse)
async def starwall(request: Request, user: dict = Depends(get_user)):
    records = await get_bitable_records(settings.STARWALL_TABLE_ID)
    winners = []
    for r in records:
        f = parse_bitable_fields(r)
        winners.append({
            "department": f.get("department", ""),
            "winner_name": f.get("winner_name", ""),
            "coins_received": f.get("coins_received", 0),
        })

    return TEMPLATES["starwall"].render(user=user, winners=winners)
