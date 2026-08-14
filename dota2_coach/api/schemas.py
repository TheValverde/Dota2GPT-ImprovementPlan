from pydantic import BaseModel, Field

from dota2_coach.analysis.schema import CoachReport


class AnalyzeRequest(BaseModel):
    player: str = Field(min_length=1, description="Persona name or OpenDota account ID")
    match_id: int = Field(gt=0)


class AnalyzeResponse(BaseModel):
    brief: dict
    report: CoachReport


class PlayerSearchResult(BaseModel):
    account_id: int
    personaname: str
    avatarfull: str | None = None
    similarity: float | None = None


class RecentMatch(BaseModel):
    match_id: int | None = None
    hero: str | None = None
    kills: int | None = None
    deaths: int | None = None
    assists: int | None = None
    won: bool | None = None
    duration: int | None = None
    game_mode: str | None = None
    start_time: int | None = None


class RefreshFantasyRequest(BaseModel):
    account_id: int | None = None
    amount: int = Field(default=7, ge=1, le=365)
    unit: str = Field(default="days")
    ranked_only: bool = False
    hide_turbo: bool = False


class AddTrackedPlayerRequest(BaseModel):
    account_id: int = Field(gt=0)
    amount: int = Field(default=7, ge=1, le=365)
    unit: str = Field(default="days")
    ranked_only: bool = False
    hide_turbo: bool = False
