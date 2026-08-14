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

## Fantasy

Span query: `amount` (1-365) and `unit` (`days`, `weeks`, `months`, `matches`).

### `GET /api/fantasy/roster`

Leaderboard for the current span.

### `POST /api/fantasy/roster`

```json
{ "account_id": 111, "amount": 7, "unit": "days" }
```

Adds or refreshes that account.

### `DELETE /api/fantasy/roster/{account_id}`

### `GET /api/fantasy/players/{account_id}`

Per-match points for the span.

### `POST /api/fantasy/refresh`

```json
{ "account_id": null, "amount": 20, "unit": "matches" }
```

`account_id` omitted refreshes the whole roster.
