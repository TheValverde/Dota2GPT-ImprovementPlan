from __future__ import annotations

from dataclasses import dataclass
from typing import Any

RANKED_LOBBY_TYPES = {5, 6, 7}
TURBO_GAME_MODE = 23


@dataclass(frozen=True)
class FantasyFilters:
    ranked_only: bool = False
    hide_turbo: bool = False


def match_passes_filters(match: dict[str, Any], filters: FantasyFilters) -> bool:
    lobby = match.get("lobby_type")
    mode = match.get("game_mode_id")
    if mode is None:
        mode = match.get("game_mode")
    try:
        lobby_id = int(lobby) if lobby is not None else None
    except (TypeError, ValueError):
        lobby_id = None
    try:
        mode_id = int(mode) if mode is not None and not isinstance(mode, str) else None
    except (TypeError, ValueError):
        mode_id = None
    if filters.ranked_only and lobby_id not in RANKED_LOBBY_TYPES:
        return False
    if filters.hide_turbo and mode_id == TURBO_GAME_MODE:
        return False
    return True
