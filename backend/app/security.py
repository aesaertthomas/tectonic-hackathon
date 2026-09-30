"""Password hashing, session tokens, login rate limiting and HTTP hardening."""

import hashlib
import secrets
import threading
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Request, Response
from fastapi.responses import JSONResponse

_hasher = PasswordHasher()
# Used when the username doesn't exist, so that case takes as long as a wrong password.
_DUMMY_HASH = _hasher.hash("timing-equaliser-not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        ok = _hasher.verify(password_hash or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return ok and password_hash is not None


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class LoginRateLimiter:
    """In-memory sliding window of failed logins per key. Good enough for a single-process POC."""

    def __init__(self, max_failures: int, window_seconds: float = 900, clock: Callable[[], float] = time.monotonic):
        self._max = max_failures
        self._window = window_seconds
        self._clock = clock
        self._failures: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _recent(self, key: str, now: float) -> list[float]:
        recent = [t for t in self._failures.get(key, []) if now - t < self._window]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def is_blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._recent(key, self._clock())) >= self._max

    def record_failure(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            self._failures[key] = [*self._recent(key, now), now]

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._failures.clear()


SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
}


def request_origin(request: Request) -> str | None:
    origin = request.headers.get("origin")
    if origin:
        return origin
    referer = request.headers.get("referer")
    if referer:
        parts = urlsplit(referer)
        if parts.scheme and parts.netloc:
            return f"{parts.scheme}://{parts.netloc}"
    return None


def _harden(request: Request, response: Response) -> Response:
    for name, value in SECURITY_HEADERS.items():
        response.headers[name] = value
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


def make_security_middleware(allowed_origins: list[str]):
    """CSRF defence for state-changing API calls (same-origin + custom header) and security headers everywhere."""
    allowed = frozenset(allowed_origins)

    async def middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method not in SAFE_METHODS and request.url.path.startswith("/api/"):
            if request_origin(request) not in allowed or request.headers.get("x-requested-with") != "fetch":
                return _harden(request, JSONResponse({"detail": "Forbidden."}, status_code=403))
        return _harden(request, await call_next(request))

    return middleware
