from __future__ import annotations

from typing import Any


def npc_hero_label(key: Any) -> str | None:
    if not isinstance(key, str) or not key:
        return None
    if key.startswith("npc_dota_hero_"):
        return key.removeprefix("npc_dota_hero_").replace("_", " ").title()
    return key.replace("_", " ")


def kill_key_matches(key: Any, player: dict, constants) -> bool:
    if not isinstance(key, str) or not key:
        return False
    hero_id = player.get("hero_id")
    npc = constants.hero_npc(hero_id) if hasattr(constants, "hero_npc") else None
    if npc and key == npc:
        return True
    label = npc_hero_label(key)
    hero = constants.hero_name(hero_id) if hero_id is not None else None
    if label and hero and label.lower() == hero.lower():
        return True
    if npc and label and npc_hero_label(npc) and label.lower() == npc_hero_label(npc).lower():
        return True
    return False


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
