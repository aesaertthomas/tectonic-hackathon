from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str) -> Engine:
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    eng = create_engine(url, connect_args=connect_args)
    if url.startswith("sqlite"):

        @event.listens_for(eng, "connect")
        def _enable_foreign_keys(dbapi_connection, _record) -> None:  # noqa: ANN001
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return eng


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
