from fastapi import FastAPI

from .api import auth, goals, insights, overview
from .config import Settings, get_settings
from .security import make_security_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(
        title="KBC Time Machine",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.debug else None,
    )
    app.middleware("http")(make_security_middleware(settings.allowed_origins))
    app.include_router(auth.router)
    app.include_router(overview.router)
    app.include_router(insights.router)
    app.include_router(goals.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
