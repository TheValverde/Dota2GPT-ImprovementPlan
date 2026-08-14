# Dota 2 Coach

Desktop overlay for Dota 2 match coaching and fantasy tracking. Think DotaPlus-style companion window: dark chrome, always-on-top pin, Coach and Fantasy tabs.

## Quick start

```bash
cp .env.example .env
# set OPENAI_API_KEY for the coach tab

uv sync --group dev
uv run dota2-coach
```

That launches the overlay window. Pin keeps it above other apps.

Fantasy tracking does not need an OpenAI key. Add as many OpenDota accounts as you want, then slice the board by days, weeks, months, or last N matches. Ranked only and Hide turbo filter the cached span. Open a player to compare ranked fantasy points against their duo and everyone else in those lobbies.

Paste an OpenDota account ID on the Coach tab and hit **Coach latest parsed** to skip picking a match. Same from the CLI:

```bash
uv run dota2-coach analyze --player 286841060
```

HTTP-only (Docker or a browser):

```bash
uv run dota2-coach serve
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

## Docs

- [Setup](docs/setup.md)
- [Architecture](docs/architecture.md)
- [Fantasy scoring](docs/fantasy.md)
- [HTTP API](docs/api.md)
- [Proposed next upgrades](docs/proposals.md)
