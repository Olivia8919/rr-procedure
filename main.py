from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from settings import settings
from auth import create_session, needs_auth, serializer
from models.feishu import get_user_info, close_client, _get_jsapi_ticket, generate_jsapi_signature
from database import close_db
from itsdangerous import BadSignature
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


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not needs_auth(request.url.path):
        return await call_next(request)

    session = request.cookies.get("rr_session")
    if session:
        try:
            serializer.loads(session)
            return await call_next(request)
        except BadSignature:
            pass

    code = request.query_params.get("code")
    if code:
        return RedirectResponse(url=f"/auth/callback?code={code}")

    redirect_uri = str(request.url).split("?")[0]
    auth_url = (
        f"{settings.FEISHU_API_BASE}/authen/v1/authorize"
        f"?app_id={settings.FEISHU_APP_ID}&redirect_uri={redirect_uri}"
    )
    return RedirectResponse(url=auth_url)


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


@app.get("/api/jsapi-config")
async def jsapi_config(url: str = ""):
    """返回飞书 JSSDK 初始化所需的签名配置"""
    if not url:
        return {"error": "缺少 url 参数"}
    try:
        ticket = await _get_jsapi_ticket()
        sig = generate_jsapi_signature(ticket, url)
        return {
            "appId": settings.FEISHU_APP_ID,
            "timestamp": sig["timestamp"],
            "noncestr": sig["noncestr"],
            "signature": sig["signature"],
        }
    except (httpx.HTTPError, KeyError):
        return {"error": "获取 JSSDK 签名失败"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
