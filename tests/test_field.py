from copy import deepcopy
from time import time

from dota2_coach.fantasy.field import aggregate_ranked_field
from dota2_coach.fantasy.scoring import Span
from dota2_coach.opendota.filters import FantasyFilters
from tests.conftest import _match_row


def test_aggregate_field_scores_lobby_and_marks_duo(sample_match: dict, constants) -> None:
    second = deepcopy(sample_match)
    second["match_id"] = 7000000004
    field = aggregate_ranked_field(111, [sample_match, second], constants)
    assert field["match_count"] == 2
    assert field["you"]["account_id"] == 111
    assert field["you"]["relation"] == "you"
    assert field["duo"]["account_id"] == 444
    assert field["duo"]["teammate_games"] == 2
    by_id = {row["account_id"]: row for row in field["players"]}
    assert by_id[222]["relation"] == "enemy"
    assert by_id[222]["enemy_games"] == 2
    assert by_id[111]["games"] == 2
    assert by_id[444]["games"] == 2


def test_ranked_field_and_parse_missing(tracker, opendota, sample_match) -> None:
    second = deepcopy(sample_match)
    second["match_id"] = 7000000004
    opendota._full_matches[7000000004] = second
    opendota._matches[111].insert(0, _match_row(7000000004, int(time()) - 86400))
    tracker.add_player(111, Span(7, "days"))
    field = tracker.ranked_field(111, Span(7, "days"))
    assert field["ranked_only"] is True
    assert field["match_count"] == 2
    assert field["duo"]["personaname"] == "TestSupport"
    assert 7000000001 in field["unparsed_match_ids"]

    parsed = tracker.parse_missing_ranked(111, Span(7, "days"))
    assert parsed["requested"] == 2
    for job in parsed["jobs"]:
        opendota.parse_job(job["job_id"])

    field_after = tracker.ranked_field(111, Span(7, "days"))
    assert field_after["parsed_matches"] == 2
    assert field_after["unparsed_match_ids"] == []
    ranked = tracker.player_card(111, Span(7, "days"), FantasyFilters(ranked_only=True))
    assert ranked["match_count"] == 2
