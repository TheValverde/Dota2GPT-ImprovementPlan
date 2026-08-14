# What we have vs what the pitches actually mean

Nothing in the pitch list is built. This page is the spec for approval.

## What the app does today

It is a **local companion window**, not an in-game overlay. `uv run dota2-coach` opens a frameless desktop window over a local server. Dota 2 does not know it exists. It cannot see your draft, your HUD, or who is in your current lobby unless you type those people in.

### Coach tab

You type a persona name or 32-bit account ID, then a match ID (or pick from that player's recent OpenDota games). The app:

1. Downloads that match from OpenDota.
2. Resolves hero/item names.
3. Builds a compact brief: KDA, GPM/XPM, lane, items, a few wards/stacks/stuns fields if OpenDota parsed the replay, plus the rest of the scoreboard.
4. Sends that brief to an LLM.
5. Shows a structured report: headline, letter grade, KDA context, strengths, leaks, focus areas, next three games.

You must have `OPENAI_API_KEY` for this tab. The model is not told your role as pos 1-5. It is not given rank-peer averages. If OpenDota never parsed the replay, stun/ward/teamfight fields are simply missing and the prompt says not to invent them.

### Fantasy tab

You search OpenDota names (or paste account IDs) and add as many accounts as you want. The roster is stored in a local SQLite file.

You pick a span: N days, weeks, months, or last N matches. Refresh pulls match history from OpenDota and scores each game with a **fixed formula**:

```
3 + 0.3*kills - 0.3*deaths + 0.15*assists + 0.003*(last hits+denies)
+ 0.002*GPM + towers + roshans + 3*teamfight% + 0.5*obs + 0.5*stacks
+ 0.25*runes + 4*first blood + 0.05*stuns
```

The board shows total, average, best/worst, a sparkline, and a per-match list. Click a match to jump to Coach with that ID filled in.

There is no ranked-only filter (`significant=0`, so turbo and unranked count). There is no CSV export. Weights are not editable. The board does not update until you hit Refresh. Unparsed games still get a score, but ward/stun/teamfight terms are zero.

### Window chrome

Title bar with Coach / Fantasy tabs. Pin (always on top), minimize, close. No opacity slider. Clicks always hit the window, not the game underneath.

## Pitches, spelled out

### P1. In-game overlay (Overwolf or Dota GSI)

**Today:** a separate window you alt-tab to after the game.

**Would mean:** while you are in Dota (queue, draft, or match), a panel draws on top of the client and reads live game events. That is what DotaPlus actually is.

This is a different product. It needs Overwolf's SDK or Valve's Game State Integration, plus running Dota. This repo cannot do it with pywebview. High effort, Windows-centric, and Valve has already gutted some draft-intel overlays.

### P2. Auto-detect the local Steam account

**Today:** every Coach lookup starts with you typing a name or account ID.

**Would mean:** on launch, read the Steam install / `loginusers.vdf` / Dota userdata on this machine, map it to a 32-bit OpenDota ID, and prefill "you" as the default player. You would still add other people by search. Fails if Steam is not installed or the profile is private on OpenDota.

### P3. Opacity slider and click-through

**Today:** Pin only toggles always-on-top. The window is fully opaque and fully clickable.

**Would mean:** a slider from ~30% to 100% opacity, plus a "click-through" toggle so mouse clicks pass into Dota while the panel stays visible. Useful if you park it over the scoreboard. Still not a real overlay; it is window-manager chrome on the existing pywebview window.

### P4. Role-aware coaching (pos 1-5)

**Today:** the model sees lane (safe/mid/off/jungle when OpenDota has `lane_role`) and the stats dump. It does not know if you queued as pos 4 or a greedy pos 3. Advice is generic "this player's game."

**Would mean:** you pick a position (or we infer it from lane + farm + wards), and the prompt changes. Pos 5 gets warding, pull timing, save usage. Pos 1 gets item timings and when to leave jungle. Same match, different plan. Does not require live Dota.

### P5. OpenDota peer benchmarks

**Today:** the brief has raw GPM, XPM, wards, damage. The model guesses whether 520 GPM is good.

**Would mean:** pull OpenDota `benchmarks` for that match (percentiles vs same-rank players on that hero) and put "GPM 72nd percentile, obs 20th" into the brief. The grade would be relative to the lobby rank, not vibes. Only works when OpenDota attached benchmarks to the match.

### P6. Request a replay parse when unparsed

**Today:** if OpenDota never parsed the replay, Coach and Fantasy lose stuns, teamfight %, observer wards, stacks, runes. Those terms score as 0. We do not ask OpenDota to parse.

**Would mean:** a "Parse this match" button that POSTs OpenDota's parse job, waits or polls, then re-scores / re-coaches. Parses are rate-limited and can take minutes. Without this, turbo and fresh pubs often look weaker than they were.

### P7. Custom fantasy weights

**Today:** one hardcoded table (OpenDota + 0.15 assists). Every tracked player uses it.

**Would mean:** a small settings panel: presets (OpenDota, Liquipedia/TI with assists, "kills-heavy") plus editable numbers. Recalculate the current span from cached match stats without re-downloading. Needed if your league's sheet does not match OpenDota.

### P8. CSV export of the current span

**Today:** numbers live in the overlay and in SQLite. No file out.

**Would mean:** Export downloads `player, match_id, hero, k/d/a, points, date` for whoever is on the roster and the current span, so you can paste into Google Sheets. No new data; it dumps what Refresh already stored.

### P9. Ranked-only / no-turbo filter

**Today:** history is fetched with `significant=0`, so turbo, unranked, and botches all score. A 12-minute turbo 20-kill game can beat a ranked 45-minute 8-kill game.

**Would mean:** checkboxes on the Fantasy bar: Ranked only, hide Turbo, maybe All Pick only. Filter uses `lobby_type` / `game_mode` already stored on each cached match. Recalculate totals. This is the highest-leverage small fantasy change if you care about "real" games.

### P10. Notify when a tracked player finishes a match

**Today:** the board is stale until you click Refresh. No polling.

**Would mean:** a background timer (every 1-2 minutes) that asks OpenDota for each roster account's latest match ID. If a new one appears, score it, bump totals, and flash the row or a desktop notification. Uses more API quota as the roster grows. Not live in-game; it is "they popped in OpenDota a few minutes after the game."

## Suggested order if you only want useful ones

If this is a post-game companion (what we actually have): **P9, P4, P5, P7, P8**.

If you want it to feel like DotaPlus during a match: **P1** is the real one, and it is a rebuild. P3 is a cheap fake. P2 is quality-of-life either way.

Send IDs to build, for example `approve P9 P4 P5`.
