# Setup

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A desktop WebView (Windows Edge WebView2, macOS WebKit, Linux WebKitGTK or Qt)
- An OpenAI API key for the Coach tab
- Optional: an [OpenDota API key](https://www.opendota.com/api-keys)

## Overlay

```bash
cp .env.example .env
uv sync --group dev
uv run dota2-coach
```

`uv run dota2-coach desktop` is the same command.

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | empty | Coach tab |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model |
| `OPENDOTA_API_KEY` | empty | Higher OpenDota rate limits |
| `DOTA2_COACH_DATA` | OS app-data dir | SQLite roster cache |
| `HOST` | `0.0.0.0` for `serve` | Bind address |
| `PORT` | `8765` | HTTP port |

Roster data lives in `%APPDATA%\Dota2Coach` on Windows or `~/.local/share/dota2-coach` on Linux/macOS.

## HTTP only

```bash
uv run dota2-coach serve
uv run pytest
```

## Docker

Docker serves the HTTP UI, not the native overlay. Port **8765**.

```bash
cp .env.example .env
docker compose up --build
```

If the host uses `ufw`:

```bash
sudo ufw allow 8765/tcp
sudo ufw reload
```
