FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    HOST=0.0.0.0 \
    PORT=8765

COPY pyproject.toml uv.lock README.md ./
COPY dota2_coach ./dota2_coach
COPY main.py ./

RUN uv sync --frozen --no-dev

EXPOSE 8765

CMD ["python", "main.py", "serve"]
