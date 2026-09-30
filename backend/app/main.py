from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import auth, budget, goals, insights, overview
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
    app.include_router(budget.router)
    app.include_router(insights.router)
    app.include_router(goals.router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    dist = Path(settings.frontend_dist)
    index = dist / "index.html"
    if index.is_file():
        if (dist / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str) -> FileResponse:
            # Client-side routes get the app shell. Unknown API paths stay JSON 404s.
            if full_path == "api" or full_path.startswith("api/"):
                raise HTTPException(status_code=404)
            return FileResponse(index)

    return app


app = create_app()
