from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.form import build_recent_form


def test_recent_form_summarizes_and_excludes_current_match() -> None:
    constants = GameConstants(heroes={3: "Bane", 22: "Zeus"})
    rows = [
        {
            "match_id": 100 + i,
            "hero_id": 3 if i % 2 else 22,
            "kills": 5,
            "deaths": i,
            "assists": 10,
            "player_slot": 130,
            "radiant_win": i % 2 == 0,
            "start_time": 1000 - i,
        }
        for i in range(6)
    ]
    form = build_recent_form(rows, constants, exclude_match_id=100, limit=4)
    assert form["games"] == 4
    assert all(m["hero"] in {"Bane", "Zeus"} for m in form["matches"])
    assert form["matches"][0]["kda"] == "5/1/10"
    # first remaining row has radiant_win False and the player is Dire: a win
    assert form["matches"][0]["won"] is True
    assert form["avg_deaths"] == 2.5


def test_recent_form_flags_hero_spam() -> None:
    constants = GameConstants(heroes={3: "Bane"})
    rows = [
        {
            "match_id": i,
            "hero_id": 3,
            "kills": 2,
            "deaths": 3,
            "assists": 20,
            "player_slot": 0,
            "radiant_win": True,
            "start_time": i,
        }
        for i in range(5)
    ]
    form = build_recent_form(rows, constants)
    assert form["most_played"] == "Bane x5"
    assert form["wins"] == 5


def test_recent_form_empty_rows() -> None:
    constants = GameConstants()
    assert build_recent_form([], constants) is None
