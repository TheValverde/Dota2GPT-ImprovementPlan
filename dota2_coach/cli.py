from __future__ import annotations

import argparse
import json
import sys

import uvicorn

from dota2_coach.config import get_settings
from dota2_coach.errors import CoachError
from dota2_coach.pipeline import AnalysisPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dota 2 match coach: web app or one-shot analysis."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Run the local web app")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    analyze = sub.add_parser("analyze", help="Print a coaching report as JSON")
    analyze.add_argument("--player", required=True, help="Persona name or account ID")
    analyze.add_argument("--match", required=True, type=int, dest="match_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()

    if args.command == "serve":
        uvicorn.run(
            "dota2_coach.api.app:app",
            host=args.host or settings.host,
            port=args.port or settings.port,
            reload=False,
        )
        return 0

    pipeline = AnalysisPipeline(settings)
    try:
        brief, report = pipeline.analyze(args.player, args.match_id)
    except CoachError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    payload = {"brief": brief, "report": report.model_dump()}
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
