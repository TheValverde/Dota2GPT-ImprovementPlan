from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.ledger import build_event_ledger, map_region


def _constants() -> GameConstants:
    return GameConstants(
        heroes={
            3: "Bane",
            6: "Drow Ranger",
            27: "Shadow Shaman",
            94: "Muerta",
            135: "Dawnbreaker",
        },
        hero_npcs={
            3: "npc_dota_hero_bane",
            6: "npc_dota_hero_drow_ranger",
            27: "npc_dota_hero_shadow_shaman",
            94: "npc_dota_hero_muerta",
            135: "npc_dota_hero_dawnbreaker",
        },
    )


def _match() -> tuple[dict, dict]:
    bane = {
        "hero_id": 3,
        "player_slot": 128,
        "isRadiant": False,
        "lane": 1,
        "obs_log": [{"time": -39, "x": 144.3, "y": 89.4}],
        "sen_log": [{"time": -11, "x": 161.9, "y": 97.2}],
        "runes_log": [{"time": 0, "key": 5}, {"time": 360, "key": 6}],
        "purchase_log": [
            {"key": "tango", "time": -89},
            {"key": "boots", "time": 140},
            {"key": "point_booster", "time": 900},
            {"key": "ultimate_scepter", "time": 910},
        ],
        "kills_log": [
            {"time": 174, "key": "npc_dota_hero_drow_ranger"},
            {"time": 197, "key": "npc_dota_hero_shadow_shaman"},
        ],
    }
    drow = {
        "hero_id": 6,
        "player_slot": 4,
        "isRadiant": True,
        "lane": 1,
        "kills_log": [{"time": 168, "key": "npc_dota_hero_dawnbreaker"}],
    }
    shaman = {
        "hero_id": 27,
        "player_slot": 1,
        "isRadiant": True,
        "lane": 1,
        "kills_log": [{"time": 436, "key": "npc_dota_hero_bane"}],
    }
    dawn = {
        "hero_id": 135,
        "player_slot": 129,
        "isRadiant": False,
        "lane": 3,
        "kills_log": [{"time": 300, "key": "npc_dota_hero_muerta"}],
    }
    muerta = {
        "hero_id": 94,
        "player_slot": 2,
        "isRadiant": True,
        "lane": 2,
        "kills_log": [],
    }
    match = {
        "duration": 2193,
        "radiant_win": False,
        "players": [drow, shaman, bane, dawn, muerta],
        "objectives": [
            {"time": 114, "type": "CHAT_MESSAGE_COURIER_LOST", "team": 2, "killer": 128},
            {
                "time": 393,
                "type": "building_kill",
                "key": "npc_dota_goodguys_tower1_bot",
                "player_slot": 129,
            },
            {"time": 1438, "type": "CHAT_MESSAGE_ROSHAN_KILL", "team": 3},
            {"time": 1439, "type": "CHAT_MESSAGE_AEGIS", "player_slot": 129},
            {"time": 77, "type": "CHAT_MESSAGE_FIRSTBLOOD", "player_slot": 4},
        ],
    }
    return match, bane


def test_map_region_labels() -> None:
    assert map_region(144.3, 89.4) == "bottom half, Radiant side"
    assert map_region(128.1, 128.7) == "mid, river"
    assert map_region(90, 160) == "top half, river"
    assert map_region(None, 90) is None


def test_ledger_is_one_clock_with_focus_tags() -> None:
    match, bane = _match()
    rows = build_event_ledger(match, _constants(), bane)
    kinds = [row["event"] for row in rows]
    assert kinds[0] == "observer_ward"
    assert rows[0]["region"] == "bottom half, Radiant side"
    courier = next(row for row in rows if row["event"] == "courier_kill")
    assert courier["by"] == "Bane"
    assert courier["by_focus"] is True
    assert courier["courier_team"] == "Radiant"
    first_kill = next(row for row in rows if row["event"] == "hero_kill")
    assert first_kill["victim"] == "Dawnbreaker"
    assert first_kill["by_team"] == "Radiant"
    assert first_kill["focus_lane"] is True
    bane_kill = next(row for row in rows if row.get("by_focus") and row["event"] == "hero_kill")
    assert bane_kill["victim"] == "Drow Ranger"
    off_lane = next(row for row in rows if row["event"] == "hero_kill" and row["by"] == "Dawnbreaker")
    assert off_lane["focus_lane"] is False
    death = next(row for row in rows if row.get("victim_is_focus"))
    assert death["by"] == "Shadow Shaman"
    tower = next(row for row in rows if row["event"] == "building")
    assert tower["lost_by"] == "Radiant"
    assert "tower1 bot" in tower["building"]
    runes = [row["rune"] for row in rows if row["event"] == "rune"]
    assert runes == ["Bounty", "Arcane"]
    items = [row["item"] for row in rows if row["event"] == "item"]
    assert items == ["boots", "ultimate scepter"]
    roshan = next(row for row in rows if row["event"] == "roshan")
    assert roshan["by_team"] == "Dire"
    aegis = next(row for row in rows if row["event"] == "aegis")
    assert aegis["by"] == "Dawnbreaker"
    fb = next(row for row in rows if row["event"] == "first_blood")
    assert fb["by"] == "Drow Ranger"
    times = [row["t"] for row in rows]
    assert times == sorted(times)
