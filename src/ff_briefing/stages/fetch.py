import json
import logging
from datetime import date

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir
from ff_briefing.sleeper.client import HttpSleeperClient, SleeperClient
from ff_briefing.sleeper.fetch import fetch_sleeper
from ff_briefing.sources.fetch import Get
from ff_briefing.stages.sources import fetch_sources

log = logging.getLogger("ff_briefing")


def _fetch_sleeper(config: Config, run_dir: RunDir, client: SleeperClient | None = None) -> None:
    # Fetch completes before any write so a failure leaves no sleeper.json behind.
    log.info("fetch: asking Sleeper for %s's leagues and rosters", config.sleeper_username)
    data = fetch_sleeper(config.sleeper_username, client or HttpSleeperClient())
    log.info(
        "fetch: Sleeper returned %d leagues: %s",
        len(data["leagues"]),
        ", ".join(league["name"] for league in data["leagues"]),
    )
    run_dir.sleeper_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _fetch_sources(config: Config, run_dir: RunDir, get: Get | None = None) -> None:
    log.info("fetch: fetching %d web sources", len(config.source_urls))
    data = fetch_sources(config.source_urls, get)
    log.info(
        "fetch: %d items from sources, %d sources skipped", len(data["items"]), len(data["notes"])
    )
    for note in data["notes"]:
        log.warning("fetch: skipped %s (%s)", note["source_url"], note["reason"])
    run_dir.sources_json.write_text(json.dumps(data, indent=2), encoding="utf-8")


def run(config: Config, run_dir: RunDir, today: date) -> None:
    _fetch_sleeper(config, run_dir)
    _fetch_sources(config, run_dir)
