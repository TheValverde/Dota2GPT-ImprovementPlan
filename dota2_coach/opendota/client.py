from __future__ import annotations

from typing import Any

import httpx

from dota2_coach.errors import MatchNotFoundError, OpenDotaError
from dota2_coach.opendota.constants import ConstantsClient, GameConstants


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
            headers={"User-Agent": "dota2-coach/0.2"},
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

    def load_constants(self) -> GameConstants:
        try:
            return self.constants.load()
        except httpx.HTTPError:
            return GameConstants()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
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
            raise OpenDotaError(f"OpenDota returned 404 for {path}.")
        if response.status_code >= 400:
            raise OpenDotaError(
                f"OpenDota returned {response.status_code} for {path}."
            )
        return response.json()
