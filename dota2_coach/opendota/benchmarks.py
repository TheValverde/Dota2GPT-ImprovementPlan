from __future__ import annotations

from typing import Any

BENCHMARK_STATS = (
    "gold_per_min",
    "xp_per_min",
    "kills_per_min",
    "deaths_per_min",
    "assists_per_min",
    "last_hits_per_min",
    "hero_damage_per_min",
    "tower_damage",
)


def _pct_display(fraction: float) -> int:
    return int(round(max(0.0, min(1.0, fraction)) * 100))


def extract_match_benchmarks(player: dict[str, Any]) -> dict[str, dict[str, float | int]]:
    raw_block = player.get("benchmarks")
    if not isinstance(raw_block, dict):
        return {}
    cleaned: dict[str, dict[str, float | int]] = {}
    for key, entry in raw_block.items():
        if not isinstance(entry, dict):
            continue
        raw = entry.get("raw")
        pct = entry.get("pct")
        if raw is None or pct is None:
            continue
        try:
            cleaned[key] = {
                "raw": round(float(raw), 2),
                "percentile": _pct_display(float(pct)),
            }
        except (TypeError, ValueError):
            continue
    return cleaned


def interpolate_percentile(curve: list[dict[str, Any]], raw: float) -> int | None:
    points: list[tuple[float, float]] = []
    for row in curve:
        try:
            points.append((float(row["value"]), float(row["percentile"])))
        except (KeyError, TypeError, ValueError):
            continue
    if not points:
        return None
    points.sort(key=lambda item: item[0])
    if raw <= points[0][0]:
        return _pct_display(points[0][1])
    if raw >= points[-1][0]:
        return _pct_display(points[-1][1])
    for index in range(1, len(points)):
        value_left, pct_left = points[index - 1]
        value_right, pct_right = points[index]
        if raw > value_right:
            continue
        if value_right == value_left:
            return _pct_display(pct_right)
        weight = (raw - value_left) / (value_right - value_left)
        return _pct_display(pct_left + weight * (pct_right - pct_left))
    return _pct_display(points[-1][1])


def _per_min(value: Any, duration_seconds: int | None) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if duration_seconds and duration_seconds > 0:
        return number / (duration_seconds / 60)
    return number


def benchmarks_from_hero_curve(
    player: dict[str, Any],
    curve_payload: dict[str, Any],
    duration_seconds: int | None,
) -> dict[str, dict[str, float | int]]:
    result = curve_payload.get("result") if isinstance(curve_payload, dict) else None
    if not isinstance(result, dict):
        return {}
    duration = duration_seconds or player.get("duration")
    raw_values = {
        "gold_per_min": player.get("gold_per_min"),
        "xp_per_min": player.get("xp_per_min"),
        "kills_per_min": _per_min(player.get("kills"), duration),
        "deaths_per_min": _per_min(player.get("deaths"), duration),
        "assists_per_min": _per_min(player.get("assists"), duration),
        "last_hits_per_min": _per_min(player.get("last_hits"), duration),
        "hero_damage_per_min": _per_min(player.get("hero_damage"), duration),
        "tower_damage": player.get("tower_damage"),
    }
    cleaned: dict[str, dict[str, float | int]] = {}
    for key, raw in raw_values.items():
        if raw is None:
            continue
        curve = result.get(key)
        if not isinstance(curve, list):
            continue
        percentile = interpolate_percentile(curve, float(raw))
        if percentile is None:
            continue
        cleaned[key] = {"raw": round(float(raw), 2), "percentile": percentile}
    return cleaned
