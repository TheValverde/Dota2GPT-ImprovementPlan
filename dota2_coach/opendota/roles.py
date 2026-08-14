from __future__ import annotations

from typing import Any


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _farm_score(player: dict[str, Any]) -> float:
    gpm = _num(player.get("gold_per_min"))
    last_hits = _num(player.get("last_hits"))
    return gpm * 2 + last_hits


def _looks_support(player: dict[str, Any]) -> bool:
    obs = _num(player.get("obs_placed"))
    if not obs:
        obs = _num(player.get("observer_wards_placed"))
    if not obs:
        obs = _num(player.get("observers_placed"))
    gpm = _num(player.get("gold_per_min"))
    last_hits = _num(player.get("last_hits"))
    return obs >= 6 or (gpm and gpm < 380) or (last_hits and last_hits < 90)


def infer_assignment(
    player: dict[str, Any],
    teammates: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    """Infer a lane assignment from OpenDota fields, not Valve role queue."""
    if player.get("is_roaming"):
        return {
            "label": "Roam",
            "basis": "OpenDota is_roaming flag",
        }

    lane_role = player.get("lane_role")
    if lane_role == 2:
        return {"label": "Mid", "basis": "lane_role 2"}
    if lane_role == 4:
        return {"label": "Jungle", "basis": "lane_role 4"}

    partners = [
        other
        for other in teammates or []
        if other is not player
        and other.get("lane_role") == lane_role
        and other.get("lane_role") is not None
    ]
    farm = _farm_score(player)

    if lane_role == 1:
        if partners:
            best_other = max(_farm_score(other) for other in partners)
            if farm >= best_other:
                return {
                    "label": "Safe core",
                    "basis": "safe lane with more farm than the lane partner",
                }
            return {
                "label": "Safe support",
                "basis": "safe lane with less farm than the lane partner",
            }
        if _looks_support(player):
            return {
                "label": "Safe support",
                "basis": "safe lane plus wards or low farm",
            }
        return {"label": "Safe core", "basis": "safe lane plus farm"}

    if lane_role == 3:
        if partners:
            best_other = max(_farm_score(other) for other in partners)
            if farm >= best_other:
                return {
                    "label": "Offlane",
                    "basis": "off lane with more farm than the lane partner",
                }
            return {
                "label": "Off support",
                "basis": "off lane with less farm than the lane partner",
            }
        if _looks_support(player):
            return {
                "label": "Off support",
                "basis": "off lane plus wards or low farm",
            }
        return {"label": "Offlane", "basis": "off lane plus farm"}

    return {
        "label": "Unknown",
        "basis": "OpenDota did not provide lane_role",
    }
