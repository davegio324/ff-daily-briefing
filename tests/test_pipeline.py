import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import pytest

from ff_briefing.config import Config
from ff_briefing.pipeline import STAGES, StageFn, run_pipeline, run_stage
from ff_briefing.rundir import MissingInputError, RunDir

DAY = date(2026, 10, 7)
CONFIG = Config(sleeper_username="eli", source_urls=[])
FILES = ["sleeper.json", "sources.json", "briefing.md", "briefing.html"]


class Recorder:
    """Fake stages that write the real contract files, tagged per recorder instance."""

    instances = 0

    def __init__(self) -> None:
        Recorder.instances += 1
        self.run_id = Recorder.instances
        self.calls: list[str] = []

    def _tag(self, name: str) -> str:
        self.calls.append(name)
        return f"{name}-run{self.run_id}"

    def fetch(self, config: Config, run_dir: RunDir, today: date) -> None:
        tag = self._tag("fetch")
        run_dir.sleeper_json.write_text(json.dumps({"tag": tag}), encoding="utf-8")
        run_dir.sources_json.write_text(json.dumps({"tag": tag}), encoding="utf-8")

    def synthesize(self, config: Config, run_dir: RunDir, today: date) -> None:
        tag = self._tag("synthesize")
        run_dir.require(run_dir.sleeper_json, "fetch")
        run_dir.require(run_dir.sources_json, "fetch")
        run_dir.briefing_md.write_text(f"# {tag}", encoding="utf-8")

    def render(self, config: Config, run_dir: RunDir, today: date) -> None:
        tag = self._tag("render")
        md = run_dir.require(run_dir.briefing_md, "synthesize").read_text(encoding="utf-8")
        run_dir.briefing_html.write_text(f"<p>{md} {tag}</p>", encoding="utf-8")

    def deliver(self, config: Config, run_dir: RunDir, today: date) -> None:
        self._tag("deliver")
        run_dir.require(run_dir.briefing_html, "render")

    def stages(self) -> Mapping[str, StageFn]:
        return {
            "fetch": self.fetch,
            "synthesize": self.synthesize,
            "render": self.render,
            "deliver": self.deliver,
        }


def day_dir(tmp_path: Path) -> Path:
    return tmp_path / "2026-10-07"


def test_registry_lists_stages_in_pipeline_order() -> None:
    assert list(STAGES) == ["fetch", "synthesize", "render", "deliver"]


def test_run_executes_every_stage_in_order_and_leaves_all_files(tmp_path: Path) -> None:
    rec = Recorder()

    ran = run_pipeline(CONFIG, tmp_path, DAY, stages=rec.stages())

    assert ran is True
    assert rec.calls == ["fetch", "synthesize", "render", "deliver"]
    assert sorted(p.name for p in day_dir(tmp_path).iterdir()) == sorted(FILES)


def test_run_skips_and_leaves_bytes_unchanged_when_final_briefing_exists(tmp_path: Path) -> None:
    run_pipeline(CONFIG, tmp_path, DAY, stages=(first := Recorder()).stages())
    before = {n: (day_dir(tmp_path) / n).read_bytes() for n in FILES}
    rec = Recorder()

    ran = run_pipeline(CONFIG, tmp_path, DAY, stages=rec.stages())

    assert ran is False
    assert rec.calls == []
    assert {n: (day_dir(tmp_path) / n).read_bytes() for n in FILES} == before
    assert first.calls


def test_force_reruns_every_stage_and_rewrites_all_files(tmp_path: Path) -> None:
    run_pipeline(CONFIG, tmp_path, DAY, stages=Recorder().stages())
    before = {n: (day_dir(tmp_path) / n).read_bytes() for n in FILES}
    rec = Recorder()

    ran = run_pipeline(CONFIG, tmp_path, DAY, force=True, stages=rec.stages())

    assert ran is True
    assert rec.calls == ["fetch", "synthesize", "render", "deliver"]
    for name in ("sleeper.json", "sources.json", "briefing.md", "briefing.html"):
        assert (day_dir(tmp_path) / name).read_bytes() != before[name], name


def test_run_with_directory_lacking_final_briefing_runs_all_stages(tmp_path: Path) -> None:
    day_dir(tmp_path).mkdir()
    (day_dir(tmp_path) / "briefing.md").write_text("# stale", encoding="utf-8")
    rec = Recorder()

    ran = run_pipeline(CONFIG, tmp_path, DAY, stages=rec.stages())

    assert ran is True
    assert rec.calls == ["fetch", "synthesize", "render", "deliver"]


def test_stage_runs_alone_from_previously_persisted_inputs(tmp_path: Path) -> None:
    run_pipeline(CONFIG, tmp_path, DAY, stages=Recorder().stages())
    rec = Recorder()

    run_stage("synthesize", CONFIG, tmp_path, DAY, stages=rec.stages())

    assert rec.calls == ["synthesize"]
    assert (day_dir(tmp_path) / "briefing.md").read_text(
        encoding="utf-8"
    ) == f"# synthesize-run{rec.run_id}"


def test_stage_runs_even_when_final_briefing_already_exists(tmp_path: Path) -> None:
    run_pipeline(CONFIG, tmp_path, DAY, stages=Recorder().stages())
    rec = Recorder()

    run_stage("render", CONFIG, tmp_path, DAY, stages=rec.stages())

    assert rec.calls == ["render"]


def test_stage_with_missing_input_raises_naming_file_and_producing_stage(tmp_path: Path) -> None:
    rec = Recorder()

    with pytest.raises(MissingInputError) as excinfo:
        run_stage("render", CONFIG, tmp_path, DAY, stages=rec.stages())

    assert "briefing.md" in str(excinfo.value)
    assert "synthesize" in str(excinfo.value)
