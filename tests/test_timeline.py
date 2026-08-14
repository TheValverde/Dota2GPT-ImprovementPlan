from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.timeline import build_macro, compact_teamfights


def test_macro_includes_towers_fights_and_gold() -> None:
    constants = GameConstants(heroes={3: "Bane", 6: "Drow Ranger", 135: "Dawnbreaker"})
    bane = {"hero_id": 3, "player_slot": 128, "account_id": 1}
    drow = {"hero_id": 6, "player_slot": 0, "account_id": 2}
    dawn = {"hero_id": 135, "player_slot": 129, "account_id": 3}
    match = {
        "radiant_win": False,
        "radiant_gold_adv": [0, 100, -800, -2000, -4000, -9000],
        "players": [drow, {"hero_id": 1, "player_slot": 1}, {"hero_id": 1, "player_slot": 2}, {"hero_id": 1, "player_slot": 3}, {"hero_id": 1, "player_slot": 4}, bane, dawn],
        "objectives": [
            {"time": 393, "type": "building_kill", "key": "npc_dota_goodguys_tower1_bot", "slot": 6},
            {"time": 1438, "type": "CHAT_MESSAGE_ROSHAN_KILL"},
        ],
        "teamfights": [
            {
                "start": 253,
                "deaths": 2,
                "players": [
                    {"damage": 100, "deaths": 1},
                    {},
                    {},
                    {},
                    {},
                    {"damage": 389, "deaths": 0},
                    {"damage": 455, "deaths": 0},
                ],
            }
        ],
    }
    macro = build_macro(match, constants, bane)
    assert macro["winner"] == "Dire"
    assert macro["objectives"][0]["by"] == "Dawnbreaker"
    assert "tower1 bot" in macro["objectives"][0]["building"]
    fights = compact_teamfights(match, constants, bane)
    assert fights[0]["focus_damage"] == 389
    assert fights[0]["focus_died"] is False
    assert "Drow Ranger" in fights[0]["died"]
    assert macro["gold_advantage"][0]["leading"] == "Even"
