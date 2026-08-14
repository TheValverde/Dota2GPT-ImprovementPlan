# Dota 2 Coach

Desktop CustomTkinter prototype from 2023, rebuilt as a local web app.

Paste a player name (or OpenDota account ID) and a match ID. The app loads the match from [OpenDota](https://www.opendota.com/), trims it into a coaching brief with hero and item names, then asks an LLM for a structured improvement plan.

## Quick start

```bash
cp .env.example .env
# set OPENAI_API_KEY in .env

uv sync --group dev
uv run dota2-coach serve
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

One-shot CLI:

```bash
uv run dota2-coach analyze --player YourName --match 1234567890
```

Docker:

```bash
cp .env.example .env
docker compose up --build
```

The HTTP API listens on **8765** so it stays off the usual 8000/8080 crowding.

## What changed

The original `main.py` was a single Tkinter script using the old `openai.ChatCompletion` API, `gpt-3.5-turbo`, and raw hero IDs. That path blocked the UI, dumped the whole answer into a label, and stored the key in `config.ini`.

This revision splits OpenDota, prompting, and HTTP into modules, uses the current OpenAI client with structured output, and serves a small web UI. Details live in [docs](docs/index.md).
