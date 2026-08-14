# HTTP API

Base URL: `http://127.0.0.1:8765`

Interactive docs: `/docs`

## `GET /api/health`

Liveness check. Returns `{ "status": "ok" }`.

## `GET /api/players/search?q=`

OpenDota player search. `q` must be at least 2 characters.

## `GET /api/players/{account_id}/recent-matches`

Recent games for an account, with hero names resolved.

## `POST /api/analyze`

```json
{
  "player": "PersonaName or account id",
  "match_id": 1234567890
}
```

`200` body:

```json
{
  "brief": { "match_id": 123, "focus_player": {}, "scoreboard": [] },
  "report": {
    "headline": "",
    "match_read": "",
    "grade": "B",
    "kda_context": "",
    "strengths": [],
    "mistakes": [],
    "focus_areas": [],
    "next_three_games": []
  }
}
```

| Status | When |
| --- | --- |
| 404 | Match missing, or player not in the lobby |
| 503 | `OPENAI_API_KEY` is unset |
| 502 | OpenDota request failed |
