from __future__ import annotations

from typing import Any


def npc_hero_label(key: Any) -> str | None:
    if not isinstance(key, str) or not key:
        return None
    if key.startswith("npc_dota_hero_"):
        return key.removeprefix("npc_dota_hero_").replace("_", " ").title()
    return key.replace("_", " ")


def named_counts(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    named: dict[str, int] = {}
    for key, value in raw.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count <= 0:
            continue
        label = npc_hero_label(key) or str(key)
        named[label] = count
    return named


def named_ability_targets(raw: Any) -> dict[str, dict[str, int]]:
    if not isinstance(raw, dict):
        return {}
    named: dict[str, dict[str, int]] = {}
    for ability, targets in raw.items():
        counts = named_counts(targets)
        if counts:
            named[str(ability)] = counts
    return named
