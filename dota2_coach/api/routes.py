from fastapi import APIRouter, Depends, HTTPException, Query

from dota2_coach.api.schemas import AnalyzeRequest, AnalyzeResponse, PlayerSearchResult, RecentMatch
from dota2_coach.errors import (
    AccountIdRequiredError,
    CoachError,
    MatchNotFoundError,
    OpenAINotConfiguredError,
    ParsedMatchNotFoundError,
    PlayerNotInMatchError,
)
from dota2_coach.pipeline import AnalysisPipeline

router = APIRouter(prefix="/api")


def get_pipeline() -> AnalysisPipeline:
    raise RuntimeError("Pipeline dependency is not configured.")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/players/search", response_model=list[PlayerSearchResult])
def search_players(
    q: str = Query(min_length=2, max_length=64),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> list[PlayerSearchResult]:
    try:
        return [PlayerSearchResult.model_validate(row) for row in pipeline.search_players(q)]
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/players/{account_id}/recent-matches", response_model=list[RecentMatch])
def recent_matches(
    account_id: int,
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> list[RecentMatch]:
    try:
        return [RecentMatch.model_validate(row) for row in pipeline.recent_matches(account_id)]
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/players/{account_id}/parsed-match", response_model=RecentMatch)
def parsed_match(
    account_id: int,
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> RecentMatch:
    try:
        return RecentMatch.model_validate(pipeline.latest_parsed_match(account_id))
    except ParsedMatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(
    body: AnalyzeRequest,
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> AnalyzeResponse:
    try:
        brief, report = pipeline.analyze(body.player, body.match_id)
    except OpenAINotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except AccountIdRequiredError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ParsedMatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PlayerNotInMatchError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AnalyzeResponse(brief=brief, report=report)


@router.post("/matches/{match_id}/parse")
def start_parse(
    match_id: int,
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> dict:
    try:
        return pipeline.start_parse(match_id)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/matches/{match_id}/parse-status")
def parse_status(
    match_id: int,
    job_id: str = Query(min_length=1),
    pipeline: AnalysisPipeline = Depends(get_pipeline),
) -> dict:
    try:
        return pipeline.parse_status(match_id, job_id)
    except MatchNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
