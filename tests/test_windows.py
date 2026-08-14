from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.ledger import build_event_ledger
from dota2_coach.opendota.windows import (
    build_death_windows,
    build_gold_swings,
    build_objective_windows,
)


def _setup() -> tuple[dict, dict, list[dict]]:
    constants = GameConstants(
        heroes={22: "Zeus", 11: "Shadow Fiend", 30: "Witch Doctor", 135: "Dawnbreaker"},
        hero_npcs={
            22: "npc_dota_hero_zuus",
            11: "npc_dota_hero_nevermore",
            30: "npc_dota_hero_witch_doctor",
            135: "npc_dota_hero_dawnbreaker",
        },
    )
    zeus = {
        "hero_id": 22,
        "player_slot": 130,
        "isRadiant": False,
        "lane": 2,
        "purchase_log": [
            {"key": "point_booster", "time": 1257},
            {"key": "ultimate_scepter", "time": 1267},
        ],
        "kills_log": [
            {"time": 632, "key": "npc_dota_hero_witch_doctor"},
            {"time": 639, "key": "npc_dota_hero_dawnbreaker"},
        ],
    }
    sf = {
        "hero_id": 11,
        "player_slot": 4,
        "isRadiant": True,
        "lane": 2,
        "kills_log": [],
    }
    wd = {
        "hero_id": 30,
        "player_slot": 3,
        "isRadiant": True,
        "lane": 3,
        "kills_log": [{"time": 1103, "key": "npc_dota_hero_zuus"}],
    }
    dawn = {"hero_id": 135, "player_slot": 0, "isRadiant": True, "lane": 3, "kills_log": []}
    match = {
        "duration": 2094,
        "players": [dawn, wd, sf, zeus],
        "objectives": [
            {
                "time": 641,
                "type": "building_kill",
                "key": "npc_dota_badguys_tower1_mid",
                "player_slot": 4,
            },
            {
                "time": 1290,
                "type": "building_kill",
                "key": "npc_dota_badguys_tower1_top",
                "player_slot": 4,
            },
        ],
        "teamfights": [{"start": 1100, "end": 1140, "deaths": 3, "players": []}],
        "radiant_gold_adv": [0] * 18 + [1379, 2219, 2054, 1515, 90, -2784, -5360],
    }
    ledger = build_event_ledger(match, constants, zeus)
    return match, zeus, ledger


def test_objective_window_flags_tower_lost_during_side_fight() -> None:
    match, zeus, ledger = _setup()
    windows = build_objective_windows(ledger, zeus)
    mid_t1 = next(w for w in windows if "tower1 mid" in w["objective"])
    assert mid_t1["lost_by_focus_team"] is True
    assert mid_t1["focus_in_action"] is True
    assert mid_t1["focus_was_fighting_elsewhere"] is True
    assert any(k["victim"] == "Witch Doctor" for k in mid_t1["kills_around"])
    top_t1 = next(w for w in windows if "tower1 top" in w["objective"])
    assert "kills_around" not in top_t1
    assert "focus_was_fighting_elsewhere" not in top_t1


def test_death_window_has_cost_fight_and_delayed_item() -> None:
    match, zeus, ledger = _setup()
    deaths = build_death_windows(match, ledger, zeus)
    assert len(deaths) == 1
    death = deaths[0]
    assert death["time"] == "18:23"
    assert death["killed_by"] == "Witch Doctor"
    assert death["in_teamfight_at"] == "18:20"
    assert death["enemy_gold_swing_next_2_min"] == 2054 - 1379
    assert death["next_item_after"]["item"] == "ultimate scepter"


def test_gold_swings_are_focus_relative() -> None:
    match, zeus, _ = _setup()
    swings = build_gold_swings(match, zeus)
    assert swings
    first = swings[0]
    assert first["toward"] == "Dire"
    assert first["toward_focus_team"] is True
    assert first["swing"] >= 3000
