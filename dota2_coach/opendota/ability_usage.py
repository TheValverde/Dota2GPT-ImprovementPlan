from __future__ import annotations

from typing import Any

from dota2_coach.opendota.abilities import npc_hero_label
from dota2_coach.opendota.labels import format_duration, is_radiant_slot

ABILITY_USAGE_NOTE = (
    "ability_usage lists every focus spell with targets split ally, enemy, and "
    "self. Ally casts on hard disables like Nightmare are save attempts. "
    "manual_ends counts deliberate wake-ups (Nightmare End). teamfights rows "
    "show per-fight cast counts; cross with macro.teamfights for who died."
)


def _ability_label(key: str) -> str:
    label = key.replace("_", " ").title()
    for prefix in ("Bane ", "Pugna ", "Undying ", "Queenofpain ", "Medusa "):
        if label.startswith(prefix):
            return label[len(prefix) :]
    return label


def _hero_npc_map(players: list[dict[str, Any]], constants) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for player in players:
        hero_id = player.get("hero_id")
        npc = constants.hero_npc(hero_id) if hero_id is not None else None
        if npc:
            mapping[npc] = player
        label = npc_hero_label(npc) if npc else None
        if label:
            mapping[label.lower()] = player
        hero = constants.hero_name(hero_id) if hero_id is not None else None
        if hero:
            mapping[hero.lower()] = player
    return mapping


def _target_side(
    target_key: str,
    focus: dict[str, Any],
    hero_lookup: dict[str, dict[str, Any]],
) -> str:
    player = hero_lookup.get(target_key) or hero_lookup.get(target_key.lower())
    if player is None:
        label = npc_hero_label(target_key)
        if label:
            player = hero_lookup.get(label.lower())
    if player is None:
        return "unknown"
    if player is focus:
        return "self"
    focus_team = is_radiant_slot(focus.get("player_slot"), focus.get("isRadiant"))
    target_team = is_radiant_slot(player.get("player_slot"), player.get("isRadiant"))
    if focus_team is None or target_team is None:
        return "unknown"
    return "ally" if focus_team == target_team else "enemy"


def _target_rows(
    targets: dict[str, int],
    focus: dict[str, Any],
    hero_lookup: dict[str, dict[str, Any]],
    constants,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        "ally": [],
        "enemy": [],
        "self": [],
        "unknown": [],
    }
    for key, count in sorted(targets.items(), key=lambda item: (-item[1], item[0])):
        try:
            casts = int(count)
        except (TypeError, ValueError):
            continue
        if casts <= 0:
            continue
        side = _target_side(str(key), focus, hero_lookup)
        player = hero_lookup.get(str(key)) or hero_lookup.get(str(key).lower())
        if player is None:
            label = npc_hero_label(key)
            if label:
                player = hero_lookup.get(label.lower())
        if player:
            hero = constants.hero_name(player.get("hero_id")) or npc_hero_label(key)
        else:
            hero = npc_hero_label(key) or str(key)
        grouped[side].append({"hero": hero, "count": casts})
    return {key: value for key, value in grouped.items() if value}


def _summarize_abilities(
    focus: dict[str, Any],
    players: list[dict[str, Any]],
    constants,
) -> list[dict[str, Any]]:
    uses = focus.get("ability_uses") or {}
    raw_targets = focus.get("ability_targets") or {}
    if not isinstance(uses, dict) and not isinstance(raw_targets, dict):
        return []
    hero_lookup = _hero_npc_map(players, constants)
    ability_keys = set(uses.keys()) | set(raw_targets.keys())
    rows: list[dict[str, Any]] = []
    for key in sorted(ability_keys):
        if not isinstance(key, str) or key.endswith("_end"):
            continue
        try:
            casts = int(uses.get(key) or 0)
        except (TypeError, ValueError):
            casts = 0
        targets_raw = raw_targets.get(key) if isinstance(raw_targets, dict) else None
        target_counts: dict[str, int] = {}
        if isinstance(targets_raw, dict):
            for target_key, value in targets_raw.items():
                try:
                    count = int(value)
                except (TypeError, ValueError):
                    continue
                if count > 0:
                    target_counts[str(target_key)] = count
        if casts <= 0 and not target_counts:
            continue
        row: dict[str, Any] = {
            "ability": _ability_label(key),
            "ability_key": key,
            "casts": casts or sum(target_counts.values()),
        }
        end_key = f"{key}_end"
        if end_key in uses:
            try:
                manual_ends = int(uses[end_key])
            except (TypeError, ValueError):
                manual_ends = 0
            if manual_ends:
                row["manual_ends"] = manual_ends
        if target_counts:
            row["targets"] = _target_rows(target_counts, focus, hero_lookup, constants)
        rows.append(row)
    return rows


def _fight_ability_casts(focus_row: dict[str, Any]) -> dict[str, int]:
    uses = focus_row.get("ability_uses") or {}
    if not isinstance(uses, dict):
        return {}
    casts: dict[str, int] = {}
    for key, value in uses.items():
        if not isinstance(key, str) or key.endswith("_end"):
            continue
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count <= 0:
            continue
        label = _ability_label(key)
        casts[label] = casts.get(label, 0) + count
    return casts


def _teamfight_rows(
    match: dict[str, Any],
    constants,
    focus: dict[str, Any],
    players: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    focus_index = next(
        (index for index, player in enumerate(players) if player is focus),
        None,
    )
    if focus_index is None:
        return []
    rows: list[dict[str, Any]] = []
    for fight in match.get("teamfights") or []:
        if not isinstance(fight, dict):
            continue
        entries = fight.get("players") or []
        if focus_index >= len(entries) or not isinstance(entries[focus_index], dict):
            continue
        focus_row = entries[focus_index]
        ability_casts = _fight_ability_casts(focus_row)
        if not ability_casts:
            continue
        died: list[str] = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or not entry.get("deaths"):
                continue
            if index < len(players):
                hero = constants.hero_name(players[index].get("hero_id")) or "Unknown"
                died.append(hero)
        row: dict[str, Any] = {
            "time": format_duration(fight.get("start")),
            "focus_died": bool(focus_row.get("deaths")),
            "ability_casts": ability_casts,
        }
        if died:
            row["died"] = died
        if focus_row.get("damage") is not None:
            row["focus_damage"] = focus_row.get("damage")
        rows.append(row)
    return rows


def build_ability_usage(
    match: dict[str, Any],
    constants,
    focus: dict[str, Any],
) -> dict[str, Any] | None:
    players = [player for player in match.get("players") or [] if isinstance(player, dict)]
    abilities = _summarize_abilities(focus, players, constants)
    teamfights = _teamfight_rows(match, constants, focus, players)
    if not abilities and not teamfights:
        return None
    payload: dict[str, Any] = {}
    if abilities:
        payload["abilities"] = abilities
    if teamfights:
        payload["teamfights"] = teamfights
    return payload
