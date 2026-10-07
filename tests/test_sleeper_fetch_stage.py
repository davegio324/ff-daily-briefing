import json
from pathlib import Path

import pytest

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir
from ff_briefing.sleeper.client import SleeperError
from ff_briefing.stages.fetch import _fetch_sleeper
from tests.sleeper.fakes import FakeSleeperClient


def _config() -> Config:
    return Config(sleeper_username="eli", source_urls=[])


def test_successful_fetch_persists_sleeper_json_in_run_dir(tmp_path: Path) -> None:
    run_dir = RunDir(tmp_path)

    _fetch_sleeper(_config(), run_dir, FakeSleeperClient())

    data = json.loads(run_dir.sleeper_json.read_text(encoding="utf-8"))
    assert data["username"] == "eli"
    assert [league["league_id"] for league in data["leagues"]] == ["L1", "L2"]


def test_failed_fetch_raises_and_writes_no_sleeper_json(tmp_path: Path) -> None:
    run_dir = RunDir(tmp_path)

    with pytest.raises(SleeperError):
        _fetch_sleeper(_config(), run_dir, FakeSleeperClient(fail_on="get_players"))

    assert not run_dir.sleeper_json.exists()
