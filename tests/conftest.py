import json
from pathlib import Path
from time import time

import pytest
from fastapi.testclient import TestClient

from dota2_coach.analysis.schema import CoachReport, FocusArea
from dota2_coach.api.app import create_app
from dota2_coach.config import Settings
from dota2_coach.fantasy.store import FantasyStore
from dota2_coach.fantasy.tracker import FantasyTracker
from dota2_coach.opendota.constants import GameConstants
from dota2_coach.pipeline import AnalysisPipeline


def _match_row(match_id: int, start_time: int, hero_id: int = 1, **overrides) -> dict:
    row = {
        "match_id": match_id,
        "hero_id": hero_id,
        "kills": 12,
        "deaths": 3,
        "assists": 9,
        "last_hits": 280,
        "denies": 18,
        "gold_per_min": 720,
        "player_slot": 0,
        "radiant_win": True,
        "start_time": start_time,
        "duration": 2400,
        "tower_kills": 2,
        "roshan_kills": 1,
        "teamfight_participation": 0.4,
        "obs_placed": 1,
        "camps_stacked": 2,
        "rune_pickups": 4,
        "firstblood_claimed": 1,
        "stuns": 10,
        "game_mode": 22,
    }
    row.update(overrides)
    return row


class FakeOpenDota:
    def __init__(self, match: dict, constants: GameConstants) -> None:
        self._match = match
        self._constants = constants
        now = int(time())
        self._matches = {
            111: [
                _match_row(7000000001, now - 2 * 86400, 1),
                _match_row(7000000002, now - 40 * 86400, 74, kills=2, deaths=10, assists=4),
            ],
            222: [
                _match_row(7000000003, now - 1 * 86400, 14, kills=6, deaths=6, assists=20),
            ],
        }

    def get_match(self, match_id: int) -> dict:
        assert match_id == self._match["match_id"]
        return self._match

    def load_constants(self) -> GameConstants:
        return self._constants

    def search_players(self, query: str) -> list[dict]:
        return [
            {
                "account_id": 111,
                "personaname": "TestCarry",
                "avatarfull": None,
                "similarity": 0.9,
            }
        ]

    def recent_matches(self, account_id: int) -> list[dict]:
        return [
            {
                "match_id": 7000000001,
                "hero_id": 1,
                "kills": 12,
                "deaths": 3,
                "assists": 9,
                "player_slot": 0,
                "radiant_win": True,
                "duration": 2460,
                "game_mode": 22,
                "start_time": 1,
            }
        ]

    def get_player(self, account_id: int) -> dict:
        names = {111: "TestCarry", 222: "EnemyMid"}
        return {
            "account_id": account_id,
            "personaname": names.get(account_id, f"Player{account_id}"),
            "avatarfull": None,
            "rank_tier": 65,
        }

    def player_matches(self, account_id: int, days: int | None = None, limit: int = 100) -> list[dict]:
        rows = list(self._matches.get(account_id, []))
        if days:
            cutoff = int(time()) - days * 86400
            rows = [row for row in rows if row["start_time"] >= cutoff]
        return rows[:limit]


class FakeCoach:
    def analyze(self, brief: dict) -> CoachReport:
        assert brief["focus_player"]["name"] == "TestCarry"
        return CoachReport(
            headline="Anti-Mage took over after a clean safe lane.",
            match_read="Radiant won a 41 minute game with TestCarry farming efficiently.",
            grade="A",
            kda_context="12/3/9 is a carry game where you converted farm into map pressure.",
            strengths=["Strong farm tempo", "Did not overstay after BKB"],
            mistakes=["Late first tower damage relative to net worth"],
            focus_areas=[
                FocusArea(
                    title="Timing windows",
                    why_it_matters="Your net worth spiked before objectives did.",
                    how_to_practice="Queue a fight or tower as soon as Battle Fury completes.",
                )
            ],
            next_three_games=["Call the 20 minute smoke after your first major item."],
        )


@pytest.fixture
def sample_match() -> dict:
    path = Path(__file__).parent / "fixtures" / "match.json"
    return json.loads(path.read_text())


@pytest.fixture
def constants() -> GameConstants:
    return GameConstants(
        heroes={1: "Anti-Mage", 74: "Invoker", 14: "Pudge"},
        items={1: "Blink Dagger", 50: "Phase Boots"},
        game_modes={22: "All Pick"},
        lobby_types={7: "Ranked"},
    )


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(openai_api_key="test", openai_model="gpt-test", data_dir=str(tmp_path))


@pytest.fixture
def opendota(sample_match: dict, constants: GameConstants) -> FakeOpenDota:
    return FakeOpenDota(sample_match, constants)


@pytest.fixture
def tracker(opendota: FakeOpenDota, tmp_path: Path) -> FantasyTracker:
    return FantasyTracker(opendota, FantasyStore(tmp_path / "fantasy.sqlite"))


@pytest.fixture
def client(
    settings: Settings,
    sample_match: dict,
    constants: GameConstants,
    opendota: FakeOpenDota,
    tracker: FantasyTracker,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    pipeline = AnalysisPipeline(settings, opendota=opendota)
    monkeypatch.setattr("dota2_coach.pipeline.MatchCoach", lambda api_key, model: FakeCoach())
    app = create_app(settings=settings, pipeline=pipeline, tracker=tracker)
    return TestClient(app)
