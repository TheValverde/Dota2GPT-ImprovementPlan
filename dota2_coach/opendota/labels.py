from __future__ import annotations

RANK_NAMES = {
    1: "Herald",
    2: "Guardian",
    3: "Crusader",
    4: "Archon",
    5: "Legend",
    6: "Ancient",
    7: "Divine",
    8: "Immortal",
}

LANE_ROLES = {
    1: "Safe lane",
    2: "Mid lane",
    3: "Off lane",
    4: "Jungle",
}


def format_duration(seconds: int | None) -> str | None:
    if seconds is None:
        return None
    sign = "-" if seconds < 0 else ""
    minutes, remainder = divmod(abs(seconds), 60)
    return f"{sign}{minutes}:{remainder:02d}"


def rank_label(rank_tier: int | None) -> str | None:
    if not rank_tier:
        return None
    medal = RANK_NAMES.get(rank_tier // 10)
    if medal is None:
        return None
    if medal == "Immortal":
        return medal
    stars = rank_tier % 10
    if stars:
        return f"{medal} {stars}"
    return medal


def lane_label(lane_role: int | None) -> str | None:
    if not lane_role:
        return None
    return LANE_ROLES.get(lane_role, f"Lane {lane_role}")


def is_radiant_slot(player_slot: int | None, is_radiant: bool | None) -> bool | None:
    if is_radiant is not None:
        return bool(is_radiant)
    if player_slot is None:
        return None
    return player_slot < 128
