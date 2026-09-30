from fastapi.testclient import TestClient

from app.security import LoginRateLimiter, hash_password, hash_token, new_session_token, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password(hashed, "s3cret-pass")
    assert not verify_password(hashed, "wrong")


def test_verify_without_hash_is_false():
    assert verify_password(None, "anything") is False


def test_verify_with_garbage_hash_is_false():
    assert verify_password("not-an-argon2-hash", "anything") is False


def test_session_tokens_are_random_and_hashed():
    a, b = new_session_token(), new_session_token()
    assert a != b and len(a) >= 40
    assert len(hash_token(a)) == 64 and hash_token(a) != a


def test_rate_limiter_blocks_then_forgets():
    now = [0.0]
    limiter = LoginRateLimiter(max_failures=3, window_seconds=60, clock=lambda: now[0])
    for _ in range(3):
        assert not limiter.is_blocked("k")
        limiter.record_failure("k")
    assert limiter.is_blocked("k")
    now[0] = 61.0
    assert not limiter.is_blocked("k")


def test_rate_limiter_reset():
    limiter = LoginRateLimiter(max_failures=1)
    limiter.record_failure("k")
    limiter.reset("k")
    assert not limiter.is_blocked("k")


def test_security_headers_present(client):
    response = client.get("/api/health")
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "same-origin"
    assert response.headers["cache-control"] == "no-store"


def test_post_without_origin_is_forbidden(app):
    with TestClient(app) as raw:
        response = raw.post("/api/auth/login", json={"username": "x", "password": "y"}, headers={"X-Requested-With": "fetch"})
    assert response.status_code == 403


def test_post_from_foreign_origin_is_forbidden(app):
    with TestClient(app) as raw:
        response = raw.post(
            "/api/auth/login",
            json={"username": "x", "password": "y"},
            headers={"Origin": "https://evil.example", "X-Requested-With": "fetch"},
        )
    assert response.status_code == 403


def test_post_without_requested_with_header_is_forbidden(app):
    with TestClient(app) as raw:
        response = raw.post("/api/auth/login", json={"username": "x", "password": "y"}, headers={"Origin": "http://testserver"})
    assert response.status_code == 403


def test_referer_is_accepted_when_origin_is_missing(app):
    with TestClient(app) as raw:
        response = raw.post(
            "/api/auth/login",
            json={"username": "x", "password": "y"},
            headers={"Referer": "http://testserver/login", "X-Requested-With": "fetch"},
        )
    assert response.status_code == 401  # got past the origin check, then failed login


def test_get_requests_do_not_need_origin(app):
    with TestClient(app) as raw:
        assert raw.get("/api/health").status_code == 200
