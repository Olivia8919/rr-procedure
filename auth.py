from fastapi import Request, HTTPException
from itsdangerous import URLSafeSerializer, BadSignature
from settings import settings

serializer = URLSafeSerializer(settings.SESSION_SECRET)


def create_session(open_id: str, name: str) -> str:
    return serializer.dumps({"open_id": open_id, "name": name})


def get_session(request: Request) -> dict:
    cookie = request.cookies.get("rr_session")
    if not cookie:
        raise HTTPException(status_code=401)
    try:
        return serializer.loads(cookie)
    except BadSignature:
        raise HTTPException(status_code=401)


def get_user(request: Request) -> dict:
    return get_session(request)


def is_super_admin(open_id: str) -> bool:
    return open_id in settings.SUPER_ADMINS
