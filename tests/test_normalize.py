import pytest

from dota2_coach.errors import PlayerNotInMatchError
from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.labels import format_duration, rank_label
from dota2_coach.opendota.normalize import build_match_brief, find_focus_player


def test_format_duration() -> None:
    assert format_duration(2460) == "41:00"
    assert format_duration(92) == "1:32"
    assert format_duration(-70) == "-1:10"


def test_rank_label() -> None:
    assert rank_label(65) == "Ancient 5"
    assert rank_label(80) == "Immortal"
    assert rank_label(None) is None


def test_find_focus_player_by_name_and_id(sample_match: dict) -> None:
    players = sample_match["players"]
    assert find_focus_player(players, "testcarry")["account_id"] == 111
    assert find_focus_player(players, "111")["personaname"] == "TestCarry"
    assert find_focus_player(players, "Enemy")["account_id"] == 222


def test_find_focus_player_missing(sample_match: dict) -> None:
    with pytest.raises(PlayerNotInMatchError) as exc:
        find_focus_player(sample_match["players"], "Nope")
    assert "Nope" in str(exc.value)
    assert "TestCarry" in exc.value.available


def test_build_match_brief_uses_names(sample_match: dict, constants: GameConstants) -> None:
    brief = build_match_brief(sample_match, "TestCarry", constants)
    assert brief["duration"] == "41:00"
    assert brief["game_mode"] == "All Pick"
    assert brief["focus_player"]["hero"] == "Anti-Mage"
    assert brief["focus_player"]["team"] == "Radiant"
    assert brief["focus_player"]["won"] is True
    assert "Blink Dagger" in brief["focus_player"]["items"]
    assert brief["focus_player"]["rank"] == "Ancient 5"
    names = {row["name"] for row in brief["scoreboard"]}
    assert "Anonymous" in names
    assert brief["parsed"] is False
    assert brief["focus_player"]["assignment"] == "Safe core"
    assert brief["focus_player"]["benchmarks"]["gold_per_min"]["percentile"] == 72
    assert brief["focus_player"]["benchmark_source"] == "match"
    assert "safelane" in brief["focus_player"]["lane_matchup_note"].lower()


def test_build_match_brief_pairs_safelane_against_offlane(
    sample_match: dict, constants: GameConstants
) -> None:
    offlaner = {
        "account_id": 555,
        "personaname": "EnemyOff",
        "hero_id": 14,
        "player_slot": 129,
        "isRadiant": False,
        "lane": 1,
        "lane_role": 3,
        "kills": 3,
        "deaths": 5,
        "assists": 8,
        "gold_per_min": 400,
        "last_hits": 140,
    }
    match = dict(sample_match)
    match["players"] = [*sample_match["players"], offlaner]
    carry = dict(sample_match["players"][0])
    carry["lane"] = 1
    match["players"][0] = carry
    brief = build_match_brief(match, "TestCarry", constants)
    against = {row["name"] for row in brief["focus_player"]["laned_against"]}
    assert against == {"EnemyOff"}
    assert brief["focus_player"]["map_lane"] == "Bottom"


def test_build_match_brief_uses_hero_curve_without_match_benchmarks(
    sample_match: dict, constants: GameConstants
) -> None:
    player = dict(sample_match["players"][0])
    player.pop("benchmarks", None)
    match = dict(sample_match)
    match["players"] = [player, *sample_match["players"][1:]]
    curve = {
        "result": {
            "gold_per_min": [
                {"percentile": 0.5, "value": 600},
                {"percentile": 0.8, "value": 750},
            ]
        }
    }
    brief = build_match_brief(match, "TestCarry", constants, hero_benchmarks=curve)
    assert brief["focus_player"]["benchmark_source"] == "hero_curve"
    assert brief["focus_player"]["benchmarks"]["gold_per_min"]["percentile"] == 74


def test_build_match_brief_includes_spell_targets_and_macro(
    sample_match: dict, constants: GameConstants
) -> None:
    player = dict(sample_match["players"][0])
    player["ability_targets"] = {
        "bane_fiends_grip": {"npc_dota_hero_drow_ranger": 2},
        "bane_enfeeble": {"npc_dota_hero_crystal_maiden": 1},
    }
    player["ability_uses"] = {"bane_fiends_grip": 2, "bane_enfeeble": 1}
    match = dict(sample_match)
    match["players"] = [player, *sample_match["players"][1:]]
    match["objectives"] = [
        {
            "time": 393,
            "type": "building_kill",
            "key": "npc_dota_goodguys_tower1_bot",
            "slot": 0,
        }
    ]
    match["radiant_gold_adv"] = [0, -500, -2000]
    brief = build_match_brief(match, "TestCarry", constants)
    assert brief["focus_player"]["ability_targets"]["bane_fiends_grip"]["Drow Ranger"] == 2
    assert brief["macro"]["objectives"][0]["by"] == "Anti-Mage"
    assert brief["macro"]["winner"] == "Radiant"
