from __future__ import annotations

from time import time
from typing import Any

from dota2_coach.errors import TrackedPlayerNotFoundError
from dota2_coach.fantasy.scoring import Span, score_match
from dota2_coach.fantasy.store import FantasyStore
from dota2_coach.opendota.client import OpenDotaClient
from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.labels import rank_label


class FantasyTracker:
    def __init__(self, opendota: OpenDotaClient, store: FantasyStore) -> None:
        self.opendota = opendota
        self.store = store

    def add_player(self, account_id: int, span: Span | None = None) -> dict[str, Any]:
        profile = self.opendota.get_player(account_id)
        existing = self.store.get_player(account_id)
        self.store.add_player(
            account_id=account_id,
            personaname=profile["personaname"],
            avatarfull=profile.get("avatarfull"),
            rank_tier=profile.get("rank_tier"),
            added_at=int(existing["added_at"]) if existing else int(time()),
        )
        active_span = span or Span(amount=30, unit="days")
        self.refresh_player(account_id, active_span)
        return self.player_card(account_id, active_span)

    def remove_player(self, account_id: int) -> None:
        if not self.store.remove_player(account_id):
            raise TrackedPlayerNotFoundError(account_id)

    def refresh(self, span: Span, account_id: int | None = None) -> dict[str, Any]:
        ids = [account_id] if account_id is not None else [
            row["account_id"] for row in self.store.list_players()
        ]
        for tracked_id in ids:
            if not self.store.get_player(tracked_id):
                raise TrackedPlayerNotFoundError(tracked_id)
            self.refresh_player(tracked_id, span)
        return self.summary(span)

    def refresh_player(self, account_id: int, span: Span) -> None:
        days = span.as_days()
        fetch_days = None if days is None else min(max(days, 90), 365)
        rows = self.opendota.player_matches(
            account_id,
            days=fetch_days,
            limit=span.fetch_limit() if span.unit == "matches" else 200,
        )
        constants = self.opendota.load_constants()
        prepared = [self._prepare_match(row, constants) for row in rows]
        self.store.upsert_matches(account_id, prepared)

    def summary(self, span: Span) -> dict[str, Any]:
        now = int(time())
        players = []
        for row in self.store.list_players():
            players.append(self._summarize_player(row, span, now))
        players.sort(key=lambda item: item["total"], reverse=True)
        return {
            "span": {"amount": span.amount, "unit": span.unit, "label": span.label()},
            "players": players,
            "formula": "OpenDota fantasy weights plus 0.15 per assist.",
        }

    def player_card(self, account_id: int, span: Span) -> dict[str, Any]:
        row = self.store.get_player(account_id)
        if row is None:
            raise TrackedPlayerNotFoundError(account_id)
        now = int(time())
        return self._summarize_player(row, span, now, include_matches=True)

    def _summarize_player(
        self,
        row: dict[str, Any],
        span: Span,
        now: int,
        include_matches: bool = False,
    ) -> dict[str, Any]:
        matches = self.store.matches_for_span(row["account_id"], span, now)
        totals = [float(match.get("points") or 0) for match in matches]
        total = round(sum(totals), 1)
        average = round(total / len(totals), 1) if totals else 0.0
        best = max(totals) if totals else None
        worst = min(totals) if totals else None
        card = {
            "account_id": row["account_id"],
            "personaname": row["personaname"],
            "avatarfull": row.get("avatarfull"),
            "rank": rank_label(row.get("rank_tier")),
            "match_count": len(matches),
            "total": total,
            "average": average,
            "best": best,
            "worst": worst,
            "sparkline": totals[:20][::-1],
        }
        if include_matches:
            card["matches"] = matches
        return card

    def _prepare_match(self, row: dict[str, Any], constants: GameConstants) -> dict[str, Any]:
        radiant_win = row.get("radiant_win")
        slot = row.get("player_slot") or 0
        won = None
        if radiant_win is not None:
            won = bool(radiant_win) == (slot < 128)
        prepared = dict(row)
        prepared["hero"] = constants.hero_name(row.get("hero_id"))
        prepared["won"] = won
        prepared["game_mode"] = constants.game_mode_name(row.get("game_mode"))
        score = score_match(prepared)
        prepared["points"] = score.total
        prepared["parsed"] = score.parsed
        prepared["breakdown"] = score.breakdown
        return prepared
