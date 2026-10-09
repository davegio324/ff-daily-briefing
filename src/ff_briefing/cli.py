import argparse
import logging
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from ff_briefing.config import load_config
from ff_briefing.errors import BriefingError
from ff_briefing.pipeline import STAGES, run_pipeline, run_stage


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ff-briefing")
    parser.add_argument("--config", type=Path, default=Path("config.toml"))
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run the whole pipeline")
    run.add_argument("--force", action="store_true", help="rerun even if today's briefing exists")
    for name in STAGES:
        commands.add_parser(name, help=f"run only the {name} stage")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S", stream=sys.stderr
    )
    today = date.today()
    try:
        config = load_config(args.config)
        if args.command == "run":
            if not run_pipeline(config, args.data_dir, today, force=args.force):
                print(f"briefing for {today.isoformat()} already exists; use --force to rerun")
        else:
            run_stage(args.command, config, args.data_dir, today)
    except BriefingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
