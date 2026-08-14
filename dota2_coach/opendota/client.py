from __future__ import annotations

from typing import Any

import httpx

from dota2_coach.errors import MatchNotFoundError, OpenDotaError
from dota2_coach.opendota.constants import ConstantsClient, GameConstants

MATCH_PROJECT = (
    "kills",
    "deaths",
    "assists",
    "last_hits",
    "denies",
    "gold_per_min",
    "xp_per_min",
    "hero_id",
    "start_time",
    "duration",
    "player_slot",
    "radiant_win",
    "tower_kills",
    "roshan_kills",
    "teamfight_participation",
    "obs_placed",
    "camps_stacked",
    "rune_pickups",
    "firstblood_claimed",
    "stuns",
    "lobby_type",
    "game_mode",
)


class OpenDotaClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 20.0,
        http: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key or None
        self._http = http or httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "dota2-coach/0.3"},
        )
        self._owns_http = http is None
        self.constants = ConstantsClient(self._http, self._base_url)

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def get_match(self, match_id: int) -> dict[str, Any]:
        payload = self._get(f"matches/{match_id}")
        if not isinstance(payload, dict) or not payload.get("players"):
            raise MatchNotFoundError(match_id)
        return payload

    def search_players(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        payload = self._get("search", params={"q": query})
        if not isinstance(payload, list):
            return []
        results: list[dict[str, Any]] = []
        for row in payload[:limit]:
            if not isinstance(row, dict):
                continue
            account_id = row.get("account_id")
            if account_id is None:
                continue
            results.append(
                {
                    "account_id": account_id,
                    "personaname": row.get("personaname") or "Unknown",
                    "avatarfull": row.get("avatarfull"),
                    "similarity": row.get("similarity"),
                }
            )
        return results

    def recent_matches(self, account_id: int, limit: int = 10) -> list[dict[str, Any]]:
        payload = self._get(f"players/{account_id}/recentMatches")
        if not isinstance(payload, list):
            return []
        return [row for row in payload[:limit] if isinstance(row, dict)]

    def get_player(self, account_id: int) -> dict[str, Any]:
        payload = self._get(f"players/{account_id}")
        if not isinstance(payload, dict):
            raise OpenDotaError(f"OpenDota returned no profile for {account_id}.")
        profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else {}
        name = profile.get("personaname") or payload.get("personaname") or str(account_id)
        return {
            "account_id": int(profile.get("account_id") or account_id),
            "personaname": str(name),
            "avatarfull": profile.get("avatarfull"),
            "rank_tier": payload.get("rank_tier"),
        }

    def player_matches(
        self,
        account_id: int,
        days: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params: list[tuple[str, str]] = [
            ("limit", str(limit)),
            ("significant", "0"),
        ]
        if days:
            params.append(("date", str(days)))
        for field in MATCH_PROJECT:
            params.append(("project", field))
        payload = self._get(f"players/{account_id}/matches", params=params)
        if not isinstance(payload, list):
            return []
        return [row for row in payload if isinstance(row, dict)]

    def get_hero_benchmarks(self, hero_id: int) -> dict[str, Any]:
        payload = self._get("benchmarks", params={"hero_id": str(hero_id)})
        return payload if isinstance(payload, dict) else {}

    def request_parse(self, match_id: int) -> dict[str, Any]:
        payload = self._post(f"request/{match_id}")
        return payload if isinstance(payload, dict) else {}

    def parse_job(self, job_id: str | int) -> Any:
        return self._get(f"request/{job_id}")

    def load_constants(self) -> GameConstants:
        try:
            return self.constants.load()
        except httpx.HTTPError:
            return GameConstants()

    def _get(
        self,
        path: str,
        params: dict[str, Any] | list[tuple[str, str]] | None = None,
    ) -> Any:
        if isinstance(params, list):
            query: dict[str, Any] | list[tuple[str, str]] = list(params)
            if self._api_key:
                query.append(("api_key", self._api_key))
        else:
            query = dict(params or {})
            if self._api_key:
                query["api_key"] = self._api_key
        try:
            response = self._http.get(f"{self._base_url}/{path}", params=query)
        except httpx.HTTPError as exc:
            raise OpenDotaError(f"OpenDota request failed: {exc}") from exc
        if response.status_code == 404:
            if path.startswith("matches/"):
                match_id = int(path.split("/")[1])
                raise MatchNotFoundError(match_id)
            if path.startswith("request/"):
                return None
            raise OpenDotaError(f"OpenDota returned 404 for {path}.")
        if response.status_code >= 400:
            raise OpenDotaError(
                f"OpenDota returned {response.status_code} for {path}."
            )
        return response.json()

    def _post(self, path: str) -> Any:
        query: dict[str, Any] = {}
        if self._api_key:
            query["api_key"] = self._api_key
        try:
            response = self._http.post(f"{self._base_url}/{path}", params=query)
        except httpx.HTTPError as exc:
            raise OpenDotaError(f"OpenDota request failed: {exc}") from exc
        if response.status_code == 404 and path.startswith("request/"):
            return None
        if response.status_code >= 400:
            raise OpenDotaError(
                f"OpenDota returned {response.status_code} for POST {path}."
            )
        if not response.content:
            return {}
        return response.json()
