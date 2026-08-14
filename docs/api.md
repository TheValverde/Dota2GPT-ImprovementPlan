# HTTP API

Base URL: `http://127.0.0.1:8765`

Interactive docs: `/docs`

## Coach

### `GET /api/health`

`{ "status": "ok" }`

### `GET /api/players/search?q=`

OpenDota player search. `q` must be at least 2 characters.

### `GET /api/players/{account_id}/recent-matches`

Recent games with hero names.

### `POST /api/analyze`

```json
{ "player": "PersonaName or account id", "match_id": 1234567890 }
```

| Status | When |
| --- | --- |
| 404 | Match missing, or player not in the lobby |
| 503 | `OPENAI_API_KEY` is unset |
| 502 | OpenDota request failed |

### `POST /api/matches/{match_id}/parse`

Submit an OpenDota parse job. Counts as 10 OpenDota calls. Returns `job_id` when queued, or `parsed: true` if `version` is already set.

### `GET /api/matches/{match_id}/parse-status?job_id=`

Poll the parse queue, then re-read the match. `queued` is false when OpenDota has dropped the job. `parsed` is true when `version` is present.

## Fantasy

Span query: `amount` (1-365) and `unit` (`days`, `weeks`, `months`, `matches`).

Optional filters on roster, player card, add, and refresh:

| Param | Meaning |
| --- | --- |
| `ranked_only` | Keep `lobby_type` 5, 6, or 7 |
| `hide_turbo` | Drop `game_mode` 23 |

### `GET /api/fantasy/roster`

Leaderboard for the current span.

### `POST /api/fantasy/roster`

```json
{ "account_id": 111, "amount": 7, "unit": "days", "ranked_only": false, "hide_turbo": true }
```

Adds or refreshes that account.

### `DELETE /api/fantasy/roster/{account_id}`

### `GET /api/fantasy/players/{account_id}`

Per-match points for the span.

### `GET /api/fantasy/players/{account_id}/field`

Ranked lobby comparison for the span. Always `ranked_only`. Respects `hide_turbo`. Scores every named player in those lobbies with the same fantasy formula. `duo` is the teammate with the most shared ranked games (minimum 2).

### `POST /api/fantasy/players/{account_id}/parse-missing`

Submit OpenDota parse jobs for unparsed ranked replays in the span, up to 10 per call.

### `POST /api/fantasy/refresh`

```json
{ "account_id": null, "amount": 20, "unit": "matches", "ranked_only": false, "hide_turbo": false }
```

`account_id` omitted refreshes the whole roster.
