from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx


def _localized_name(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    for key in ("localized_name", "dname", "name"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            cleaned = value
            for prefix in ("game_mode_", "lobby_type_"):
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix) :]
            return cleaned.replace("_", " ").title()
    return None


def _id_name_map(payload: Any) -> dict[int, str]:
    mapping: dict[int, str] = {}
    if not isinstance(payload, dict):
        return mapping
    for key, entry in payload.items():
        name = _localized_name(entry)
        item_id = None
        if isinstance(entry, dict) and entry.get("id") is not None:
            item_id = int(entry["id"])
        elif str(key).isdigit():
            item_id = int(key)
        if item_id is None or not name:
            continue
        mapping[item_id] = name
    return mapping


@dataclass
class GameConstants:
    heroes: dict[int, str] = field(default_factory=dict)
    hero_npcs: dict[int, str] = field(default_factory=dict)
    items: dict[int, str] = field(default_factory=dict)
    game_modes: dict[int, str] = field(default_factory=dict)
    lobby_types: dict[int, str] = field(default_factory=dict)

    def hero_name(self, hero_id: int | None) -> str | None:
        if hero_id is None:
            return None
        return self.heroes.get(hero_id, f"Hero {hero_id}")

    def hero_npc(self, hero_id: int | None) -> str | None:
        if hero_id is None:
            return None
        return self.hero_npcs.get(hero_id)

    def item_name(self, item_id: int | None) -> str | None:
        if not item_id:
            return None
        return self.items.get(item_id, f"Item {item_id}")

    def game_mode_name(self, mode_id: int | None) -> str | None:
        if mode_id is None:
            return None
        return self.game_modes.get(mode_id, f"Mode {mode_id}")

    def lobby_name(self, lobby_id: int | None) -> str | None:
        if lobby_id is None:
            return None
        return self.lobby_types.get(lobby_id, f"Lobby {lobby_id}")


def _npc_name_map(payload: Any) -> dict[int, str]:
    mapping: dict[int, str] = {}
    if not isinstance(payload, dict):
        return mapping
    for key, entry in payload.items():
        if not isinstance(entry, dict):
            continue
        npc = entry.get("name")
        if not isinstance(npc, str) or not npc.startswith("npc_dota_hero_"):
            continue
        hero_id = entry.get("id")
        if hero_id is None and str(key).isdigit():
            hero_id = int(key)
        if hero_id is None:
            continue
        mapping[int(hero_id)] = npc
    return mapping


def constants_from_payloads(
    heroes: Any,
    items: Any,
    game_modes: Any,
    lobby_types: Any,
) -> GameConstants:
    return GameConstants(
        heroes=_id_name_map(heroes),
        hero_npcs=_npc_name_map(heroes),
        items=_id_name_map(items),
        game_modes=_id_name_map(game_modes),
        lobby_types=_id_name_map(lobby_types),
    )


class ConstantsClient:
    def __init__(self, http: httpx.Client, base_url: str) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._cache: GameConstants | None = None

    def load(self) -> GameConstants:
        if self._cache is not None:
            return self._cache
        heroes = self._get("constants/heroes")
        items = self._get("constants/items")
        game_modes = self._get("constants/game_mode")
        lobby_types = self._get("constants/lobby_type")
        self._cache = constants_from_payloads(heroes, items, game_modes, lobby_types)
        return self._cache

    def _get(self, path: str) -> Any:
        response = self._http.get(f"{self._base_url}/{path}")
        response.raise_for_status()
        return response.json()
