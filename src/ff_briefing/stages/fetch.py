import json
from datetime import date

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir


def _fetch_sleeper(config: Config, run_dir: RunDir) -> None:
    run_dir.sleeper_json.write_text(json.dumps({}, indent=2), encoding="utf-8")


def _fetch_sources(config: Config, run_dir: RunDir) -> None:
    run_dir.sources_json.write_text(json.dumps({"sources": []}, indent=2), encoding="utf-8")


def run(config: Config, run_dir: RunDir, today: date) -> None:
    _fetch_sleeper(config, run_dir)
    _fetch_sources(config, run_dir)
