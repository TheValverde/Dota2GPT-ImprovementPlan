from __future__ import annotations

from typing import Any

from dota2_coach.opendota.labels import format_duration, is_radiant_slot

OBJECTIVE_WINDOW_BEFORE = 90
OBJECTIVE_WINDOW_AFTER = 20

WINDOWS_NOTE = (
    "objective_windows: every tower and Roshan with the kills around it. "
    "lost_by_focus_team plus focus_was_fighting_elsewhere means the objective "
    "was the price of a fight somewhere else; call it a trade and say if it was "
    "worth it. death_windows: every focus death with the killer, the fight it "
    "happened in, the enemy gold swing over the next two minutes, and the item "
    "it delayed. Every focus death must appear in the report with its cost. "
    "gold_swings: each swing needs an explanation tied to events on the clock."
)


def _focus_team(focus: dict[str, Any]) -> str | None:
    radiant = is_radiant_slot(focus.get("player_slot"), focus.get("isRadiant"))
    if radiant is None:
        return None
    return "Radiant" if radiant else "Dire"


def build_objective_windows(
    ledger: list[dict[str, Any]], focus: dict[str, Any]
) -> list[dict[str, Any]]:
    team = _focus_team(focus)
    kills = [row for row in ledger if row.get("event") == "hero_kill"]
    rows: list[dict[str, Any]] = []
    for row in ledger:
        if row.get("event") not in {"building", "roshan"}:
            continue
        t = row.get("t")
        if t is None:
            continue
        near = [
            k
            for k in kills
            if t - OBJECTIVE_WINDOW_BEFORE <= k.get("t", 0) <= t + OBJECTIVE_WINDOW_AFTER
        ]
        entry: dict[str, Any] = {
            "time": row.get("time"),
            "objective": row.get("building") or "Roshan",
        }
        if row.get("by"):
            entry["taken_by"] = row["by"]
        lost = row.get("lost_by")
        if lost:
            entry["lost_by"] = lost
            if team and lost == team:
                entry["lost_by_focus_team"] = True
        if near:
            entry["kills_around"] = [
                {"time": k.get("time"), "by": k.get("by"), "victim": k.get("victim")}
                for k in near[:6]
            ]
            focus_active = any(
                k.get("by_focus") or k.get("victim_is_focus") for k in near
            )
            if focus_active:
                entry["focus_in_action"] = True
                if entry.get("lost_by_focus_team") and not row.get("by_focus"):
                    entry["focus_was_fighting_elsewhere"] = True
        rows.append(entry)
    return rows


def build_death_windows(
    match: dict[str, Any], ledger: list[dict[str, Any]], focus: dict[str, Any]
) -> list[dict[str, Any]]:
    team = _focus_team(focus)
    adv = match.get("radiant_gold_adv") or []
    fights = match.get("teamfights") or []
    deaths = [
        row
        for row in ledger
        if row.get("event") == "hero_kill" and row.get("victim_is_focus")
    ]
    buildings = [
        row
        for row in ledger
        if row.get("event") == "building" and team and row.get("lost_by") == team
    ]
    items = [row for row in ledger if row.get("event") == "item"]
    rows: list[dict[str, Any]] = []
    for death in deaths:
        t = death.get("t")
        if t is None:
            continue
        row: dict[str, Any] = {"time": death.get("time"), "killed_by": death.get("by")}
        minute = t // 60
        if isinstance(adv, list) and 0 <= minute < len(adv):
            later = min(minute + 2, len(adv) - 1)
            try:
                delta = int(adv[later]) - int(adv[minute])
            except (TypeError, ValueError):
                delta = None
            if delta is not None and team:
                row["enemy_gold_swing_next_2_min"] = delta if team == "Dire" else -delta
        for fight in fights:
            start = fight.get("start")
            end = fight.get("end")
            if isinstance(start, int) and isinstance(end, int) and start - 5 <= t <= end + 5:
                row["in_teamfight_at"] = format_duration(start)
                break
        lost = [b for b in buildings if t < b.get("t", 0) <= t + 150]
        if lost:
            row["objectives_lost_within_2_min"] = [
                {"time": b.get("time"), "building": b.get("building")} for b in lost[:3]
            ]
        nxt = next((i for i in items if i.get("t", 0) > t), None)
        if nxt:
            row["next_item_after"] = {"item": nxt.get("item"), "time": nxt.get("time")}
        rows.append(row)
    return rows


def build_gold_swings(
    match: dict[str, Any],
    focus: dict[str, Any],
    threshold: int = 3000,
    span: int = 2,
) -> list[dict[str, Any]]:
    adv = match.get("radiant_gold_adv") or []
    if not isinstance(adv, list) or len(adv) <= span:
        return []
    team = _focus_team(focus)
    rows: list[dict[str, Any]] = []
    i = 0
    while i + span < len(adv):
        try:
            delta = int(adv[i + span]) - int(adv[i])
        except (TypeError, ValueError):
            i += 1
            continue
        if abs(delta) >= threshold:
            toward = "Radiant" if delta > 0 else "Dire"
            row: dict[str, Any] = {
                "time": format_duration(i * 60),
                "through": format_duration((i + span) * 60),
                "swing": abs(delta),
                "toward": toward,
            }
            if team:
                row["toward_focus_team"] = toward == team
            rows.append(row)
            i += span
        else:
            i += 1
    return rows
