from fastapi.testclient import TestClient

from dota2_coach.api.app import create_app
from dota2_coach.api.routes import get_pipeline
from dota2_coach.config import Settings
from dota2_coach.pipeline import AnalysisPipeline
from tests.conftest import FakeOpenDota


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_player_search(client: TestClient) -> None:
    response = client.get("/api/players/search", params={"q": "Test"})
    assert response.status_code == 200
    assert response.json()[0]["account_id"] == 111


def test_recent_matches(client: TestClient) -> None:
    response = client.get("/api/players/111/recent-matches")
    assert response.status_code == 200
    body = response.json()[0]
    assert body["hero"] == "Anti-Mage"
    assert body["won"] is True


def test_analyze(client: TestClient) -> None:
    response = client.post(
        "/api/analyze",
        json={"player": "TestCarry", "match_id": 7000000001},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["report"]["grade"] == "A"
    assert body["brief"]["focus_player"]["hero"] == "Anti-Mage"


def test_analyze_unknown_player(client: TestClient) -> None:
    response = client.post(
        "/api/analyze",
        json={"player": "Missing", "match_id": 7000000001},
    )
    assert response.status_code == 404
    assert "Missing" in response.json()["detail"]


def test_index(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Match Coach" in response.text


def test_analyze_requires_openai_key(sample_match, constants) -> None:
    settings = Settings(openai_api_key="", openai_model="gpt-test")
    pipeline = AnalysisPipeline(settings, opendota=FakeOpenDota(sample_match, constants))
    app = create_app()
    app.dependency_overrides[get_pipeline] = lambda: pipeline
    local_client = TestClient(app)
    response = local_client.post(
        "/api/analyze",
        json={"player": "TestCarry", "match_id": 7000000001},
    )
    assert response.status_code == 503
