from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from dota2_coach.api.fantasy_routes import get_tracker, router as fantasy_router
from dota2_coach.api.routes import get_pipeline, router
from dota2_coach.config import Settings, get_settings
from dota2_coach.fantasy.store import FantasyStore
from dota2_coach.fantasy.tracker import FantasyTracker
from dota2_coach.paths import resolve_data_dir
from dota2_coach.pipeline import AnalysisPipeline

STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"


def build_tracker(settings: Settings, pipeline: AnalysisPipeline) -> FantasyTracker:
    data_dir = resolve_data_dir(settings.data_dir)
    return FantasyTracker(
        opendota=pipeline.opendota,
        store=FantasyStore(data_dir / "fantasy.sqlite"),
    )


def create_app(
    settings: Settings | None = None,
    pipeline: AnalysisPipeline | None = None,
    tracker: FantasyTracker | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    pipeline = pipeline or AnalysisPipeline(settings)
    tracker = tracker or build_tracker(settings, pipeline)
    app = FastAPI(
        title="Dota 2 Coach",
        description="Overlay-style Dota 2 coach and fantasy tracker.",
        version="0.3.0",
    )
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    app.dependency_overrides[get_tracker] = lambda: tracker
    app.include_router(router)
    app.include_router(fantasy_router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app
