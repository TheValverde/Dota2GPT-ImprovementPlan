from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.normalize import build_match_brief
from dota2_coach.opendota.opening import OPENING_NOTE, build_map_opening, build_opening_sequence


def _opening_match() -> tuple[dict, dict, GameConstants]:
    constants = GameConstants(
        heroes={
            3: "Bane",
            6: "Drow Ranger",
            27: "Shadow Shaman",
            108: "Underlord",
            135: "Dawnbreaker",
        }
    )
    bane = {
        "hero_id": 3,
        "player_slot": 128,
        "account_id": 1,
        "personaname": "Hugo",
        "isRadiant": False,
        "lane": 1,
        "lane_role": 3,
        "obs_log": [{"time": -39}, {"time": 291}, {"time": 629}],
        "sen_log": [{"time": -11}, {"time": 98}],
        "kills_log": [
            {"time": 174, "key": "npc_dota_hero_drow_ranger"},
            {"time": 197, "key": "npc_dota_hero_shadow_shaman"},
            {"time": 212, "key": "npc_dota_hero_drow_ranger"},
        ],
        "killed": {"npc_dota_courier": 2},
    }
    drow = {
        "hero_id": 6,
        "player_slot": 4,
        "account_id": 2,
        "personaname": "Castro",
        "isRadiant": True,
        "lane": 1,
        "lane_role": 1,
        "kills_log": [{"time": 168, "key": "npc_dota_hero_dawnbreaker"}],
    }
    shaman = {
        "hero_id": 27,
        "player_slot": 1,
        "account_id": 3,
        "personaname": "Chango",
        "isRadiant": True,
        "lane": 1,
        "lane_role": 1,
    }
    dawn = {
        "hero_id": 135,
        "player_slot": 129,
        "account_id": 4,
        "personaname": "DB",
        "isRadiant": False,
        "lane": 1,
        "lane_role": 3,
    }
    underlord = {
        "hero_id": 108,
        "player_slot": 3,
        "account_id": 5,
        "personaname": "CatWizard",
        "isRadiant": True,
        "lane": 3,
        "lane_role": 3,
        "kills_log": [{"time": 4, "key": "npc_dota_hero_silencer"}],
    }
    match = {
        "match_id": 8933116845,
        "radiant_win": False,
        "duration": 2193,
        "players": [drow, shaman, bane, dawn, underlord],
        "objectives": [
            {
                "time": 114,
                "type": "CHAT_MESSAGE_COURIER_LOST",
                "team": 2,
                "killer": 128,
            },
            {
                "time": 154,
                "type": "CHAT_MESSAGE_COURIER_LOST",
                "team": 2,
                "killer": 128,
            },
            {
                "time": 393,
                "type": "building_kill",
                "key": "npc_dota_goodguys_tower1_bot",
                "player_slot": 129,
            },
            {
                "time": 472,
                "type": "building_kill",
                "key": "npc_dota_goodguys_tower1_mid",
                "player_slot": 2,
            },
            {
                "time": 610,
                "type": "CHAT_MESSAGE_COURIER_LOST",
                "team": 2,
                "killer": 132,
            },
        ],
    }
    return match, bane, constants


def test_opening_sequence_is_ward_then_couriers_then_lane_kills() -> None:
    match, bane, constants = _opening_match()
    rows = build_opening_sequence(match, constants, bane)
    kinds = [(row["time"], row["event"], row.get("victim") or row.get("courier_team")) for row in rows]
    assert kinds[:8] == [
        ("-0:39", "observer", None),
        ("-0:11", "sentry", None),
        ("1:38", "sentry", None),
        ("1:54", "courier_kill", "Radiant"),
        ("2:34", "courier_kill", "Radiant"),
        ("2:48", "hero_kill", "Dawnbreaker"),
        ("2:54", "hero_kill", "Drow Ranger"),
        ("3:17", "hero_kill", "Shadow Shaman"),
    ]
    assert rows[0]["by_focus"] is True
    assert rows[3]["by"] == "Bane"
    assert rows[5]["by"] == "Drow Ranger"
    assert rows[5]["by_focus"] is False
    assert rows[6]["by_focus"] is True
    assert any(row["event"] == "tower" and "tower1 bot" in row.get("building", "") for row in rows)
    assert all(row.get("victim") != "Silencer" for row in rows)
    assert all("tower1 mid" not in row.get("building", "") for row in rows)
    assert all(row["event"] != "courier_kill" or row["time"] != "10:10" for row in rows)


def test_map_opening_keeps_other_lanes() -> None:
    match, bane, constants = _opening_match()
    extra = build_map_opening(match, constants, bane)
    victims = [row.get("victim") for row in extra if row["event"] == "hero_kill"]
    assert "Silencer" in victims
    assert "Drow Ranger" not in victims
    assert any("tower1 mid" in row.get("building", "") for row in extra)


def test_brief_exposes_opening_sequence_and_note(
    sample_match: dict, constants: GameConstants
) -> None:
    player = dict(sample_match["players"][0])
    player["obs_log"] = [{"time": -39}]
    player["killed"] = {"npc_dota_courier": 2}
    player["kills_log"] = [{"time": 174, "key": "npc_dota_hero_invoker"}]
    match = dict(sample_match)
    match["players"] = [player, *sample_match["players"][1:]]
    match["objectives"] = [
        {
            "time": 114,
            "type": "CHAT_MESSAGE_COURIER_LOST",
            "team": 2,
            "killer": 0,
        }
    ]
    brief = build_match_brief(match, "TestCarry", constants)
    times = [row["event"] for row in brief["opening_sequence"]]
    assert times[:3] == ["observer", "courier_kill", "hero_kill"]
    assert brief["opening_note"] == OPENING_NOTE
    assert brief["focus_player"]["courier_kills"] == 2
