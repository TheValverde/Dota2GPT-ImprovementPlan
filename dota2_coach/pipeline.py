from __future__ import annotations

from typing import Any

from dota2_coach.analysis.coach import MatchCoach
from dota2_coach.analysis.schema import CoachReport
from dota2_coach.config import Settings
from dota2_coach.opendota.client import OpenDotaClient
from dota2_coach.opendota.normalize import build_match_brief


class AnalysisPipeline:
    def __init__(self, settings: Settings, opendota: OpenDotaClient | None = None) -> None:
        self._settings = settings
        self.opendota = opendota or OpenDotaClient(
            base_url=settings.opendota_base_url,
            api_key=settings.opendota_api_key,
        )

    def analyze(self, player: str, match_id: int) -> tuple[dict[str, Any], CoachReport]:
        match = self.opendota.get_match(match_id)
        constants = self.opendota.load_constants()
        brief = build_match_brief(match, player, constants)
        coach = MatchCoach(self._settings.openai_api_key, self._settings.openai_model)
        report = coach.analyze(brief)
        return brief, report

    def search_players(self, query: str) -> list[dict[str, Any]]:
        return self.opendota.search_players(query)

    def recent_matches(self, account_id: int) -> list[dict[str, Any]]:
        constants = self.opendota.load_constants()
        rows = self.opendota.recent_matches(account_id)
        summarized: list[dict[str, Any]] = []
        for row in rows:
            summarized.append(
                {
                    "match_id": row.get("match_id"),
                    "hero": constants.hero_name(row.get("hero_id")),
                    "kills": row.get("kills"),
                    "deaths": row.get("deaths"),
                    "assists": row.get("assists"),
                    "won": bool(row.get("radiant_win") == ((row.get("player_slot") or 0) < 128))
                    if row.get("radiant_win") is not None
                    else None,
                    "duration": row.get("duration"),
                    "game_mode": constants.game_mode_name(row.get("game_mode")),
                    "start_time": row.get("start_time"),
                }
            )
        return summarized
