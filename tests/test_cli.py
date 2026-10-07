from datetime import date
from pathlib import Path
from typing import Any

import pytest

from ff_briefing import cli
from ff_briefing.config import Config, ConfigError
from ff_briefing.errors import BriefingError
from ff_briefing.rundir import MissingInputError


class Calls:
    def __init__(self) -> None:
        self.pipeline: list[dict[str, Any]] = []
        self.stage: list[dict[str, Any]] = []


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> Calls:
    recorded = Calls()

    def fake_pipeline(
        config: Config, data_dir: Path, today: date, force: bool = False, **_: Any
    ) -> bool:
        recorded.pipeline.append(
            {"config": config, "data_dir": data_dir, "today": today, "force": force}
        )
        return True

    def fake_stage(name: str, config: Config, data_dir: Path, today: date, **_: Any) -> None:
        recorded.stage.append(
            {"name": name, "config": config, "data_dir": data_dir, "today": today}
        )

    monkeypatch.setattr(cli, "run_pipeline", fake_pipeline)
    monkeypatch.setattr(cli, "run_stage", fake_stage)
    return recorded


def test_run_passes_loaded_config_data_dir_and_todays_date_to_the_pipeline(
    calls: Calls, config_file: Path, tmp_path: Path
) -> None:
    code = cli.main(["--config", str(config_file), "--data-dir", str(tmp_path / "d"), "run"])

    assert code == 0
    (call,) = calls.pipeline
    assert call["config"] == Config(sleeper_username="eli", source_urls=["https://a.test/feed"])
    assert call["data_dir"] == tmp_path / "d"
    assert call["today"] == date.today()
    assert call["force"] is False


def test_run_force_flag_reaches_the_pipeline(calls: Calls, config_file: Path) -> None:
    cli.main(["--config", str(config_file), "run", "--force"])

    assert calls.pipeline[0]["force"] is True


def test_config_path_defaults_to_config_toml_in_the_working_directory(
    calls: Calls, config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(config_file.parent)

    assert cli.main(["run"]) == 0
    assert calls.pipeline[0]["config"].sleeper_username == "eli"


def test_data_dir_defaults_to_data(
    calls: Calls, config_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(config_file.parent)

    cli.main(["run"])

    assert calls.pipeline[0]["data_dir"] == Path("data")


def test_run_reports_skip_on_stdout_and_exits_zero_when_pipeline_skipped(
    monkeypatch: pytest.MonkeyPatch, config_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(cli, "run_pipeline", lambda *a, **k: False)

    code = cli.main(["--config", str(config_file), "run"])

    assert code == 0
    assert "already" in capsys.readouterr().out


@pytest.mark.parametrize("stage", ["fetch", "synthesize", "render", "deliver"])
def test_stage_subcommand_runs_only_that_stage(
    calls: Calls, config_file: Path, tmp_path: Path, stage: str
) -> None:
    code = cli.main(["--config", str(config_file), "--data-dir", str(tmp_path), stage])

    assert code == 0
    assert calls.pipeline == []
    (call,) = calls.stage
    assert call["name"] == stage
    assert call["data_dir"] == tmp_path
    assert call["today"] == date.today()
    assert call["config"].sleeper_username == "eli"


@pytest.mark.parametrize(
    "error", [ConfigError("bad config"), MissingInputError("missing briefing.md")]
)
def test_any_briefing_error_prints_error_line_to_stderr_and_exits_one(
    monkeypatch: pytest.MonkeyPatch,
    config_file: Path,
    capsys: pytest.CaptureFixture[str],
    error: BriefingError,
) -> None:
    def boom(*_: Any, **__: Any) -> None:
        raise error

    monkeypatch.setattr(cli, "run_stage", boom)

    code = cli.main(["--config", str(config_file), "render"])

    captured = capsys.readouterr()
    assert code == 1
    assert captured.err.strip() == f"error: {error}"
    assert "Traceback" not in captured.err


def test_missing_config_file_exits_one_with_error_naming_the_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.main(["--config", str(tmp_path / "nope.toml"), "run"])

    err = capsys.readouterr().err
    assert code == 1
    assert err.startswith("error: ")
    assert "nope.toml" in err
    assert "Traceback" not in err
