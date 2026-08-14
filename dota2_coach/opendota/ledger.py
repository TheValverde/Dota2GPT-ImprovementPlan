from __future__ import annotations

from typing import Any

from dota2_coach.opendota.abilities import kill_key_matches, npc_hero_label
from dota2_coach.opendota.labels import format_duration, is_radiant_slot

EARLY_WINDOW_SECONDS = 8 * 60

LEDGER_NOTE = (
    "event_ledger is the whole game on one clock: kills, towers, Roshan, "
    "couriers, the focus player's wards with a map region, runes, and finished "
    "items. Read it in order and chain rows that sit together. A ward, then "
    "courier kills, then kills on the lane opponents is one play. Rows with "
    "focus_lane true are the focus player's own lane during the laning stage."
)

RUNE_NAMES = {
    0: "Double Damage",
    1: "Haste",
    2: "Illusion",
    3: "Invisibility",
    4: "Regeneration",
    5: "Bounty",
    6: "Arcane",
    7: "Water",
    8: "Shield",
    9: "Wisdom",
}

_SKIP_PURCHASES = {
    "tango",
    "flask",
    "clarity",
    "faerie fire",
    "enchanted mango",
    "branches",
    "tpscroll",
    "ward observer",
    "ward sentry",
    "ward dispenser",
    "dust",
    "smoke of deceit",
    "tome of knowledge",
    "magic stick",
    "circlet",
    "slippers",
    "gauntlets",
    "mantle",
    "ring of protection",
    "quelling blade",
    "blades of attack",
    "gloves",
    "boots of elves",
    "belt of strength",
    "band of elvenskin",
    "crown",
    "robe",
    "staff of wizardry",
    "ogre axe",
    "blade of alacrity",
    "point booster",
    "sobi mask",
    "sage mask",
    "ring of regen",
    "ring of tarrasque",
    "tiara of selemene",
    "void stone",
    "energy booster",
    "vitality booster",
    "mithril hammer",
    "javelin",
    "broadsword",
    "claymore",
    "demon edge",
    "eaglesong",
    "reaver",
    "sacred relic",
    "relic",
    "mystic staff",
    "hyperstone",
    "platemail",
    "chainmail",
    "helm of iron will",
    "blitz knuckles",
    "shadow amulet",
    "wind lace",
    "fluffy hat",
    "headdress",
    "blight stone",
    "diadem",
    "cornucopia",
    "wizard hat",
}


def map_region(x: Any, y: Any) -> str | None:
    """Rough map region from OpenDota ward grid coordinates (about 64 to 192).

    The river runs top-left to bottom-right; Radiant holds the bottom-left,
    Dire the top-right, so x+y splits the sides and x-y splits top from bottom.
    """
    try:
        xf = float(x)
        yf = float(y)
    except (TypeError, ValueError):
        return None
    if abs(xf - yf) <= 14:
        lane = "mid"
    elif xf - yf > 14:
        lane = "bottom half"
    else:
        lane = "top half"
    total = xf + yf
    if total < 250:
        side = "Radiant side"
    elif total > 262:
        side = "Dire side"
    else:
        side = "river"
    return f"{lane}, {side}"


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


def _team_of(player: dict[str, Any]) -> str | None:
    radiant = is_radiant_slot(player.get("player_slot"), player.get("isRadiant"))
    if radiant is None:
        return None
    return "Radiant" if radiant else "Dire"


def _seconds(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _victim(
    players: list[dict[str, Any]], key: Any, constants
) -> tuple[str, dict[str, Any] | None]:
    for player in players:
        if kill_key_matches(key, player, constants):
            return _hero_label(player, constants), player
    return npc_hero_label(key) or "unknown", None


def build_event_ledger(
    match: dict[str, Any], constants, focus: dict[str, Any]
) -> list[dict[str, Any]]:
    players = [p for p in match.get("players") or [] if isinstance(p, dict)]
    focus_slot = focus.get("player_slot")
    focus_lane = focus.get("lane")
    focus_label = _hero_label(focus, constants)
    events: list[tuple[int, int, dict[str, Any]]] = []

    def add(t: int, row: dict[str, Any], order: int = 1) -> None:
        row["t"] = t
        row["time"] = format_duration(t)
        events.append((t, order, row))

    for kind, log in (
        ("observer_ward", focus.get("obs_log")),
        ("sentry_ward", focus.get("sen_log")),
    ):
        for entry in log or []:
            if not isinstance(entry, dict):
                continue
            t = _seconds(entry.get("time"))
            if t is None:
                continue
            row: dict[str, Any] = {"event": kind, "by": focus_label, "by_focus": True}
            region = map_region(entry.get("x"), entry.get("y"))
            if region:
                row["region"] = region
            add(t, row, order=0)

    for entry in focus.get("runes_log") or []:
        if not isinstance(entry, dict):
            continue
        t = _seconds(entry.get("time"))
        if t is None:
            continue
        rune = RUNE_NAMES.get(_seconds(entry.get("key")) or -1)
        add(t, {"event": "rune", "rune": rune or str(entry.get("key")), "by_focus": True})

    for entry in focus.get("purchase_log") or []:
        if not isinstance(entry, dict):
            continue
        t = _seconds(entry.get("time"))
        if t is None:
            continue
        item = str(entry.get("key") or "").replace("_", " ")
        if not item or item in _SKIP_PURCHASES or item.startswith("recipe "):
            continue
        add(t, {"event": "item", "item": item, "by_focus": True})

    for player in players:
        is_focus = player is focus or player.get("player_slot") == focus_slot
        by_team = _team_of(player)
        for entry in player.get("kills_log") or []:
            if not isinstance(entry, dict):
                continue
            t = _seconds(entry.get("time"))
            if t is None:
                continue
            victim_label, victim_player = _victim(players, entry.get("key"), constants)
            row = {
                "event": "hero_kill",
                "by": _hero_label(player, constants),
                "victim": victim_label,
            }
            if by_team:
                row["by_team"] = by_team
            if is_focus:
                row["by_focus"] = True
            victim_is_focus = victim_player is focus or (
                victim_player is not None
                and victim_player.get("player_slot") == focus_slot
            )
            if victim_is_focus:
                row["victim_is_focus"] = True
            if t <= EARLY_WINDOW_SECONDS and focus_lane is not None:
                in_lane = (
                    is_focus
                    or victim_is_focus
                    or player.get("lane") == focus_lane
                    or (victim_player is not None and victim_player.get("lane") == focus_lane)
                )
                row["focus_lane"] = bool(in_lane)
            add(t, row)

    for event in match.get("objectives") or []:
        if not isinstance(event, dict):
            continue
        t = _seconds(event.get("time"))
        if t is None:
            continue
        kind = str(event.get("type") or "")
        if kind == "building_kill":
            key = str(event.get("key") or "")
            row = {"event": "building"}
            if key.startswith("npc_dota_"):
                row["building"] = key.replace("npc_dota_", "").replace("_", " ")
            if "goodguys" in key:
                row["lost_by"] = "Radiant"
            elif "badguys" in key:
                row["lost_by"] = "Dire"
            actor = _player_by_slot(players, event.get("player_slot"))
            if actor is None:
                actor = _player_by_slot(players, event.get("killer"))
            if actor is not None:
                row["by"] = _hero_label(actor, constants)
                if actor is focus or actor.get("player_slot") == focus_slot:
                    row["by_focus"] = True
            add(t, row)
        elif kind == "CHAT_MESSAGE_COURIER_LOST":
            row = {"event": "courier_kill"}
            team = _team_name(event.get("team"))
            if team:
                row["courier_team"] = team
            killer = _player_by_slot(players, event.get("killer"))
            if killer is not None:
                row["by"] = _hero_label(killer, constants)
                if killer is focus or killer.get("player_slot") == focus_slot:
                    row["by_focus"] = True
            add(t, row)
        elif kind == "CHAT_MESSAGE_ROSHAN_KILL":
            row = {"event": "roshan"}
            team = _team_name(event.get("team"))
            if team:
                row["by_team"] = team
            add(t, row)
        elif kind in {"CHAT_MESSAGE_AEGIS", "CHAT_MESSAGE_AEGIS_STOLEN"}:
            row = {"event": "aegis" if kind == "CHAT_MESSAGE_AEGIS" else "aegis_stolen"}
            actor = _player_by_slot(players, event.get("player_slot"))
            if actor is None:
                slot = event.get("slot")
                if isinstance(slot, int) and 0 <= slot < len(players):
                    actor = players[slot]
            if actor is not None:
                row["by"] = _hero_label(actor, constants)
                if actor is focus or actor.get("player_slot") == focus_slot:
                    row["by_focus"] = True
            add(t, row)
        elif kind == "CHAT_MESSAGE_MINIBOSS_KILL":
            add(t, {"event": "tormentor"})
        elif kind == "CHAT_MESSAGE_FIRSTBLOOD":
            row = {"event": "first_blood"}
            actor = _player_by_slot(players, event.get("player_slot"))
            if actor is not None:
                row["by"] = _hero_label(actor, constants)
                if actor is focus or actor.get("player_slot") == focus_slot:
                    row["by_focus"] = True
            add(t, row, order=0)

    events.sort(key=lambda item: (item[0], item[1]))
    return [row for _, _, row in events]
