from pydantic import BaseModel, Field


class FocusArea(BaseModel):
    title: str
    why_it_matters: str
    how_to_practice: str


class CoachReport(BaseModel):
    headline: str = Field(description="One sharp sentence about this player's game.")
    match_read: str = Field(
        description=(
            "Two to four paragraphs. Walk the game in time order: lane, towers, "
            "Roshan, gold swing, who showed in fights. Place the focus player "
            "inside those moments. Do not summarize only their KDA."
        )
    )
    grade: str = Field(description="Letter grade from S, A, B, C, D, or F.")
    kda_context: str = Field(
        description="What the KDA and farm numbers actually meant in this lobby."
    )
    game_timeline: list[str] = Field(
        default_factory=list,
        description=(
            "Chronological beats with timestamps. Include teammate and enemy "
            "actions, not only the focus player."
        ),
    )
    strengths: list[str] = Field(default_factory=list)
    mistakes: list[str] = Field(default_factory=list)
    focus_areas: list[FocusArea] = Field(default_factory=list)
    next_three_games: list[str] = Field(default_factory=list)
