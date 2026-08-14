from __future__ import annotations

from typing import Any

from dota2_coach.opendota.abilities import npc_hero_label
from dota2_coach.opendota.labels import format_duration

OPENING_UNTIL_SECONDS = 8 * 60

OPENING_NOTE = (
    "Read these rows in clock order. If the focus player's observer sits before "
    "their courier kills, and those sit before kills on the lane opponents, that "
    "is one play: the ward is how the courier was seen, the dead couriers are why "
    "the lane then dies (no regen, delayed items), then the heroes die. "
    "Do not split the observer, the courier snipes, and the hero kills into three "
    "unrelated facts."
)


def _hero_label(player: dict[str, Any], constants) -> str:
    return constants.hero_name(player.get("hero_id")) or "Unknown"


def _player_by_slot(players: list[dict[str, Any]], slot: Any) -> dict[str, Any] | None:
    try:
        slot_id = int(slot)
    except (TypeError, ValueError):
        return None
    for player in players:
        if player.get("player_slot") == slot_id:
            return player
    return None


def _team_name(team: Any) -> str | None:
    try:
        team_id = int(team)
    except (TypeError, ValueError):
        return None
    if team_id == 2:
        return "Radiant"
    if team_id == 3:
        return "Dire"
    return None


def _seconds(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _in_window(seconds: int, until: int) -> bool:
    return seconds <= until


def _lane_hero_names(
    players: list[dict[str, Any]], constants, lane: Any
) -> set[str]:
    names: set[str] = set()
    if lane is None:
        return names
    for player in players:
        if player.get("lane") != lane:
            continue
        label = _hero_label(player, constants)
        names.add(label)
        names.add(label.lower())
    return names


def _same_lane(player: dict[str, Any], lane: Any) -> bool:
    return lane is not None and player.get("lane") == lane


def _tower_matches_lane(building: str | None, lane: Any) -> bool:
    if lane is None or not building:
        return True
    key = building.replace(" ", "_")
    if lane == 1:
        return "_bot" in key
    if lane == 2:
        return "_mid" in key
    if lane == 3:
        return "_top" in key
    return True


def build_opening_sequence(
    match: dict[str, Any],
    constants,
    focus: dict[str, Any],
    until_seconds: int = OPENING_UNTIL_SECONDS,
) -> list[dict[str, Any]]:
    players = [p for p in match.get("players") or [] if isinstance(p, dict)]
    focus_slot = focus.get("player_slot")
    focus_lane = focus.get("lane")
    lane_heroes = _lane_hero_names(players, constants, focus_lane)
    events: list[tuple[int, dict[str, Any]]] = []

    for kind, log in (
        ("observer", focus.get("obs_log")),
        ("sentry", focus.get("sen_log")),
    ):
        if not isinstance(log, list):
            continue
        for entry in log:
            if not isinstance(entry, dict):
                continue
            time = _seconds(entry.get("time"))
            if time is None or not _in_window(time, until_seconds):
                continue
            events.append(
                (
                    time,
                    {
                        "time": format_duration(time),
                        "event": kind,
                        "by": _hero_label(focus, constants),
                        "by_focus": True,
                    },
                )
            )

    for event in match.get("objectives") or []:
        if not isinstance(event, dict):
            continue
        time = _seconds(event.get("time"))
        if time is None or not _in_window(time, until_seconds):
            continue
        kind = str(event.get("type") or "")
        if kind == "CHAT_MESSAGE_COURIER_LOST":
            killer = _player_by_slot(players, event.get("killer"))
            row: dict[str, Any] = {
                "time": format_duration(time),
                "event": "courier_kill",
            }
            courier_team = _team_name(event.get("team"))
            if courier_team:
                row["courier_team"] = courier_team
            if killer is not None:
                row["by"] = _hero_label(killer, constants)
                row["by_focus"] = killer is focus or killer.get("player_slot") == focus_slot
            events.append((time, row))
        elif kind == "building_kill":
            key = event.get("key")
            row = {
                "time": format_duration(time),
                "event": "tower",
            }
            if isinstance(key, str) and key.startswith("npc_dota_"):
                row["building"] = key.replace("npc_dota_", "").replace("_", " ")
            if not _tower_matches_lane(row.get("building"), focus_lane):
                continue
            actor = _player_by_slot(players, event.get("player_slot"))
            if actor is None:
                actor = _player_by_slot(players, event.get("killer"))
            if actor is not None:
                row["by"] = _hero_label(actor, constants)
                row["by_focus"] = actor is focus or actor.get("player_slot") == focus_slot
            events.append((time, row))

    for player in players:
        kills = player.get("kills_log")
        if not isinstance(kills, list):
            continue
        is_focus = player is focus or player.get("player_slot") == focus_slot
        killer_in_lane = is_focus or _same_lane(player, focus_lane)
        for entry in kills:
            if not isinstance(entry, dict):
                continue
            time = _seconds(entry.get("time"))
            if time is None or not _in_window(time, until_seconds):
                continue
            victim = npc_hero_label(entry.get("key")) or "unknown"
            victim_in_lane = victim in lane_heroes or victim.lower() in lane_heroes
            if focus_lane is not None and not killer_in_lane and not victim_in_lane:
                continue
            events.append(
                (
                    time,
                    {
                        "time": format_duration(time),
                        "event": "hero_kill",
                        "by": _hero_label(player, constants),
                        "victim": victim,
                        "by_focus": is_focus,
                    },
                )
            )

    events.sort(key=lambda item: item[0])
    return [row for _, row in events]
