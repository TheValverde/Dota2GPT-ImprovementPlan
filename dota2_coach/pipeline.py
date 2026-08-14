from __future__ import annotations

from time import time
from typing import Any

from dota2_coach.analysis.coach import MatchCoach
from dota2_coach.analysis.schema import CoachReport
from dota2_coach.config import Settings
from dota2_coach.errors import OpenDotaError
from dota2_coach.opendota.client import OpenDotaClient
from dota2_coach.opendota.normalize import build_match_brief, find_focus_player
from dota2_coach.opendota.parse_jobs import REPLAY_RETENTION_SECONDS, submit_parse


class AnalysisPipeline:
    def __init__(self, settings: Settings, opendota: OpenDotaClient | None = None) -> None:
        self._settings = settings
        self.opendota = opendota or OpenDotaClient(
            base_url=settings.opendota_base_url,
            api_key=settings.opendota_api_key,
        )

    def analyze(self, player: str, match_id: int) -> tuple[dict[str, Any], CoachReport]:
        brief = self.build_brief(player, match_id)
        coach = MatchCoach(self._settings.openai_api_key, self._settings.openai_model)
        report = coach.analyze(brief)
        return brief, report

    def build_brief(self, player: str, match_id: int) -> dict[str, Any]:
        match = self.opendota.get_match(match_id)
        constants = self.opendota.load_constants()
        focus = find_focus_player(
            [p for p in match.get("players") or [] if isinstance(p, dict)],
            player,
        )
        hero_curve = None
        if not isinstance(focus.get("benchmarks"), dict) or not focus.get("benchmarks"):
            hero_id = focus.get("hero_id")
            if hero_id:
                try:
                    hero_curve = self.opendota.get_hero_benchmarks(int(hero_id))
                except OpenDotaError:
                    hero_curve = None
        brief = build_match_brief(match, player, constants, hero_benchmarks=hero_curve)
        start_time = match.get("start_time")
        if start_time and int(time()) - int(start_time) > REPLAY_RETENTION_SECONDS:
            brief["replay_may_have_expired"] = True
        return brief

    def start_parse(self, match_id: int) -> dict[str, Any]:
        match = self.opendota.get_match(match_id)
        return submit_parse(self.opendota, match)

    def parse_status(self, match_id: int, job_id: str) -> dict[str, Any]:
        job = self.opendota.parse_job(job_id)
        queued = job is not None and job != {}
        match = self.opendota.get_match(match_id)
        parsed = match.get("version") is not None
        return {
            "match_id": match_id,
            "job_id": job_id,
            "queued": queued,
            "parsed": parsed,
        }

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
