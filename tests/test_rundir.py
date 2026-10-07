from datetime import date
from pathlib import Path

import pytest

from ff_briefing.errors import BriefingError
from ff_briefing.rundir import MissingInputError, run_dir_for

DAY = date(2026, 10, 7)


def test_run_dir_is_created_under_data_dir_named_by_iso_date(tmp_path: Path) -> None:
    run_dir = run_dir_for(tmp_path, DAY)

    assert run_dir.path == tmp_path / "2026-10-07"
    assert run_dir.path.is_dir()


def test_run_dir_for_an_existing_directory_keeps_its_files(tmp_path: Path) -> None:
    (tmp_path / "2026-10-07").mkdir()
    (tmp_path / "2026-10-07" / "briefing.md").write_text("keep", encoding="utf-8")

    run_dir = run_dir_for(tmp_path, DAY)

    assert run_dir.briefing_md.read_text(encoding="utf-8") == "keep"


def test_stage_files_live_in_the_run_directory_under_contract_names(tmp_path: Path) -> None:
    run_dir = run_dir_for(tmp_path, DAY)

    assert run_dir.sleeper_json == run_dir.path / "sleeper.json"
    assert run_dir.sources_json == run_dir.path / "sources.json"
    assert run_dir.briefing_md == run_dir.path / "briefing.md"
    assert run_dir.briefing_html == run_dir.path / "briefing.html"


def test_require_returns_the_file_when_it_exists(tmp_path: Path) -> None:
    run_dir = run_dir_for(tmp_path, DAY)
    run_dir.briefing_md.write_text("x", encoding="utf-8")

    assert run_dir.require(run_dir.briefing_md, "synthesize") == run_dir.briefing_md


def test_require_on_a_missing_file_names_the_file_and_producing_stage(tmp_path: Path) -> None:
    run_dir = run_dir_for(tmp_path, DAY)

    with pytest.raises(MissingInputError) as excinfo:
        run_dir.require(run_dir.briefing_md, "synthesize")

    assert "briefing.md" in str(excinfo.value)
    assert "synthesize" in str(excinfo.value)


def test_missing_input_error_is_a_briefing_error() -> None:
    assert issubclass(MissingInputError, BriefingError)
