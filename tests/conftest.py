import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dota2_coach.analysis.schema import CoachReport, FocusArea
from dota2_coach.api.app import create_app
from dota2_coach.api.routes import get_pipeline
from dota2_coach.config import Settings
from dota2_coach.opendota.constants import GameConstants
from dota2_coach.pipeline import AnalysisPipeline


class FakeOpenDota:
    def __init__(self, match: dict, constants: GameConstants) -> None:
        self._match = match
        self._constants = constants

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
def client(
    sample_match: dict,
    constants: GameConstants,
    monkeypatch: pytest.MonkeyPatch,
) -> TestClient:
    settings = Settings(openai_api_key="test", openai_model="gpt-test")
    pipeline = AnalysisPipeline(settings, opendota=FakeOpenDota(sample_match, constants))
    monkeypatch.setattr("dota2_coach.pipeline.MatchCoach", lambda api_key, model: FakeCoach())
    app = create_app()
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    return TestClient(app)
