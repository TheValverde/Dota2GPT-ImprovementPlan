from __future__ import annotations

from collections import Counter
from typing import Any

FORM_NOTE = (
    "recent_form is the player's last games before this one. Use it for habits: "
    "a leak that repeats across games matters more than a one-off. Do not "
    "re-coach those games, just connect repeated patterns."
)


def _won(row: dict[str, Any]) -> bool | None:
    radiant_win = row.get("radiant_win")
    slot = row.get("player_slot")
    if radiant_win is None or slot is None:
        return None
    return bool(radiant_win) == (slot < 128)


def build_recent_form(
    rows: list[dict[str, Any]],
    constants,
    exclude_match_id: int | None = None,
    limit: int = 10,
) -> dict[str, Any] | None:
    usable = [row for row in rows if isinstance(row, dict)]
    usable.sort(key=lambda row: row.get("start_time") or 0, reverse=True)
    matches: list[dict[str, Any]] = []
    heroes: Counter[str] = Counter()
    wins = 0
    deaths_total = 0
    for row in usable:
        if exclude_match_id is not None and row.get("match_id") == exclude_match_id:
            continue
        hero = constants.hero_name(row.get("hero_id")) or "Unknown"
        won = _won(row)
        entry: dict[str, Any] = {
            "hero": hero,
            "kda": f"{row.get('kills', 0)}/{row.get('deaths', 0)}/{row.get('assists', 0)}",
        }
        if won is not None:
            entry["won"] = won
            if won:
                wins += 1
        matches.append(entry)
        heroes[hero] += 1
        try:
            deaths_total += int(row.get("deaths") or 0)
        except (TypeError, ValueError):
            pass
        if len(matches) >= limit:
            break
    if not matches:
        return None
    payload: dict[str, Any] = {
        "matches": matches,
        "games": len(matches),
        "wins": wins,
        "avg_deaths": round(deaths_total / len(matches), 1),
    }
    hero, count = heroes.most_common(1)[0]
    if count >= 3:
        payload["most_played"] = f"{hero} x{count}"
    return payload
