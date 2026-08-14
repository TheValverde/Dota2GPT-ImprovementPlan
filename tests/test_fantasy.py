from dota2_coach.fantasy.scoring import Span
from dota2_coach.opendota.filters import FantasyFilters


def test_add_and_rank_players(tracker) -> None:
    tracker.add_player(111, Span(60, "days"))
    tracker.add_player(222, Span(60, "days"))
    summary = tracker.summary(Span(60, "days"))
    names = [row["personaname"] for row in summary["players"]]
    assert names[0] in {"TestCarry", "EnemyMid"}
    assert len(summary["players"]) == 2
    assert summary["players"][0]["total"] >= summary["players"][1]["total"]


def test_span_filters_old_matches(tracker) -> None:
    tracker.add_player(111, Span(60, "days"))
    week = tracker.player_card(111, Span(7, "days"))
    month = tracker.player_card(111, Span(2, "months"))
    last_match = tracker.player_card(111, Span(1, "matches"))
    assert week["match_count"] == 1
    assert month["match_count"] == 2
    assert last_match["match_count"] == 1
    assert last_match["matches"][0]["match_id"] == 7000000001


def test_ranked_and_turbo_filters(tracker) -> None:
    tracker.add_player(111, Span(2, "months"))
    all_games = tracker.player_card(111, Span(2, "months"))
    ranked = tracker.player_card(111, Span(2, "months"), FantasyFilters(ranked_only=True))
    no_turbo = tracker.player_card(111, Span(2, "months"), FantasyFilters(hide_turbo=True))
    assert all_games["match_count"] == 2
    assert ranked["match_count"] == 1
    assert ranked["matches"][0]["match_id"] == 7000000001
    assert no_turbo["match_count"] == 1
    assert no_turbo["matches"][0]["match_id"] == 7000000001


def test_remove_player(tracker) -> None:
    tracker.add_player(111, Span(7, "days"))
    tracker.remove_player(111)
    assert tracker.summary(Span(7, "days"))["players"] == []
