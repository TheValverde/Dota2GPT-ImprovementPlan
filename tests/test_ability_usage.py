from dota2_coach.opendota.ability_usage import build_ability_usage
from dota2_coach.opendota.constants import GameConstants


def _constants() -> GameConstants:
    return GameConstants(
        heroes={
            3: "Bane",
            4: "Bloodseeker",
            6: "Drow Ranger",
            74: "Invoker",
            135: "Dawnbreaker",
        },
        hero_npcs={
            3: "npc_dota_hero_bane",
            4: "npc_dota_hero_bloodseeker",
            6: "npc_dota_hero_drow_ranger",
            74: "npc_dota_hero_invoker",
            135: "npc_dota_hero_dawnbreaker",
        },
    )


def test_build_ability_usage_splits_targets_and_fights() -> None:
    constants = _constants()
    bane = {
        "hero_id": 3,
        "player_slot": 1,
        "account_id": 1,
        "ability_uses": {
            "bane_nightmare": 3,
            "bane_nightmare_end": 2,
            "bane_fiends_grip": 1,
        },
        "ability_targets": {
            "bane_nightmare": {
                "npc_dota_hero_invoker": 2,
                "npc_dota_hero_bane": 1,
            },
            "bane_fiends_grip": {"npc_dota_hero_invoker": 1},
        },
    }
    drow = {"hero_id": 6, "player_slot": 0, "account_id": 2}
    invoker = {"hero_id": 74, "player_slot": 128, "account_id": 3}
    match = {
        "players": [drow, bane, invoker],
        "teamfights": [
            {
                "start": 830,
                "deaths": 2,
                "players": [
                    {"damage": 100, "deaths": 1},
                    {
                        "damage": 389,
                        "deaths": 0,
                        "ability_uses": {
                            "bane_nightmare": 1,
                            "bane_nightmare_end": 1,
                            "bane_fiends_grip": 1,
                        },
                    },
                    {"damage": 455, "deaths": 0},
                ],
            }
        ],
    }
    usage = build_ability_usage(match, constants, bane)
    assert usage is not None
    nightmare = next(row for row in usage["abilities"] if row["ability_key"] == "bane_nightmare")
    assert nightmare["casts"] == 3
    assert nightmare["manual_ends"] == 2
    assert nightmare["targets"]["enemy"] == [{"hero": "Invoker", "count": 2}]
    assert nightmare["targets"]["self"] == [{"hero": "Bane", "count": 1}]
    fight = usage["teamfights"][0]
    assert fight["time"] == "13:50"
    assert fight["ability_casts"]["Nightmare"] == 1
    assert fight["died"] == ["Drow Ranger"]


def test_build_ability_usage_returns_none_without_data() -> None:
    constants = _constants()
    focus = {"hero_id": 3, "player_slot": 1}
    assert build_ability_usage({"players": [focus]}, constants, focus) is None
