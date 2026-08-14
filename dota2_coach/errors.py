class CoachError(Exception):
    """Base error for the coaching pipeline."""


class MatchNotFoundError(CoachError):
    def __init__(self, match_id: int) -> None:
        super().__init__(f"OpenDota has no match {match_id}.")
        self.match_id = match_id


class PlayerNotInMatchError(CoachError):
    def __init__(self, player: str, available: list[str]) -> None:
        names = ", ".join(available) if available else "no named players"
        super().__init__(
            f"Could not find player '{player}' in this match. Players found: {names}."
        )
        self.player = player
        self.available = available


class OpenDotaError(CoachError):
    pass


class OpenAINotConfiguredError(CoachError):
    def __init__(self) -> None:
        super().__init__("OPENAI_API_KEY is not set.")
