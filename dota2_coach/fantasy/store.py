from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from dota2_coach.fantasy.scoring import Span, score_match


class FantasyStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS roster (
                    account_id INTEGER PRIMARY KEY,
                    personaname TEXT NOT NULL,
                    avatarfull TEXT,
                    rank_tier INTEGER,
                    added_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS matches (
                    account_id INTEGER NOT NULL,
                    match_id INTEGER NOT NULL,
                    start_time INTEGER,
                    hero_id INTEGER,
                    won INTEGER,
                    payload TEXT NOT NULL,
                    points REAL NOT NULL,
                    parsed INTEGER NOT NULL,
                    PRIMARY KEY (account_id, match_id)
                );
                """
            )

    def add_player(
        self,
        account_id: int,
        personaname: str,
        avatarfull: str | None,
        rank_tier: int | None,
        added_at: int,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO roster (account_id, personaname, avatarfull, rank_tier, added_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                    personaname = excluded.personaname,
                    avatarfull = excluded.avatarfull,
                    rank_tier = excluded.rank_tier
                """,
                (account_id, personaname, avatarfull, rank_tier, added_at),
            )

    def remove_player(self, account_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM roster WHERE account_id = ?", (account_id,)
            )
            connection.execute("DELETE FROM matches WHERE account_id = ?", (account_id,))
            return cursor.rowcount > 0

    def list_players(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM roster ORDER BY added_at ASC"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_player(self, account_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM roster WHERE account_id = ?", (account_id,)
            ).fetchone()
        return dict(row) if row else None

    def upsert_matches(self, account_id: int, matches: list[dict[str, Any]]) -> None:
        with self._connect() as connection:
            for match in matches:
                match_id = match.get("match_id")
                if match_id is None:
                    continue
                score = score_match(match)
                won = match.get("won")
                won_flag = None if won is None else int(bool(won))
                connection.execute(
                    """
                    INSERT INTO matches (
                        account_id, match_id, start_time, hero_id, won, payload, points, parsed
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(account_id, match_id) DO UPDATE SET
                        start_time = excluded.start_time,
                        hero_id = excluded.hero_id,
                        won = excluded.won,
                        payload = excluded.payload,
                        points = excluded.points,
                        parsed = excluded.parsed
                    """,
                    (
                        account_id,
                        int(match_id),
                        match.get("start_time"),
                        match.get("hero_id"),
                        won_flag,
                        json.dumps(match),
                        score.total,
                        int(score.parsed),
                    ),
                )

    def matches_for_span(self, account_id: int, span: Span, now: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM matches
                WHERE account_id = ?
                ORDER BY start_time DESC
                """,
                (account_id,),
            ).fetchall()
        scored: list[dict[str, Any]] = []
        days = span.as_days()
        cutoff = now - days * 86400 if days is not None else None
        for row in rows:
            start_time = row["start_time"] or 0
            if cutoff is not None and start_time < cutoff:
                continue
            payload = json.loads(row["payload"])
            payload["points"] = row["points"]
            payload["parsed"] = bool(row["parsed"])
            payload["won"] = None if row["won"] is None else bool(row["won"])
            scored.append(payload)
        limit = span.match_limit()
        if limit is not None:
            return scored[:limit]
        return scored
