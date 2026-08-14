from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.lane_swing import build_lane_swing


def test_lane_swing_tracks_early_kills_and_gold_gap() -> None:
    constants = GameConstants(
        heroes={11: "Shadow Fiend", 22: "Zeus"},
        hero_npcs={11: "npc_dota_hero_nevermore", 22: "npc_dota_hero_zuus"},
    )
    zeus = {
        "hero_id": 22,
        "player_slot": 130,
        "account_id": 1,
        "isRadiant": False,
        "lane": 2,
        "lane_role": 2,
        "last_hits": 214,
        "gold_per_min": 665,
        "kills_log": [
            {"time": 77, "key": "npc_dota_hero_nevermore"},
            {"time": 157, "key": "npc_dota_hero_nevermore"},
            {"time": 745, "key": "npc_dota_hero_nevermore"},
        ],
        "gold_t": [0, 332, 889, 1371, 1745, 2126, 2390, 2809, 3149, 3461, 3918],
        "xp_t": [0, 240, 878, 1599, 2082, 2536, 2845, 3656, 3963, 4356, 4922],
        "lh_t": [0, 4, 10, 14, 20, 26, 29, 37, 41, 44, 51],
    }
    sf = {
        "hero_id": 11,
        "player_slot": 4,
        "account_id": 2,
        "isRadiant": True,
        "lane": 2,
        "lane_role": 2,
        "last_hits": 197,
        "gold_per_min": 422,
        "deaths": 11,
        "kills_log": [{"time": 909, "key": "npc_dota_hero_spectre"}],
        "purchase_log": [
            {"key": "tango", "time": -80},
            {"key": "bottle", "time": 117},
            {"key": "power_treads", "time": 586},
            {"key": "dragon_lance", "time": 829},
        ],
        "gold_t": [0, 321, 677, 802, 1089, 1377, 1769, 2025, 2467, 2932, 3435],
        "xp_t": [0, 268, 748, 956, 1410, 1920, 2548, 2791, 3331, 4021, 4786],
        "lh_t": [0, 4, 10, 11, 15, 20, 27, 29, 37, 45, 54],
    }
    match = {"players": [zeus, sf]}
    swing = build_lane_swing(match, constants, zeus)
    assert swing is not None
    assert swing["opponent"] == "Shadow Fiend"
    assert [row["time"] for row in swing["early_kills_on_opponent"]] == ["1:17", "2:37"]
    assert swing["kills_on_opponent_count"] == 3
    assert swing["opponent_first_kill"] == "15:09"
    three = next(row for row in swing["snapshots"] if row["time"] == "3:00")
    assert three["gold_lead"] == 569
    assert three["xp_lead"] == 643
    ten = next(row for row in swing["snapshots"] if row["time"] == "10:00")
    assert ten["opponent_lh"] == 54
    assert ten["focus_lh"] == 51
    assert swing["opponent_items"][0] == {"item": "bottle", "time": "1:57"}
    assert swing["opponent_deaths"] == 11
