from __future__ import annotations

from typing import Any

from dota2_coach.fantasy.scoring import score_match
from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.labels import is_radiant_slot

FIELD_MATCH_CAP = 40
PARSE_REQUEST_CAP = 10
DUO_MIN_GAMES = 2


def lobby_player_stats(
    match: dict[str, Any],
    player: dict[str, Any],
    constants: GameConstants | None = None,
) -> dict[str, Any]:
    radiant = is_radiant_slot(player.get("player_slot"), player.get("isRadiant"))
    radiant_win = match.get("radiant_win")
    won = None
    if radiant is not None and radiant_win is not None:
        won = radiant == bool(radiant_win)
    hero_id = player.get("hero_id")
    stats = {
        "match_id": match.get("match_id"),
        "account_id": player.get("account_id"),
        "personaname": player.get("personaname") or "Anonymous",
        "hero_id": hero_id,
        "hero": constants.hero_name(hero_id) if constants else None,
        "kills": player.get("kills"),
        "deaths": player.get("deaths"),
        "assists": player.get("assists"),
        "last_hits": player.get("last_hits"),
        "denies": player.get("denies"),
        "gold_per_min": player.get("gold_per_min"),
        "xp_per_min": player.get("xp_per_min"),
        "tower_kills": player.get("tower_kills") or player.get("towers_killed"),
        "roshan_kills": player.get("roshan_kills") or player.get("roshans_killed"),
        "teamfight_participation": player.get("teamfight_participation"),
        "obs_placed": player.get("obs_placed") or player.get("observer_wards_placed"),
        "camps_stacked": player.get("camps_stacked"),
        "rune_pickups": player.get("rune_pickups") or player.get("runes_grabbed"),
        "firstblood_claimed": player.get("firstblood_claimed"),
        "stuns": player.get("stuns"),
        "player_slot": player.get("player_slot"),
        "is_radiant": radiant,
        "won": won,
        "start_time": match.get("start_time"),
        "lobby_type": match.get("lobby_type"),
        "game_mode": match.get("game_mode"),
        "game_mode_id": match.get("game_mode"),
        "parsed": match.get("version") is not None,
    }
    score = score_match(stats)
    stats["points"] = score.total
    stats["breakdown"] = score.breakdown
    if match.get("version") is not None:
        stats["parsed"] = True
    return stats


def _find_focus(
    players: list[dict[str, Any]], account_id: int
) -> dict[str, Any] | None:
    for player in players:
        if player.get("account_id") == account_id:
            return player
    return None


def aggregate_ranked_field(
    focus_account_id: int,
    matches: list[dict[str, Any]],
    constants: GameConstants | None = None,
) -> dict[str, Any]:
    buckets: dict[int, dict[str, Any]] = {}
    parsed_matches = 0
    used_matches = 0
    unparsed_ids: list[int] = []

    for match in matches:
        players = [row for row in (match.get("players") or []) if isinstance(row, dict)]
        focus = _find_focus(players, focus_account_id)
        if focus is None:
            continue
        used_matches += 1
        if match.get("version") is not None:
            parsed_matches += 1
        else:
            match_id = match.get("match_id")
            if match_id is not None:
                unparsed_ids.append(int(match_id))
        focus_radiant = is_radiant_slot(focus.get("player_slot"), focus.get("isRadiant"))
        for player in players:
            account_id = player.get("account_id")
            if account_id is None:
                continue
            account_id = int(account_id)
            stats = lobby_player_stats(match, player, constants)
            radiant = stats.get("is_radiant")
            same_team = (
                focus_radiant is not None
                and radiant is not None
                and radiant == focus_radiant
            )
            bucket = buckets.get(account_id)
            if bucket is None:
                bucket = {
                    "account_id": account_id,
                    "personaname": stats["personaname"],
                    "games": 0,
                    "teammate_games": 0,
                    "enemy_games": 0,
                    "wins": 0,
                    "total": 0.0,
                    "points": [],
                }
                buckets[account_id] = bucket
            if stats["personaname"] and stats["personaname"] != "Anonymous":
                bucket["personaname"] = stats["personaname"]
            bucket["games"] += 1
            bucket["total"] = round(bucket["total"] + float(stats["points"]), 1)
            bucket["points"].append(float(stats["points"]))
            if stats.get("won") is True:
                bucket["wins"] += 1
            if account_id == focus_account_id:
                continue
            if same_team:
                bucket["teammate_games"] += 1
            else:
                bucket["enemy_games"] += 1

    others = [
        row
        for row in buckets.values()
        if row["account_id"] != focus_account_id and row["personaname"] != "Anonymous"
    ]
    duo_games = 0
    if others:
        duo_games = max(row["teammate_games"] for row in others)
        if duo_games < DUO_MIN_GAMES:
            duo_games = 0

    players: list[dict[str, Any]] = []
    for row in buckets.values():
        average = round(row["total"] / row["games"], 1) if row["games"] else 0.0
        is_focus = row["account_id"] == focus_account_id
        is_duo = (not is_focus) and duo_games > 0 and row["teammate_games"] == duo_games
        is_stack = (not is_focus) and (not is_duo) and row["teammate_games"] >= DUO_MIN_GAMES
        if is_focus:
            relation = "you"
        elif is_duo:
            relation = "duo"
        elif is_stack:
            relation = "stack"
        elif row["teammate_games"] > row["enemy_games"]:
            relation = "teammate"
        elif row["enemy_games"] > 0:
            relation = "enemy"
        else:
            relation = "lobby"
        players.append(
            {
                "account_id": row["account_id"],
                "personaname": row["personaname"],
                "games": row["games"],
                "teammate_games": row["teammate_games"],
                "enemy_games": row["enemy_games"],
                "wins": row["wins"],
                "total": row["total"],
                "average": average,
                "relation": relation,
                "is_focus": is_focus,
                "is_duo": is_duo,
            }
        )

    players.sort(
        key=lambda item: (item["average"], item["games"], item["total"]),
        reverse=True,
    )
    for index, row in enumerate(players, start=1):
        row["rank"] = index

    you = next((row for row in players if row["is_focus"]), None)
    duo = next((row for row in players if row["is_duo"]), None)
    regulars = [row for row in players if row["games"] >= DUO_MIN_GAMES or row["is_focus"]]
    display = sorted(
        regulars,
        key=lambda item: (
            not item["is_focus"],
            not item["is_duo"],
            -item["teammate_games"],
            -item["average"],
        ),
    )
    return {
        "match_count": used_matches,
        "parsed_matches": parsed_matches,
        "unparsed_match_ids": unparsed_ids,
        "you": you,
        "duo": duo,
        "players": players,
        "regulars": display,
        "one_game_players": max(len(players) - len(regulars), 0),
    }
