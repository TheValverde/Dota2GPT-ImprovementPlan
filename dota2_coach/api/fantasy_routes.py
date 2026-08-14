from fastapi import APIRouter, Depends, HTTPException, Query

from dota2_coach.api.schemas import AddTrackedPlayerRequest, RefreshFantasyRequest
from dota2_coach.errors import CoachError, TrackedPlayerNotFoundError
from dota2_coach.fantasy.scoring import parse_span
from dota2_coach.fantasy.tracker import FantasyTracker
from dota2_coach.opendota.filters import FantasyFilters

router = APIRouter(prefix="/api/fantasy")


def get_tracker() -> FantasyTracker:
    raise RuntimeError("Tracker dependency is not configured.")


def _span(amount: int, unit: str):
    try:
        return parse_span(amount, unit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _filters(ranked_only: bool, hide_turbo: bool) -> FantasyFilters:
    return FantasyFilters(ranked_only=ranked_only, hide_turbo=hide_turbo)


@router.get("/roster")
def roster(
    amount: int = Query(default=7, ge=1, le=365),
    unit: str = Query(default="days"),
    ranked_only: bool = Query(default=False),
    hide_turbo: bool = Query(default=False),
    tracker: FantasyTracker = Depends(get_tracker),
) -> dict:
    try:
        return tracker.summary(_span(amount, unit), _filters(ranked_only, hide_turbo))
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/roster")
def add_player(
    body: AddTrackedPlayerRequest,
    tracker: FantasyTracker = Depends(get_tracker),
) -> dict:
    try:
        return tracker.add_player(
            body.account_id,
            _span(body.amount, body.unit),
            _filters(body.ranked_only, body.hide_turbo),
        )
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.delete("/roster/{account_id}")
def remove_player(
    account_id: int,
    tracker: FantasyTracker = Depends(get_tracker),
) -> dict[str, bool]:
    try:
        tracker.remove_player(account_id)
    except TrackedPlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True}


@router.get("/players/{account_id}/field")
def ranked_field(
    account_id: int,
    amount: int = Query(default=7, ge=1, le=365),
    unit: str = Query(default="days"),
    hide_turbo: bool = Query(default=False),
    tracker: FantasyTracker = Depends(get_tracker),
) -> dict:
    try:
        return tracker.ranked_field(account_id, _span(amount, unit), hide_turbo=hide_turbo)
    except TrackedPlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/players/{account_id}/parse-missing")
def parse_missing_ranked(
    account_id: int,
    amount: int = Query(default=7, ge=1, le=365),
    unit: str = Query(default="days"),
    hide_turbo: bool = Query(default=False),
    tracker: FantasyTracker = Depends(get_tracker),
) -> dict:
    try:
        return tracker.parse_missing_ranked(
            account_id, _span(amount, unit), hide_turbo=hide_turbo
        )
    except TrackedPlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/players/{account_id}")
def player_card(
    account_id: int,
    amount: int = Query(default=7, ge=1, le=365),
    unit: str = Query(default="days"),
    ranked_only: bool = Query(default=False),
    hide_turbo: bool = Query(default=False),
    tracker: FantasyTracker = Depends(get_tracker),
) -> dict:
    try:
        return tracker.player_card(
            account_id,
            _span(amount, unit),
            _filters(ranked_only, hide_turbo),
        )
    except TrackedPlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/refresh")
def refresh(
    body: RefreshFantasyRequest,
    tracker: FantasyTracker = Depends(get_tracker),
) -> dict:
    try:
        return tracker.refresh(
            _span(body.amount, body.unit),
            body.account_id,
            _filters(body.ranked_only, body.hide_turbo),
        )
    except TrackedPlayerNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except CoachError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
