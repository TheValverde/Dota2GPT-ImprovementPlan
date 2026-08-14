from __future__ import annotations

from typing import Any

from dota2_coach.opendota.labels import format_duration


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
    if 0 <= slot_id < len(players):
        return players[slot_id]
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


def compact_gold_advantage(match: dict[str, Any], step: int = 5) -> list[dict[str, Any]]:
    series = match.get("radiant_gold_adv") or []
    if not isinstance(series, list):
        return []
    rows: list[dict[str, Any]] = []
    for minute, value in enumerate(series):
        if minute % step != 0 and minute != len(series) - 1:
            continue
        try:
            gold = int(value)
        except (TypeError, ValueError):
            continue
        rows.append(
            {
                "time": format_duration(minute * 60),
                "radiant_gold_adv": gold,
                "leading": "Radiant" if gold > 0 else "Dire" if gold < 0 else "Even",
            }
        )
    return rows


def compact_objectives(match: dict[str, Any], constants) -> list[dict[str, Any]]:
    players = [p for p in match.get("players") or [] if isinstance(p, dict)]
    rows: list[dict[str, Any]] = []
    for event in match.get("objectives") or []:
        if not isinstance(event, dict):
            continue
        kind = str(event.get("type") or "")
        if kind not in {
            "building_kill",
            "CHAT_MESSAGE_ROSHAN_KILL",
            "CHAT_MESSAGE_AEGIS",
            "CHAT_MESSAGE_AEGIS_STOLEN",
            "CHAT_MESSAGE_MINIBOSS_KILL",
            "CHAT_MESSAGE_FIRSTBLOOD",
            "CHAT_MESSAGE_COURIER_LOST",
        }:
            continue
        row: dict[str, Any] = {
            "time": format_duration(event.get("time")),
            "event": kind.replace("CHAT_MESSAGE_", "").replace("_", " ").title(),
        }
        key = event.get("key")
        if isinstance(key, str) and key.startswith("npc_dota_"):
            row["building"] = key.replace("npc_dota_", "").replace("_", " ")
        courier_team = _team_name(event.get("team"))
        if kind == "CHAT_MESSAGE_COURIER_LOST" and courier_team:
            row["courier_team"] = courier_team
        actor = None
        killer = event.get("killer")
        if killer is not None:
            actor = _player_by_slot(players, killer)
        if actor is None:
            slot = event.get("slot")
            if isinstance(slot, int) and 0 <= slot < len(players):
                actor = players[slot]
        if actor is not None:
            row["by"] = _hero_label(actor, constants)
        rows.append(row)
    return rows


def compact_teamfights(
    match: dict[str, Any],
    constants,
    focus: dict[str, Any],
) -> list[dict[str, Any]]:
    players = [p for p in match.get("players") or [] if isinstance(p, dict)]
    focus_index = next(
        (i for i, player in enumerate(players) if player is focus),
        None,
    )
    rows: list[dict[str, Any]] = []
    for fight in match.get("teamfights") or []:
        if not isinstance(fight, dict):
            continue
        entries = fight.get("players") or []
        died: list[str] = []
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or not entry.get("deaths"):
                continue
            if index < len(players):
                died.append(_hero_label(players[index], constants))
        row: dict[str, Any] = {
            "time": format_duration(fight.get("start")),
            "deaths": fight.get("deaths"),
            "died": died,
        }
        if focus_index is not None and focus_index < len(entries):
            focus_row = entries[focus_index] if isinstance(entries[focus_index], dict) else {}
            row["focus_damage"] = focus_row.get("damage")
            row["focus_died"] = bool(focus_row.get("deaths"))
        rows.append(row)
    return rows


def build_macro(match: dict[str, Any], constants, focus: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    objectives = compact_objectives(match, constants)
    fights = compact_teamfights(match, constants, focus)
    gold = compact_gold_advantage(match)
    if objectives:
        payload["objectives"] = objectives
    if fights:
        payload["teamfights"] = fights
    if gold:
        payload["gold_advantage"] = gold
    winner = match.get("radiant_win")
    if winner is True:
        payload["winner"] = "Radiant"
    elif winner is False:
        payload["winner"] = "Dire"
    return payload
