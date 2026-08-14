from __future__ import annotations

from typing import Any, Callable

from dota2_coach.opendota.labels import is_radiant_slot, lane_label

# OpenDota `lane` is the map side. 1 bottom, 2 middle, 3 top.
# `lane_role` is Safe/Mid/Off for that player's team, so Dire safe and Radiant
# safe are opposite sides of the map.
PHYSICAL_LANES = {
    1: "Bottom",
    2: "Middle",
    3: "Top",
}

LANE_MATCHUP_NOTE = (
    "Safelane lanes against the enemy offlane. Offlane lanes against the enemy "
    "safelane. Mid lanes against mid. OpenDota lane_role is Safe/Mid/Off, not "
    "the map side: the same lane_role on the other team is the opposite lane. "
    "Parsed matches also set lane (1 bottom, 2 mid, 3 top) for the physical side."
)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def opposing_lane_role(lane_role: int | None) -> int | None:
    role = _as_int(lane_role)
    if role == 1:
        return 3
    if role == 3:
        return 1
    if role == 2:
        return 2
    return None


def physical_lane_label(lane: int | None) -> str | None:
    lane_id = _as_int(lane)
    if lane_id is None:
        return None
    return PHYSICAL_LANES.get(lane_id)


def _team(player: dict[str, Any]) -> bool | None:
    return is_radiant_slot(player.get("player_slot"), player.get("isRadiant"))


def _split_lobby(
    player: dict[str, Any], others: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    team = _team(player)
    allies: list[dict[str, Any]] = []
    enemies: list[dict[str, Any]] = []
    if team is None:
        return allies, enemies
    for other in others:
        if other is player:
            continue
        other_team = _team(other)
        if other_team is None:
            continue
        if other_team == team:
            allies.append(other)
        else:
            enemies.append(other)
    return allies, enemies


def _match_physical(anchor: dict[str, Any], pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lane_id = _as_int(anchor.get("lane"))
    if lane_id not in PHYSICAL_LANES:
        return []
    matched: list[dict[str, Any]] = []
    for other in pool:
        if _as_int(other.get("lane")) == lane_id:
            matched.append(other)
    return matched


def _match_role(
    pool: list[dict[str, Any]], lane_role: int | None
) -> list[dict[str, Any]]:
    role = _as_int(lane_role)
    if role is None:
        return []
    return [other for other in pool if _as_int(other.get("lane_role")) == role]


def lane_opponents(
    player: dict[str, Any], others: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    _, enemies = _split_lobby(player, others)
    physical = _match_physical(player, enemies)
    if physical:
        return physical
    return _match_role(enemies, opposing_lane_role(player.get("lane_role")))


def lane_partners(
    player: dict[str, Any], others: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    allies, _ = _split_lobby(player, others)
    physical = _match_physical(player, allies)
    if physical:
        return physical
    return _match_role(allies, player.get("lane_role"))


def _short_player(
    player: dict[str, Any], hero_name: Callable[[int | None], str | None]
) -> dict[str, str]:
    row: dict[str, str] = {}
    name = player.get("personaname")
    if name:
        row["name"] = str(name)
    hero = hero_name(player.get("hero_id"))
    if hero:
        row["hero"] = hero
    role = lane_label(player.get("lane_role"))
    if role:
        row["lane_role"] = role
    return row


def describe_lane_matchup(
    player: dict[str, Any],
    others: list[dict[str, Any]],
    hero_name: Callable[[int | None], str | None],
) -> dict[str, Any]:
    payload: dict[str, Any] = {"lane_matchup_note": LANE_MATCHUP_NOTE}
    map_lane = physical_lane_label(player.get("lane"))
    if map_lane:
        payload["map_lane"] = map_lane
    with_heroes = [
        _short_player(other, hero_name) for other in lane_partners(player, others)
    ]
    against = [
        _short_player(other, hero_name) for other in lane_opponents(player, others)
    ]
    if with_heroes:
        payload["laned_with"] = with_heroes
    if against:
        payload["laned_against"] = against
    return payload
