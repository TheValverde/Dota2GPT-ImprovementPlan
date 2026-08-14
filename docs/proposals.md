# What we have, and what we can still do with OpenDota

Pitches below are limited to **OpenDota HTTP + data we already store**. In-game overlays, Steam-folder sniffing, and window opacity are out of scope.

OpenDota checked against live responses and [the public API](https://docs.opendota.com/): `GET /matches/{id}`, `GET /players/{id}/matches` (`project`, `date`, `limit`, `lobby_type`, `game_mode`, `significant`), `GET /benchmarks?hero_id=`, `POST /request/{match_id}`, `GET /request/{jobId}`, `GET /constants/*`.

## What the app does today

Local companion window. Dota does not see it. No live lobby, no draft.

**Coach.** `GET /matches/{match_id}` plus constants. The brief includes KDA, GPM/XPM, items, an inferred assignment (Safe core / Safe support / Mid / Offlane / Off support / Jungle / Roam from `lane_role`, farm, and wards), lane opponents (safelane vs enemy offlane, using parsed `lane` for the map side), an opening clock (focus wards, courier snipes, early hero kills, first towers), the other lanes in that window, a lane swing (gold/XP/CS vs the opponent after early kills, plus that opponent's first kill and items), a compact macro (towers, Roshan, teamfights, gold swing), who the focus player actually cast spells on, and OpenDota benchmarks (`{ raw, pct }` from the match, or interpolated from `GET /benchmarks?hero_id=` when the replay is unparsed). The LLM is told to coach that assignment, walk the game in time order, treat pre-lane vision plus courier kills plus lane kills as one play when they sit in that order, treat early lane kills as a swing (what they bought, whether the opponent ever became a hero), and not treat overlapping disables (Grip plus Enfeeble on the same target) as a leak. Percentiles are a hero-wide curve, not a medal bracket. If `version` is missing, the overlay can `POST /request/{match_id}`, poll `GET /request/{jobId}`, then re-analyze. **Coach latest parsed** scans `GET /players/{id}/recentMatches` for a row with `version`, then `GET /players/{id}/matches?project=version` over the last 50 games if recent games are all unparsed.

**Fantasy.** `GET /players/{id}/matches` with `significant=0` and a projected field list, including `lobby_type` and `game_mode`. Scores with one hardcoded formula. Span is local filtering of the SQLite cache. Ranked-only (`lobby_type` 5/6/7) and hide-turbo (`game_mode` 23) checkboxes filter cached rows. Selecting a player builds a ranked field from `GET /matches/{id}` for those ranked games: same-lobby fantasy points for the duo (most games as teammate) and everyone else. Unparsed ranked replays are submitted with `POST /request/{match_id}` (cap 10 per pass). Refresh is still manual.

**Not in the API (so we will not pitch them):**

- Valve ranked role queue (pos 1-5). OpenDota has `lane_role` 1-4 and `is_roaming`, not "queued as 4".
- Same-rank-only percentiles. `GET /benchmarks?hero_id=` is a **hero-wide** curve. Match `benchmarks.pct` is the same idea (where this game sits on that hero's distribution), not "Ancient 5 only".
- Live game events. `GET /live` is pro/top games, not your client.

## Shipped

### P4. Coach from lane and farm, not a fake pos 1-5

Inferred labels use `lane_role`, `is_roaming`, last hits, GPM, and observer wards. The prompt coaches that label. It does not print Valve pos 1-5. Lane opponents are the other team's **opposite** role on the same map side: safelane vs offlane. Same `lane_role` on the other team is the opposite lane. Parsed matches use `lane` (1 bottom, 2 mid, 3 top) as the physical side.

### P5. OpenDota benchmarks in the brief

Parsed matches pass `players[].benchmarks`. Unparsed matches interpolate `GET /benchmarks?hero_id=`. The overlay shows percentile plus raw value, with a note that the curve is hero-wide.

### P6. Request a parse, then reload

Unparsed coach reports show **Request parse**. That hits `POST /request/{match_id}` (OpenDota counts this as 10 rate-limit calls), polls `GET /request/{jobId}` for about 60 seconds, then re-analyzes. Valve replays usually expire after about 10 days.

### P9. Filter ranked / drop turbo

Fantasy checkboxes: Ranked only (`lobby_type` 5/6/7) and Hide turbo (`game_mode` 23). Filters apply to the SQLite cache for the current span.

## Still open

### P7. Recalculate fantasy with different weights

**API:** none. Match stats are already in SQLite (`kills`, `deaths`, `gpm`, …).

**Would mean:** presets (OpenDota, OpenDota+assists which we use now) and a numbers table. Re-sum the current span. No re-download unless a field was never projected.

### P8. Export the current span

**API:** none. Dump cache.

**Would mean:** CSV of roster + match_id + hero + KDA + points + `start_time` for the active span.

### P10. Poll for new games

**API:** `GET /players/{id}/recentMatches` or `GET /players/{id}/matches?limit=1`. Compare `match_id` to cache.

**Would mean:** a timer while the app is open. New ID → score → update the row. Delay is "OpenDota ingested the match", not live. Rate limit: ~60 req/min without a key. A 10-player roster every 2 minutes is fine. A 50-player roster every 30 seconds is not.

## Cut (not OpenDota)

| Old ID | Why it is cut |
| --- | --- |
| P1 in-game overlay | Needs Overwolf or Valve GSI. Not this API. |
| P2 auto Steam account | Reads local Steam files. OpenDota cannot tell whose PC this is. |
| P3 opacity / click-through | Window manager. No extra match data. |
