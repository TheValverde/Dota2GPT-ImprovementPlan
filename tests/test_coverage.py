from dota2_coach.analysis.coverage import (
    build_checklist,
    missing_moments,
    repair_instruction,
)
from dota2_coach.analysis.schema import CoachReport


def _brief() -> dict:
    return {
        "death_windows": [
            {"time": "18:23", "killed_by": "Witch Doctor"},
            {"time": "20:58", "killed_by": "Dawnbreaker"},
        ],
        "objective_windows": [
            {"time": "10:41", "objective": "badguys tower1 mid", "lost_by_focus_team": True},
            {"time": "23:28", "objective": "goodguys tower1 mid", "lost_by": "Radiant"},
        ],
        "event_ledger": [{"time": "29:47", "event": "roshan"}],
        "gold_swings": [{"time": "21:00", "swing": 4299, "toward_focus_team": True}],
        "lane_swing": {
            "opponent": "Shadow Fiend",
            "early_kills_on_opponent": [{"time": "1:17", "hero": "Shadow Fiend"}],
        },
    }


def _report(match_read: str) -> CoachReport:
    return CoachReport(
        headline="h",
        match_read=match_read,
        grade="A",
        kda_context="k",
    )


def test_checklist_collects_required_moments() -> None:
    checklist = build_checklist(_brief())
    times = [item["time"] for item in checklist]
    assert times == ["18:23", "20:58", "10:41", "29:47", "21:00", "1:17"]


def test_missing_moments_uses_timestamp_boundaries() -> None:
    checklist = build_checklist(_brief())
    covered = _report(
        "Kill at 1:17 set the lane. Deaths at 18:23 and 20:58 cost the lead. "
        "Mid T1 fell 10:41. Rosh 29:47. Swing at 21:00."
    )
    assert missing_moments(covered, checklist) == []

    partial = _report("Death at 18:23. The 21:17 fight was fine.")
    missing = [item["time"] for item in missing_moments(partial, checklist)]
    assert "18:23" in " ".join(m for m in ["18:23"]) and "18:23" not in missing
    assert "1:17" in missing
    assert "20:58" in missing


def test_repair_instruction_names_the_misses() -> None:
    checklist = build_checklist(_brief())
    text = repair_instruction(checklist[:2])
    assert "18:23" in text
    assert "20:58" in text
    assert "Return the full corrected report" in text
