import json
from datetime import date

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir
from ff_briefing.sleeper.client import HttpSleeperClient, SleeperClient
from ff_briefing.sleeper.fetch import fetch_sleeper
from ff_briefing.sources.fetch import Get
from ff_briefing.stages.sources import fetch_sources


def _fetch_sleeper(config: Config, run_dir: RunDir, client: SleeperClient | None = None) -> None:
    # Fetch completes before any write so a failure leaves no sleeper.json behind.
    data = fetch_sleeper(config.sleeper_username, client or HttpSleeperClient())
    run_dir.sleeper_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _fetch_sources(config: Config, run_dir: RunDir, get: Get | None = None) -> None:
    data = fetch_sources(config.source_urls, get)
    run_dir.sources_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run(config: Config, run_dir: RunDir, today: date) -> None:
    _fetch_sleeper(config, run_dir)
    _fetch_sources(config, run_dir)
