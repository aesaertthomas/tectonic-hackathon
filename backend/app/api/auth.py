from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import delete, select

from ..deps import SESSION_COOKIE, AppSettings, CurrentCustomer, DbSession
from ..models import AuthSession, Customer
from ..schemas import LoginIn, MeOut
from ..security import LoginRateLimiter, hash_token, new_session_token, utcnow, verify_password

router = APIRouter(prefix="/api", tags=["auth"])

user_limiter = LoginRateLimiter(max_failures=5)
ip_limiter = LoginRateLimiter(max_failures=20)
INVALID_LOGIN = "Invalid username or password."


@router.post("/auth/login", response_model=MeOut)
def login(body: LoginIn, request: Request, response: Response, db: DbSession, settings: AppSettings) -> MeOut:
    username = body.username.strip().lower()
    ip = request.client.host if request.client else "unknown"
    user_key = f"{username}|{ip}"
    if user_limiter.is_blocked(user_key) or ip_limiter.is_blocked(ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait a few minutes and try again.")

    customer = db.scalar(select(Customer).where(Customer.username == username))
    password_ok = verify_password(customer.password_hash if customer else None, body.password)
    if customer is None or not password_ok:
        user_limiter.record_failure(user_key)
        ip_limiter.record_failure(ip)
        raise HTTPException(status_code=401, detail=INVALID_LOGIN)
    user_limiter.reset(user_key)

    now = utcnow()
    old_token = request.cookies.get(SESSION_COOKIE)
    if old_token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_token(old_token)))
    db.execute(delete(AuthSession).where(AuthSession.customer_id == customer.id, AuthSession.expires_at <= now))
    token = new_session_token()
    db.add(
        AuthSession(
            token_hash=hash_token(token),
            customer_id=customer.id,
            created_at=now,
            expires_at=now + timedelta(hours=settings.session_ttl_hours),
        )
    )
    db.commit()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_ttl_hours * 3600,
        path="/",
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
    )
    return MeOut(display_name=customer.display_name)


@router.post("/auth/logout", status_code=204)
def logout(request: Request, db: DbSession, settings: AppSettings) -> Response:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        db.execute(delete(AuthSession).where(AuthSession.token_hash == hash_token(token)))
        db.commit()
    response = Response(status_code=204)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="strict", secure=settings.cookie_secure)
    return response


@router.get("/me", response_model=MeOut)
def me(customer: CurrentCustomer) -> MeOut:
    return MeOut(display_name=customer.display_name)
