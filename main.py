from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from settings import settings
from auth import create_session
from models.feishu import get_user_info, close_client
from database import close_db
import httpx

import routes.home as home_routes
import routes.transfer as transfer_routes
import routes.starwall as starwall_routes
import routes.admin as admin_routes

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html"]),
)

TEMPLATES = {
    "home": env.get_template("home.html"),
    "transfer": env.get_template("transfer.html"),
    "starwall": env.get_template("starwall.html"),
    "admin": env.get_template("admin.html"),
    "transactions": env.get_template("transactions.html"),
}

for mod in [home_routes, transfer_routes, starwall_routes, admin_routes]:
    mod.TEMPLATES = TEMPLATES


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_db()
    await close_client()


app = FastAPI(title="RR Procedure", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(home_routes.router)
app.include_router(transfer_routes.router)
app.include_router(starwall_routes.router)
app.include_router(admin_routes.router)


@app.get("/auth/callback")
async def auth_callback(code: str = ""):
    if not code:
        return HTMLResponse("<p>缺少认证参数，请从飞书工作台打开</p>")
    try:
        user_data = await get_user_info(code)
        open_id = user_data.get("open_id", "")
        name = user_data.get("name", open_id)
        session = create_session(open_id, name)
        resp = RedirectResponse(url="/")
        resp.set_cookie(
            "rr_session", session,
            max_age=settings.SESSION_MAX_AGE, httponly=True, samesite="lax",
        )
        return resp
    except (httpx.HTTPError, KeyError, ValueError):
        return HTMLResponse("<p>认证失败，请重试</p>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
