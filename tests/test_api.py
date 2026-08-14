from fastapi.testclient import TestClient

from dota2_coach.api.app import create_app
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
    assert body["brief"]["focus_player"]["assignment"] == "Safe core"
    assert body["brief"]["focus_player"]["benchmarks"]["gold_per_min"]["percentile"] == 72
    assert body["brief"]["parsed"] is False


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
    assert "Dota Coach" in response.text
    assert "Fantasy" in response.text
    assert "Ranked only" in response.text
    assert "Hide turbo" in response.text


def test_analyze_requires_openai_key(sample_match, constants, tmp_path) -> None:
    settings = Settings(openai_api_key="", openai_model="gpt-test", data_dir=str(tmp_path))
    pipeline = AnalysisPipeline(settings, opendota=FakeOpenDota(sample_match, constants))
    app = create_app(settings=settings, pipeline=pipeline)
    local_client = TestClient(app)
    response = local_client.post(
        "/api/analyze",
        json={"player": "TestCarry", "match_id": 7000000001},
    )
    assert response.status_code == 503


def test_request_parse_then_status(client: TestClient) -> None:
    started = client.post("/api/matches/7000000001/parse")
    assert started.status_code == 200
    body = started.json()
    assert body["parsed"] is False
    assert body["job_id"] == "job-1"

    status = client.get(
        "/api/matches/7000000001/parse-status",
        params={"job_id": "job-1"},
    )
    assert status.status_code == 200
    assert status.json()["parsed"] is True

    again = client.post("/api/matches/7000000001/parse")
    assert again.status_code == 200
    assert again.json()["parsed"] is True
