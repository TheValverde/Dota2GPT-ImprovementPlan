# Dota 2 Coach docs

Overlay companion for post-game coaching and a fantasy point board.

- [Setup](setup.md)
- [Architecture](architecture.md)
- [Fantasy scoring](fantasy.md)
- [HTTP API](api.md)
- [Proposed next upgrades](proposals.md) (shipped P4/P5/P6/P9 vs remaining P7/P8/P10)

## Panels

**Coach.** Look up a player, pick a match, or paste an account ID and use **Coach latest parsed**. The brief includes lane opponents, a compact game timeline (towers, Roshan, fights, gold), and who the focus player actually cast spells on. Unparsed matches can request a parse, then re-analyze.

**Fantasy.** Track any number of accounts. Totals, averages, and per-match points over a span of days, weeks, months, or last N matches. Optional ranked-only and hide-turbo filters. Selecting a player also scores everyone in their ranked lobbies (duo plus the rest of the field) and requests parses for unparsed replays.
