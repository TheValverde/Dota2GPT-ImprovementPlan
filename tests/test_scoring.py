import pytest

from dota2_coach.fantasy.scoring import Span, parse_span, score_match


def test_score_match_opendota_weights() -> None:
    score = score_match(
        {
            "kills": 10,
            "deaths": 5,
            "assists": 10,
            "last_hits": 200,
            "denies": 10,
            "gold_per_min": 500,
            "tower_kills": 2,
            "roshan_kills": 1,
            "teamfight_participation": 0.5,
            "obs_placed": 3,
            "camps_stacked": 2,
            "rune_pickups": 4,
            "firstblood_claimed": 1,
            "stuns": 20,
        }
    )
    assert score.total == 20.6
    assert score.parsed is True


def test_score_match_missing_parsed_fields() -> None:
    score = score_match({"kills": 1, "deaths": 1, "assists": 1})
    assert score.parsed is False
    assert score.total == 3.1


def test_span_conversions() -> None:
    assert Span(2, "weeks").as_days() == 14
    assert Span(1, "months").as_days() == 30
    assert Span(20, "matches").match_limit() == 20
    assert parse_span(7, "days").label() == "7 days"


def test_span_rejects_bad_unit() -> None:
    with pytest.raises(ValueError):
        parse_span(3, "years")
