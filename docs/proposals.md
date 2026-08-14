# What we have, and what we can still do with OpenDota

Pitches below are limited to **OpenDota HTTP + data we already store**. In-game overlays, Steam-folder sniffing, and window opacity are out of scope.

OpenDota checked against live responses and [the public API](https://docs.opendota.com/): `GET /matches/{id}`, `GET /players/{id}/matches` (`project`, `date`, `limit`, `lobby_type`, `game_mode`, `significant`), `GET /benchmarks?hero_id=`, `POST /request/{match_id}`, `GET /request/{jobId}`, `GET /constants/*`.

## What the app does today

Local companion window. Dota does not see it. No live lobby, no draft.

**Coach.** `GET /matches/{match_id}` plus constants. We keep KDA, GPM/XPM, lane (`lane_role` mapped to Safe/Mid/Off/Jungle), items, and a few parse fields if present. We send that to an LLM. We **do not** pass `players[].benchmarks`, even though a parsed match returns them as `{ raw, pct }` per stat (confirmed on a live parsed match: `gold_per_min.pct` etc.).

**Fantasy.** `GET /players/{id}/matches` with `significant=0` (turbo and unranked included) and a projected field list. Scores with one hardcoded formula. Span is local filtering of the SQLite cache. Refresh is manual.

**Not in the API (so we will not pitch them):**

- Valve ranked role queue (pos 1-5). OpenDota has `lane_role` 1-4 and `is_roaming`, not "queued as 4".
- Same-rank-only percentiles. `GET /benchmarks?hero_id=` is a **hero-wide** curve. Match `benchmarks.pct` is the same idea (where this game sits on that hero's distribution), not "Ancient 5 only".
- Live game events. `GET /live` is pro/top games, not your client.

## Feasible pitches

### P4. Coach from lane and farm, not a fake pos 1-5

**API:** `lane_role`, `lane`, `is_roaming`, `last_hits`, `gold_per_min`, `obs_placed` on `GET /matches/{id}` (parsed). We already map `lane_role` to a lane name.

**Would mean:** label the player as something like "safe core", "safe support", "mid", "off", "roam" using those fields (high LH/GPM on safe lane vs high obs / low farm). Change the prompt to that label. We cannot print "you queued pos 4" because OpenDota does not expose that.

### P5. Put OpenDota benchmarks in the brief

**API:** parsed `GET /matches/{id}` already includes `players[].benchmarks` (`gold_per_min`, `xp_per_min`, `kills_per_min`, `last_hits_per_min`, `hero_damage_per_min`, `tower_damage`, … each `{ raw, pct }`). If the match is unparsed, `GET /benchmarks?hero_id=` returns the percentile curve and we interpolate GPM/XPM/LH ourselves.

**Would mean:** the LLM sees "GPM 24th percentile on this hero", not just "470 GPM". Honest limit: hero population, not your medal.

### P6. Request a parse, then reload

**API:** `POST /request/{match_id}` (OpenDota counts this as **10** rate-limit calls), then `GET /request/{jobId}`, then `GET /matches/{id}` again. Parsed rows get `version`, stuns, teamfight %, obs, stacks, runes, `benchmarks`.

**Would mean:** a button when `version` is missing. Wait/poll, then re-coach and re-score. Can take minutes. Fresh pubs often need this or fantasy wards/stuns stay at 0.

### P7. Recalculate fantasy with different weights

**API:** none. Match stats are already in SQLite (`kills`, `deaths`, `gpm`, …).

**Would mean:** presets (OpenDota, OpenDota+assists which we use now) and a numbers table. Re-sum the current span. No re-download unless a field was never projected.

### P8. Export the current span

**API:** none. Dump cache.

**Would mean:** CSV of roster + match_id + hero + KDA + points + `start_time` for the active span.

### P9. Filter ranked / drop turbo

**API fields we already project:** `lobby_type`, `game_mode`. Constants: ranked is `lobby_type` 7 (also 5/6 legacy). Turbo is `game_mode` 23. OpenDota also accepts query `significant=1`, `lobby_type=7`, `game_mode=22` on `GET /players/{id}/matches`.

**Would mean:** checkboxes on Fantasy. Filter cached rows (and optionally refetch with those query params). Turbo 20-kill games stop beating ranked 45-minute games. Highest-leverage small change.

### P10. Poll for new games

**API:** `GET /players/{id}/recentMatches` or `GET /players/{id}/matches?limit=1`. Compare `match_id` to cache.

**Would mean:** a timer while the app is open. New ID → score → update the row. Delay is "OpenDota ingested the match", not live. Rate limit: ~60 req/min without a key. A 10-player roster every 2 minutes is fine. A 50-player roster every 30 seconds is not.

## Cut (not OpenDota)

| Old ID | Why it is cut |
| --- | --- |
| P1 in-game overlay | Needs Overwolf or Valve GSI. Not this API. |
| P2 auto Steam account | Reads local Steam files. OpenDota cannot tell whose PC this is. |
| P3 opacity / click-through | Window manager. No extra match data. |

## If you only pick a few

**P9, P5, P6, P4.** P9 is filter math. P5 is fields we already download and throw away. P6 is the official parse endpoint. P4 is `lane_role` plus farm/ward heuristics.

Send IDs, for example `approve P9 P5 P6`.
