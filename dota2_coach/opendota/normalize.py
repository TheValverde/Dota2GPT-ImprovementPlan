from __future__ import annotations

from typing import Any

from dota2_coach.errors import PlayerNotInMatchError
from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.labels import (
    format_duration,
    is_radiant_slot,
    lane_label,
    rank_label,
)

def find_focus_player(players: list[dict[str, Any]], query: str) -> dict[str, Any]:
    needle = query.strip()
    if not needle:
        raise PlayerNotInMatchError(query, _available_names(players))

    if needle.isdigit():
        account_id = int(needle)
        for player in players:
            if player.get("account_id") == account_id:
                return player
        raise PlayerNotInMatchError(query, _available_names(players))

    lowered = needle.lower()
    exact = [
        player
        for player in players
        if (player.get("personaname") or "").lower() == lowered
    ]
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise PlayerNotInMatchError(
            query,
            _available_names(exact) + ["(name is not unique, use account ID)"],
        )

    partial = [
        player
        for player in players
        if lowered in (player.get("personaname") or "").lower()
    ]
    if len(partial) == 1:
        return partial[0]
    raise PlayerNotInMatchError(query, _available_names(players))


def _available_names(players: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for player in players:
        name = player.get("personaname")
        account_id = player.get("account_id")
        if name:
            names.append(str(name))
        elif account_id:
            names.append(str(account_id))
    return names


def _item_slots(player: dict[str, Any], constants: GameConstants) -> list[str]:
    names: list[str] = []
    for slot in ("item_0", "item_1", "item_2", "item_3", "item_4", "item_5"):
        name = constants.item_name(player.get(slot))
        if name:
            names.append(name)
    return names


def _purchases(player: dict[str, Any], limit: int = 12) -> list[dict[str, Any]]:
    log = player.get("purchase_log") or []
    if not isinstance(log, list):
        return []
    purchases: list[dict[str, Any]] = []
    for entry in log[:limit]:
        if not isinstance(entry, dict):
            continue
        key = entry.get("key")
        purchases.append(
            {
                "item": str(key).replace("_", " ") if key else "unknown",
                "time": format_duration(entry.get("time")),
            }
        )
    return purchases


def _clean_player(
    player: dict[str, Any],
    constants: GameConstants,
    radiant_win: bool | None,
    include_purchases: bool = False,
) -> dict[str, Any]:
    radiant = is_radiant_slot(player.get("player_slot"), player.get("isRadiant"))
    won = player.get("win")
    if won is None and radiant is not None and radiant_win is not None:
        won = radiant == radiant_win

    cleaned: dict[str, Any] = {
        "account_id": player.get("account_id"),
        "name": player.get("personaname") or "Anonymous",
        "hero": constants.hero_name(player.get("hero_id")),
        "team": "Radiant" if radiant else "Dire" if radiant is False else None,
        "won": bool(won) if won is not None else None,
        "level": player.get("level"),
        "kills": player.get("kills"),
        "deaths": player.get("deaths"),
        "assists": player.get("assists"),
        "last_hits": player.get("last_hits"),
        "denies": player.get("denies"),
        "gold_per_min": player.get("gold_per_min"),
        "xp_per_min": player.get("xp_per_min"),
        "net_worth": player.get("net_worth"),
        "hero_damage": player.get("hero_damage"),
        "tower_damage": player.get("tower_damage"),
        "hero_healing": player.get("hero_healing"),
        "lane": lane_label(player.get("lane_role")),
        "rank": rank_label(player.get("rank_tier")),
        "items": _item_slots(player, constants),
        "neutral_item": constants.item_name(player.get("item_neutral")),
        "observer_wards": player.get("obs_placed"),
        "sentry_wards": player.get("sen_placed"),
        "camps_stacked": player.get("camps_stacked"),
        "runes": player.get("rune_pickups"),
        "teamfight_participation": player.get("teamfight_participation"),
        "stuns": player.get("stuns"),
        "roshan_kills": player.get("roshan_kills"),
        "tower_kills": player.get("tower_kills"),
        "first_blood": bool(player.get("firstblood_claimed"))
        if player.get("firstblood_claimed") is not None
        else None,
    }
    if include_purchases:
        cleaned["early_purchases"] = _purchases(player)
    return {key: value for key, value in cleaned.items() if value not in (None, [], {})}


def build_match_brief(
    match: dict[str, Any],
    player_query: str,
    constants: GameConstants,
) -> dict[str, Any]:
    players = [p for p in match.get("players") or [] if isinstance(p, dict)]
    focus = find_focus_player(players, player_query)
    radiant_win = match.get("radiant_win")
    scoreboard = [
        _clean_player(player, constants, radiant_win, include_purchases=False)
        for player in players
    ]
    return {
        "match_id": match.get("match_id"),
        "duration": format_duration(match.get("duration")),
        "duration_seconds": match.get("duration"),
        "game_mode": constants.game_mode_name(match.get("game_mode")),
        "lobby": constants.lobby_name(match.get("lobby_type")),
        "radiant_win": radiant_win,
        "radiant_score": match.get("radiant_score"),
        "dire_score": match.get("dire_score"),
        "first_blood_time": format_duration(match.get("first_blood_time")),
        "focus_player": _clean_player(
            focus, constants, radiant_win, include_purchases=True
        ),
        "scoreboard": scoreboard,
    }
