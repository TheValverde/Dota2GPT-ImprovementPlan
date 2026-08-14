from dota2_coach.opendota.client import MATCH_PROJECT
from dota2_coach.opendota.parsed import account_id_from_player, first_parsed, is_parsed


def test_is_parsed() -> None:
    assert is_parsed({"version": 22}) is True
    assert is_parsed({"version": None}) is False
    assert is_parsed({}) is False


def test_first_parsed_skips_unparsed() -> None:
    rows = [
        {"match_id": 1, "version": None},
        {"match_id": 2, "version": 21},
        {"match_id": 3, "version": 22},
    ]
    assert first_parsed(rows)["match_id"] == 2
    assert first_parsed([{"match_id": 1}]) is None


def test_account_id_from_player() -> None:
    assert account_id_from_player("286841060") == 286841060
    assert account_id_from_player("  111  ") == 111
    assert account_id_from_player("Hugo") is None


def test_version_is_projected() -> None:
    assert "version" in MATCH_PROJECT
