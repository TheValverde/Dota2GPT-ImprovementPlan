from fastapi.testclient import TestClient


def test_fantasy_roster_flow(client: TestClient) -> None:
    added = client.post(
        "/api/fantasy/roster",
        json={"account_id": 111, "amount": 60, "unit": "days"},
    )
    assert added.status_code == 200
    assert added.json()["personaname"] == "TestCarry"

    client.post("/api/fantasy/roster", json={"account_id": 222, "amount": 60, "unit": "days"})
    roster = client.get("/api/fantasy/roster", params={"amount": 60, "unit": "days"})
    assert roster.status_code == 200
    assert len(roster.json()["players"]) == 2

    week = client.get("/api/fantasy/players/111", params={"amount": 7, "unit": "days"})
    assert week.json()["match_count"] == 1

    deleted = client.delete("/api/fantasy/roster/111")
    assert deleted.status_code == 200
    leftover = client.get("/api/fantasy/roster", params={"amount": 60, "unit": "days"})
    assert leftover.json()["players"][0]["account_id"] == 222


def test_ranked_field_and_parse_missing(client: TestClient) -> None:
    client.post("/api/fantasy/roster", json={"account_id": 111, "amount": 7, "unit": "days"})
    field = client.get("/api/fantasy/players/111/field", params={"amount": 7, "unit": "days"})
    assert field.status_code == 200
    body = field.json()
    assert body["ranked_only"] is True
    assert body["you"]["account_id"] == 111
    names = {row["personaname"] for row in body["players"]}
    assert "TestSupport" in names
    assert "EnemyMid" in names
    assert body["unparsed_match_ids"]

    started = client.post(
        "/api/fantasy/players/111/parse-missing",
        params={"amount": 7, "unit": "days"},
    )
    assert started.status_code == 200
    assert started.json()["requested"] >= 1


def test_fantasy_ranked_and_hide_turbo_query(client: TestClient) -> None:
    client.post("/api/fantasy/roster", json={"account_id": 111, "amount": 60, "unit": "days"})
    month = client.get("/api/fantasy/players/111", params={"amount": 2, "unit": "months"})
    ranked = client.get(
        "/api/fantasy/players/111",
        params={"amount": 2, "unit": "months", "ranked_only": True},
    )
    no_turbo = client.get(
        "/api/fantasy/players/111",
        params={"amount": 2, "unit": "months", "hide_turbo": True},
    )
    assert month.json()["match_count"] == 2
    assert ranked.json()["match_count"] == 1
    assert no_turbo.json()["match_count"] == 1
    roster = client.get(
        "/api/fantasy/roster",
        params={"amount": 2, "unit": "months", "hide_turbo": True},
    )
    assert roster.json()["filters"]["hide_turbo"] is True
    assert roster.json()["players"][0]["match_count"] == 1


def test_fantasy_refresh_and_bad_span(client: TestClient) -> None:
    client.post("/api/fantasy/roster", json={"account_id": 111, "amount": 7, "unit": "days"})
    refreshed = client.post(
        "/api/fantasy/refresh",
        json={"amount": 20, "unit": "matches"},
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["span"]["unit"] == "matches"

    bad = client.get("/api/fantasy/roster", params={"amount": 7, "unit": "years"})
    assert bad.status_code == 400
