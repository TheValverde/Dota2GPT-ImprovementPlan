from __future__ import annotations

from typing import Any

from dota2_coach.opendota.labels import format_duration, is_radiant_slot

PHASE_BOUNDS = (
    ("laning", 0, 600),
    ("midgame", 600, 1500),
    ("closing", 1500, None),
)

PHASES_NOTE = (
    "phases: laning, midgame, and closing summaries. Use them as the spine so "
    "the recap never skips a stretch of the game."
)


def _focus_team(focus: dict[str, Any]) -> str | None:
    radiant = is_radiant_slot(focus.get("player_slot"), focus.get("isRadiant"))
    if radiant is None:
        return None
    return "Radiant" if radiant else "Dire"


def build_phases(
    match: dict[str, Any], ledger: list[dict[str, Any]], focus: dict[str, Any]
) -> list[dict[str, Any]]:
    team = _focus_team(focus)
    adv = match.get("radiant_gold_adv") or []
    duration = match.get("duration")
    rows: list[dict[str, Any]] = []
    for name, start, end in PHASE_BOUNDS:
        if isinstance(duration, int) and start > duration:
            continue
        stop = end if end is not None else (duration if isinstance(duration, int) else None)
        limit = float("inf") if end is None else end
        span_rows = [r for r in ledger if start <= r.get("t", 0) < limit]
        kills = [r for r in span_rows if r.get("event") == "hero_kill"]
        buildings = [r for r in span_rows if r.get("event") == "building"]
        entry: dict[str, Any] = {
            "phase": name,
            "window": f"{format_duration(start)}-{format_duration(stop) if stop is not None else 'end'}",
        }
        if team:
            entry["team_kills"] = sum(1 for k in kills if k.get("by_team") == team)
            entry["enemy_kills"] = sum(
                1 for k in kills if k.get("by_team") and k.get("by_team") != team
            )
            entry["towers_lost"] = sum(1 for b in buildings if b.get("lost_by") == team)
            entry["towers_taken"] = sum(
                1 for b in buildings if b.get("lost_by") and b.get("lost_by") != team
            )
        entry["focus_kills"] = sum(1 for k in kills if k.get("by_focus"))
        entry["focus_deaths"] = sum(1 for k in kills if k.get("victim_is_focus"))
        items = [r.get("item") for r in span_rows if r.get("event") == "item"]
        if items:
            entry["focus_items"] = items
        if isinstance(adv, list) and adv and team:
            minute = stop // 60 if stop is not None else len(adv) - 1
            minute = max(0, min(minute, len(adv) - 1))
            try:
                lead = int(adv[minute])
            except (TypeError, ValueError):
                lead = None
            if lead is not None:
                entry["gold_lead_at_end"] = lead if team == "Radiant" else -lead
        rows.append(entry)
    return rows
