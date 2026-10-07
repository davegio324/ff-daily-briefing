from datetime import date
from pathlib import Path

import pytest

from ff_briefing.config import Config
from ff_briefing.render.converter import RenderError
from ff_briefing.rundir import MissingInputError, RunDir
from ff_briefing.stages import render

TODAY = date(2026, 10, 7)
CONFIG = Config(sleeper_username="eli", source_urls=[])


def _run_dir(tmp_path: Path, markdown: str | None) -> RunDir:
    run_dir = RunDir(tmp_path)
    if markdown is not None:
        run_dir.briefing_md.write_text(markdown, encoding="utf-8")
    return run_dir


def test_writes_rendered_briefing_with_date_in_title(tmp_path: Path) -> None:
    run_dir = _run_dir(tmp_path, "## Sunday Funday\n\n- start Kelce\n")

    render.run(CONFIG, run_dir, TODAY)

    out = run_dir.briefing_html.read_text(encoding="utf-8")
    assert "<h2>Sunday Funday</h2>" in out
    assert "<title>Fantasy briefing for 2026-10-07</title>" in out


def test_empty_markdown_raises_and_writes_nothing(tmp_path: Path) -> None:
    run_dir = _run_dir(tmp_path, "  \n")

    with pytest.raises(RenderError):
        render.run(CONFIG, run_dir, TODAY)

    assert not run_dir.briefing_html.exists()
    assert [p.name for p in tmp_path.iterdir()] == ["briefing.md"]


def test_failed_render_leaves_existing_briefing_untouched(tmp_path: Path) -> None:
    run_dir = _run_dir(tmp_path, "")
    run_dir.briefing_html.write_text("previous", encoding="utf-8")

    with pytest.raises(RenderError):
        render.run(CONFIG, run_dir, TODAY)

    assert run_dir.briefing_html.read_text(encoding="utf-8") == "previous"


def test_missing_markdown_raises_error_naming_expected_file(tmp_path: Path) -> None:
    run_dir = _run_dir(tmp_path, None)

    with pytest.raises(MissingInputError, match="briefing.md"):
        render.run(CONFIG, run_dir, TODAY)

    assert not run_dir.briefing_html.exists()


def test_rerun_replaces_existing_briefing(tmp_path: Path) -> None:
    run_dir = _run_dir(tmp_path, "first version")
    render.run(CONFIG, run_dir, TODAY)

    run_dir.briefing_md.write_text("second version", encoding="utf-8")
    render.run(CONFIG, run_dir, TODAY)

    out = run_dir.briefing_html.read_text(encoding="utf-8")
    assert "second version" in out and "first version" not in out
    assert sorted(p.name for p in tmp_path.iterdir()) == ["briefing.html", "briefing.md"]
