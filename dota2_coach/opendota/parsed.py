from __future__ import annotations

from typing import Any

PARSED_LOOKBACK = 50


def is_parsed(row: dict[str, Any]) -> bool:
    return row.get("version") is not None


def first_parsed(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in rows:
        if is_parsed(row):
            return row
    return None


def account_id_from_player(player: str) -> int | None:
    needle = player.strip()
    if needle.isdigit():
        return int(needle)
    return None
