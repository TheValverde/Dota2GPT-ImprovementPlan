from __future__ import annotations

import argparse
import json
import sys

import uvicorn

from dota2_coach.config import get_settings
from dota2_coach.desktop import launch_desktop
from dota2_coach.errors import CoachError
from dota2_coach.pipeline import AnalysisPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dota 2 overlay: match coach and fantasy tracker."
    )
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("desktop", help="Launch the overlay window (default)")
    sub.add_parser("serve", help="Run the HTTP server without a window")

    analyze = sub.add_parser("analyze", help="Print a coaching report as JSON")
    analyze.add_argument("--player", required=True, help="Persona name or account ID")
    analyze.add_argument("--match", required=True, type=int, dest="match_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    command = args.command or "desktop"

    if command == "desktop":
        return launch_desktop(
            settings,
            host=args.host or "127.0.0.1",
            port=args.port,
        )

    if command == "serve":
        uvicorn.run(
            "dota2_coach.api.app:create_app",
            factory=True,
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
