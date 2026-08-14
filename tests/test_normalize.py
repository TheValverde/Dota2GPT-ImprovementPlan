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
