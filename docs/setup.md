# Setup

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key
- Optional: an [OpenDota API key](https://www.opendota.com/api-keys) if you hit the public rate limit

## Local install

```bash
cp .env.example .env
```

Set at least `OPENAI_API_KEY`. Optional knobs:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model used for structured coaching |
| `OPENDOTA_API_KEY` | empty | Higher OpenDota rate limits |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8765` | HTTP port |

Then:

```bash
uv sync --group dev
uv run dota2-coach serve
```

The app is at `http://127.0.0.1:8765`. Tests:

```bash
uv run pytest
```

## Docker

Port **8765** is the documented listen port. This environment had no `ufw` and no running containers, so nothing else was occupying it. If you run `ufw` on the host:

```bash
sudo ufw allow 8765/tcp
sudo ufw reload
```

```bash
cp .env.example .env
docker compose up --build
```

`docker compose` reads `.env` for `OPENAI_API_KEY` and related settings.

## CLI

```bash
uv run dota2-coach analyze --player 111 --match 7000000001
```

`--player` accepts a persona name or a 32-bit OpenDota / Steam account ID.
