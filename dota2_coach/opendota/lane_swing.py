from __future__ import annotations

from typing import Any

from dota2_coach.opendota.abilities import kill_key_matches, npc_hero_label
from dota2_coach.opendota.labels import format_duration
from dota2_coach.opendota.lanes import lane_opponents

LANE_SWING_NOTE = (
    "Early kills on the lane opponent are a swing, not a score. After those "
    "deaths, say what the gold and XP lead was, what the opponent delayed "
    "(bottle, boots, first item), and who could leave the lane first. If last "
    "hits equalize later, they farmed an empty wave. If they take a T1 while "
    "the focus player is on a side fight, that tower is the tax for leaving, "
    "not the opponent winning the lane. Follow them for the rest of the game: "
    "first kill time and items say whether they ever became a hero."
)

_SKIP_ITEMS = {
    "tango",
    "flask",
    "clarity",
    "faerie fire",
    "enchanted mango",
    "branches",
    "tpscroll",
    "ward observer",
    "ward sentry",
    "ward dispenser",
    "dust",
    "smoke of deceit",
    "tome of knowledge",
    "circlet",
    "slippers",
    "gauntlets",
    "mantle",
    "quelling blade",
}


def _series_at(series: Any, minute: int) -> int | None:
    if not isinstance(series, list) or minute < 0 or minute >= len(series):
        return None
    try:
        return int(series[minute])
    except (TypeError, ValueError):
        return None


def _core_opponent(focus: dict[str, Any], players: list[dict[str, Any]]) -> dict[str, Any] | None:
    opponents = lane_opponents(focus, players)
    if not opponents:
        return None

    def farm(player: dict[str, Any]) -> float:
        try:
            return float(player.get("last_hits") or 0) + float(player.get("gold_per_min") or 0) / 100
        except (TypeError, ValueError):
            return 0.0

    return max(opponents, key=farm)


def _kills_on(
    focus: dict[str, Any],
    opponent: dict[str, Any],
    constants,
    until: int | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in focus.get("kills_log") or []:
        if not isinstance(entry, dict):
            continue
        if not kill_key_matches(entry.get("key"), opponent, constants):
            continue
        try:
            seconds = int(entry.get("time"))
        except (TypeError, ValueError):
            continue
        if until is not None and seconds > until:
            continue
        rows.append(
            {
                "time": format_duration(seconds),
                "hero": constants.hero_name(opponent.get("hero_id"))
                or npc_hero_label(entry.get("key"))
                or "unknown",
            }
        )
    return rows


def _first_kill(player: dict[str, Any]) -> str | None:
    log = player.get("kills_log")
    if not isinstance(log, list) or not log:
        return None
    first = log[0]
    if not isinstance(first, dict):
        return None
    return format_duration(first.get("time"))


def _item_times(player: dict[str, Any], limit: int = 10) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for entry in player.get("purchase_log") or []:
        if not isinstance(entry, dict):
            continue
        raw = str(entry.get("key") or "").replace("_", " ")
        if not raw or raw in _SKIP_ITEMS or raw.startswith("recipe "):
            continue
        time = format_duration(entry.get("time"))
        if not time:
            continue
        rows.append({"item": raw, "time": time})
        if len(rows) >= limit:
            break
    return rows


def _snapshot(focus: dict[str, Any], opponent: dict[str, Any], minute: int) -> dict[str, Any] | None:
    focus_gold = _series_at(focus.get("gold_t"), minute)
    opp_gold = _series_at(opponent.get("gold_t"), minute)
    focus_xp = _series_at(focus.get("xp_t"), minute)
    opp_xp = _series_at(opponent.get("xp_t"), minute)
    if focus_gold is None or opp_gold is None:
        return None
    row: dict[str, Any] = {
        "time": format_duration(minute * 60),
        "focus_gold": focus_gold,
        "opponent_gold": opp_gold,
        "gold_lead": focus_gold - opp_gold,
        "focus_lh": _series_at(focus.get("lh_t"), minute),
        "opponent_lh": _series_at(opponent.get("lh_t"), minute),
    }
    if focus_xp is not None and opp_xp is not None:
        row["focus_xp"] = focus_xp
        row["opponent_xp"] = opp_xp
        row["xp_lead"] = focus_xp - opp_xp
    return row


def build_lane_swing(
    match: dict[str, Any],
    constants,
    focus: dict[str, Any],
) -> dict[str, Any] | None:
    players = [p for p in match.get("players") or [] if isinstance(p, dict)]
    opponent = _core_opponent(focus, players)
    if opponent is None:
        return None
    snapshots = []
    for minute in (3, 6, 10, 15):
        row = _snapshot(focus, opponent, minute)
        if row:
            snapshots.append(row)
    kills = _kills_on(focus, opponent, constants)
    early_kills = _kills_on(focus, opponent, constants, until=8 * 60)
    payload: dict[str, Any] = {
        "opponent": constants.hero_name(opponent.get("hero_id")) or "Unknown",
        "note": LANE_SWING_NOTE,
    }
    if early_kills:
        payload["early_kills_on_opponent"] = early_kills
    if kills:
        payload["kills_on_opponent"] = [row["time"] for row in kills]
        payload["kills_on_opponent_count"] = len(kills)
    if snapshots:
        payload["snapshots"] = snapshots
    first_kill = _first_kill(opponent)
    if first_kill:
        payload["opponent_first_kill"] = first_kill
    else:
        payload["opponent_never_killed"] = True
    items = _item_times(opponent)
    if items:
        payload["opponent_items"] = items
    deaths = opponent.get("deaths")
    if deaths is not None:
        payload["opponent_deaths"] = deaths
    return payload
