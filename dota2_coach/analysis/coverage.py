from __future__ import annotations

import re
from typing import Any

from dota2_coach.analysis.schema import CoachReport

MAX_REPAIR_ITEMS = 12


def _add(
    items: list[dict[str, str]], seen: set[str], time: Any, moment: str
) -> None:
    if not time:
        return
    key = str(time)
    if key in seen:
        return
    seen.add(key)
    items.append({"time": key, "moment": moment})


def build_checklist(brief: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for death in brief.get("death_windows") or []:
        _add(items, seen, death.get("time"), f"focus death to {death.get('killed_by') or 'unknown'}")
    for window in brief.get("objective_windows") or []:
        if window.get("lost_by_focus_team"):
            _add(items, seen, window.get("time"), f"lost {window.get('objective') or 'objective'}")
    for row in brief.get("event_ledger") or []:
        if row.get("event") == "roshan":
            _add(items, seen, row.get("time"), "Roshan kill")
    for swing in brief.get("gold_swings") or []:
        direction = "toward the focus team" if swing.get("toward_focus_team") else "against the focus team"
        _add(items, seen, swing.get("time"), f"gold swing of {swing.get('swing')} {direction}")
    lane = brief.get("lane_swing") or {}
    early = lane.get("early_kills_on_opponent") or []
    if early:
        _add(
            items,
            seen,
            early[0].get("time"),
            f"first kill on the lane opponent ({lane.get('opponent')})",
        )
    return items


def _report_text(report: CoachReport) -> str:
    parts: list[str] = [report.headline, report.match_read, report.kda_context]
    parts.extend(report.game_timeline)
    parts.extend(report.strengths)
    parts.extend(report.mistakes)
    for area in report.focus_areas:
        parts.extend([area.title, area.why_it_matters, area.how_to_practice])
    parts.extend(report.next_three_games)
    return " ".join(part for part in parts if part)


def _mentions(text: str, time: str) -> bool:
    return re.search(rf"(?<![\d:]){re.escape(time)}(?![\d:])", text) is not None


def missing_moments(
    report: CoachReport, checklist: list[dict[str, str]]
) -> list[dict[str, str]]:
    text = _report_text(report)
    return [item for item in checklist if not _mentions(text, item["time"])]


def repair_instruction(missing: list[dict[str, str]]) -> str:
    listed = "; ".join(
        f"{item['time']} ({item['moment']})" for item in missing[:MAX_REPAIR_ITEMS]
    )
    return (
        "The report skipped moments that must be covered. Revise it so each of "
        f"these appears with its timestamp and its consequence: {listed}. Keep "
        "everything that is already correct. Return the full corrected report."
    )
