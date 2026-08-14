from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dota2_coach.api.routes import get_pipeline, router
from dota2_coach.config import get_settings
from dota2_coach.pipeline import AnalysisPipeline

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    pipeline = AnalysisPipeline(settings)
    app = FastAPI(
        title="Dota 2 Coach",
        description="Match analysis and improvement plans from OpenDota plus an LLM coach.",
        version="0.2.0",
    )
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
