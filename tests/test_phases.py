from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.ledger import build_event_ledger
from dota2_coach.opendota.phases import build_phases


def test_phases_summarize_kills_towers_items_and_gold() -> None:
    constants = GameConstants(
        heroes={22: "Zeus", 11: "Shadow Fiend"},
        hero_npcs={22: "npc_dota_hero_zuus", 11: "npc_dota_hero_nevermore"},
    )
    zeus = {
        "hero_id": 22,
        "player_slot": 130,
        "isRadiant": False,
        "lane": 2,
        "purchase_log": [
            {"key": "bottle", "time": 89},
            {"key": "kaya", "time": 657},
            {"key": "refresher", "time": 1645},
        ],
        "kills_log": [
            {"time": 77, "key": "npc_dota_hero_nevermore"},
            {"time": 745, "key": "npc_dota_hero_nevermore"},
            {"time": 1600, "key": "npc_dota_hero_nevermore"},
        ],
    }
    sf = {
        "hero_id": 11,
        "player_slot": 4,
        "isRadiant": True,
        "lane": 2,
        "kills_log": [{"time": 1103, "key": "npc_dota_hero_zuus"}],
    }
    match = {
        "duration": 2094,
        "players": [sf, zeus],
        "objectives": [
            {"time": 641, "type": "building_kill", "key": "npc_dota_badguys_tower1_mid"},
            {"time": 1408, "type": "building_kill", "key": "npc_dota_goodguys_tower1_mid"},
        ],
        "radiant_gold_adv": [0] * 10 + [-500] * 15 + [-9000] * 10,
    }
    ledger = build_event_ledger(match, constants, zeus)
    phases = build_phases(match, ledger, zeus)
    assert [p["phase"] for p in phases] == ["laning", "midgame", "closing"]

    laning = phases[0]
    assert laning["window"] == "0:00-10:00"
    assert laning["focus_kills"] == 1
    assert laning["focus_deaths"] == 0
    assert laning["focus_items"] == ["bottle"]
    # adv[10] is -500 and the focus player is Dire, so the lead is +500
    assert laning["gold_lead_at_end"] == 500

    midgame = phases[1]
    assert midgame["focus_kills"] == 1
    assert midgame["focus_deaths"] == 1
    assert midgame["towers_lost"] == 1
    assert midgame["towers_taken"] == 1
    assert midgame["gold_lead_at_end"] == 9000

    closing = phases[2]
    assert closing["window"] == "25:00-34:54"
    assert closing["focus_kills"] == 1
    assert closing["focus_items"] == ["refresher"]


def test_phases_skip_missing_late_game() -> None:
    constants = GameConstants(heroes={22: "Zeus"}, hero_npcs={})
    zeus = {"hero_id": 22, "player_slot": 130, "isRadiant": False}
    match = {"duration": 900, "players": [zeus]}
    phases = build_phases(match, [], zeus)
    assert [p["phase"] for p in phases] == ["laning", "midgame"]
