from __future__ import annotations

from time import time
from typing import Any

from dota2_coach.errors import MatchNotFoundError, TrackedPlayerNotFoundError
from dota2_coach.fantasy.field import (
    FIELD_MATCH_CAP,
    PARSE_REQUEST_CAP,
    aggregate_ranked_field,
    lobby_player_stats,
)
from dota2_coach.fantasy.scoring import Span, score_match
from dota2_coach.fantasy.store import FantasyStore
from dota2_coach.opendota.client import OpenDotaClient
from dota2_coach.opendota.constants import GameConstants
from dota2_coach.opendota.filters import FantasyFilters
from dota2_coach.opendota.labels import rank_label
from dota2_coach.opendota.parse_jobs import submit_parse


class FantasyTracker:
    def __init__(self, opendota: OpenDotaClient, store: FantasyStore) -> None:
        self.opendota = opendota
        self.store = store

    def add_player(
        self,
        account_id: int,
        span: Span | None = None,
        filters: FantasyFilters | None = None,
    ) -> dict[str, Any]:
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
        return self.player_card(account_id, active_span, filters)

    def remove_player(self, account_id: int) -> None:
        if not self.store.remove_player(account_id):
            raise TrackedPlayerNotFoundError(account_id)

    def refresh(
        self,
        span: Span,
        account_id: int | None = None,
        filters: FantasyFilters | None = None,
    ) -> dict[str, Any]:
        ids = [account_id] if account_id is not None else [
            row["account_id"] for row in self.store.list_players()
        ]
        for tracked_id in ids:
            if not self.store.get_player(tracked_id):
                raise TrackedPlayerNotFoundError(tracked_id)
            self.refresh_player(tracked_id, span)
        return self.summary(span, filters)

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

    def summary(
        self,
        span: Span,
        filters: FantasyFilters | None = None,
    ) -> dict[str, Any]:
        now = int(time())
        active = filters or FantasyFilters()
        players = [
            self._summarize_player(row, span, now, filters=active)
            for row in self.store.list_players()
        ]
        players.sort(key=lambda item: item["total"], reverse=True)
        return {
            "span": {"amount": span.amount, "unit": span.unit, "label": span.label()},
            "filters": {
                "ranked_only": active.ranked_only,
                "hide_turbo": active.hide_turbo,
            },
            "players": players,
            "formula": "OpenDota fantasy weights plus 0.15 per assist.",
        }

    def player_card(
        self,
        account_id: int,
        span: Span,
        filters: FantasyFilters | None = None,
    ) -> dict[str, Any]:
        row = self.store.get_player(account_id)
        if row is None:
            raise TrackedPlayerNotFoundError(account_id)
        now = int(time())
        return self._summarize_player(
            row, span, now, include_matches=True, filters=filters
        )

    def _summarize_player(
        self,
        row: dict[str, Any],
        span: Span,
        now: int,
        include_matches: bool = False,
        filters: FantasyFilters | None = None,
    ) -> dict[str, Any]:
        matches = self.store.matches_for_span(
            row["account_id"], span, now, filters=filters
        )
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
        prepared["game_mode_id"] = row.get("game_mode")
        prepared["lobby_type"] = row.get("lobby_type")
        prepared["game_mode"] = constants.game_mode_name(row.get("game_mode"))
        score = score_match(prepared)
        prepared["points"] = score.total
        prepared["parsed"] = score.parsed
        prepared["breakdown"] = score.breakdown
        return prepared

    def ranked_field(
        self,
        account_id: int,
        span: Span,
        hide_turbo: bool = False,
    ) -> dict[str, Any]:
        if not self.store.get_player(account_id):
            raise TrackedPlayerNotFoundError(account_id)
        ranked_rows = self._ranked_span_matches(account_id, span, hide_turbo)
        constants = self.opendota.load_constants()
        full_matches: list[dict[str, Any]] = []
        missing: list[int] = []
        for row in ranked_rows:
            match_id = row.get("match_id")
            if match_id is None:
                continue
            match = self._load_full_match(int(match_id))
            if match is None:
                missing.append(int(match_id))
                continue
            self._rescore_focus_from_lobby(
                account_id,
                match,
                constants,
                fallback_start=row.get("start_time"),
            )
            full_matches.append(match)
        field = aggregate_ranked_field(account_id, full_matches, constants)
        return {
            "account_id": account_id,
            "span": {"amount": span.amount, "unit": span.unit, "label": span.label()},
            "ranked_only": True,
            "hide_turbo": hide_turbo,
            "formula": "OpenDota fantasy weights plus 0.15 per assist.",
            "note": (
                "Points are from the same ranked lobbies only. "
                "Duo is the player on your team most often."
            ),
            "missing_match_ids": missing,
            "parse_cap": PARSE_REQUEST_CAP,
            **field,
        }

    def parse_missing_ranked(
        self,
        account_id: int,
        span: Span,
        hide_turbo: bool = False,
    ) -> dict[str, Any]:
        if not self.store.get_player(account_id):
            raise TrackedPlayerNotFoundError(account_id)
        ranked_rows = self._ranked_span_matches(account_id, span, hide_turbo)
        jobs: list[dict[str, Any]] = []
        already = 0
        skipped = 0
        requested = 0
        for row in ranked_rows:
            match_id = row.get("match_id")
            if match_id is None:
                continue
            match = self._load_full_match(int(match_id), refresh_unparsed=True)
            if match is None:
                skipped += 1
                continue
            if match.get("version") is not None:
                already += 1
                continue
            if requested >= PARSE_REQUEST_CAP:
                skipped += 1
                continue
            result = submit_parse(self.opendota, match)
            if result.get("parsed"):
                already += 1
                continue
            jobs.append(result)
            if result.get("job_id"):
                requested += 1
            else:
                skipped += 1
        return {
            "account_id": account_id,
            "already_parsed": already,
            "requested": len([job for job in jobs if job.get("job_id")]),
            "skipped": skipped,
            "jobs": jobs,
            "parse_cap": PARSE_REQUEST_CAP,
            "message": (
                "Requested OpenDota parses for unparsed ranked replays. "
                "Each request counts as 10 OpenDota calls."
            ),
        }

    def _ranked_span_matches(
        self,
        account_id: int,
        span: Span,
        hide_turbo: bool,
    ) -> list[dict[str, Any]]:
        filters = FantasyFilters(ranked_only=True, hide_turbo=hide_turbo)
        rows = self.store.matches_for_span(account_id, span, int(time()), filters)
        return rows[:FIELD_MATCH_CAP]

    def _load_full_match(
        self,
        match_id: int,
        refresh_unparsed: bool = True,
    ) -> dict[str, Any] | None:
        cached = self.store.get_full_match(match_id)
        if cached and cached.get("version") is not None:
            return cached
        if cached and not refresh_unparsed:
            return cached
        try:
            match = self.opendota.get_match(match_id)
        except MatchNotFoundError:
            return cached
        self.store.upsert_full_match(match)
        return match

    def _rescore_focus_from_lobby(
        self,
        account_id: int,
        match: dict[str, Any],
        constants: GameConstants,
        fallback_start: int | None = None,
    ) -> None:
        for player in match.get("players") or []:
            if not isinstance(player, dict):
                continue
            if player.get("account_id") != account_id:
                continue
            stats = lobby_player_stats(match, player, constants)
            if not stats.get("start_time") and fallback_start:
                stats["start_time"] = fallback_start
            self.store.upsert_matches(account_id, [stats])
            return
