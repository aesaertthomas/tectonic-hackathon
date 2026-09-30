import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401  (registers the tables on Base.metadata)
from app.config import Settings, get_settings
from app.db import Base, make_engine
from app.deps import get_db
from app.main import create_app

ORIGIN = "http://testserver"


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, database_url="sqlite://", allowed_origins=[ORIGIN], cookie_secure=False)


@pytest.fixture
def engine(tmp_path):
    eng = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


@pytest.fixture
def app(settings, session_factory):
    application = create_app(settings)

    def override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    application.dependency_overrides[get_db] = override_db
    application.dependency_overrides[get_settings] = lambda: settings
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        test_client.headers.update({"Origin": ORIGIN, "X-Requested-With": "fetch"})
        yield test_client


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.api.auth import ip_limiter, user_limiter

    user_limiter.clear()
    ip_limiter.clear()
    yield
