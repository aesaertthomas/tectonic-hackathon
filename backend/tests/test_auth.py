from datetime import datetime

from sqlalchemy import func, select, update

from app.models import AuthSession
from app.security import hash_token
from tests.helpers import PASSWORD, add_customer, login


def test_login_sets_hardened_cookie_and_stores_only_a_hash(client, db):
    add_customer(db, "anna", display_name="Anna")
    response = login(client, "anna")
    assert response.json() == {"display_name": "Anna"}
    cookie = response.headers["set-cookie"].lower()
    assert "tm_session=" in cookie and "httponly" in cookie and "samesite=strict" in cookie and "path=/" in cookie
    token = client.cookies.get("tm_session")
    db.expire_all()
    stored = db.scalars(select(AuthSession)).all()
    assert [s.token_hash for s in stored] == [hash_token(token)]


def test_me_requires_login(client):
    response = client.get("/api/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Please log in."}


def test_me_after_login(client, db):
    add_customer(db, "anna", display_name="Anna")
    login(client, "anna")
    assert client.get("/api/me").json() == {"display_name": "Anna"}


def test_wrong_password_and_unknown_user_look_the_same(client, db):
    add_customer(db, "anna")
    wrong = client.post("/api/auth/login", json={"username": "anna", "password": "nope"})
    unknown = client.post("/api/auth/login", json={"username": "nobody", "password": "nope"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Invalid username or password."}


def test_username_is_case_insensitive(client, db):
    add_customer(db, "anna")
    assert client.post("/api/auth/login", json={"username": "  Anna ", "password": PASSWORD}).status_code == 200


def test_rate_limit_blocks_even_the_right_password(client, db):
    add_customer(db, "anna")
    for _ in range(5):
        assert client.post("/api/auth/login", json={"username": "anna", "password": "nope"}).status_code == 401
    blocked = client.post("/api/auth/login", json={"username": "anna", "password": PASSWORD})
    assert blocked.status_code == 429


def test_expired_session_is_rejected(client, db):
    add_customer(db, "anna")
    login(client, "anna")
    db.execute(update(AuthSession).values(expires_at=datetime(2000, 1, 1)))
    db.commit()
    assert client.get("/api/me").status_code == 401


def test_new_login_replaces_the_old_session(client, db):
    add_customer(db, "anna")
    login(client, "anna")
    login(client, "anna")
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(AuthSession)) == 1


def test_logout_deletes_the_session(client, db):
    add_customer(db, "anna")
    login(client, "anna")
    assert client.post("/api/auth/logout").status_code == 204
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(AuthSession)) == 0
    assert client.get("/api/me").status_code == 401


def test_forged_cookie_is_rejected(client, db):
    add_customer(db, "anna")
    client.cookies.set("tm_session", "forged-token")
    assert client.get("/api/me").status_code == 401


def test_login_body_is_strict(client):
    response = client.post("/api/auth/login", json={"username": "a", "password": "b", "admin": True})
    assert response.status_code == 422
    too_long = client.post("/api/auth/login", json={"username": "a", "password": "x" * 129})
    assert too_long.status_code == 422
