from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Protocol

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir, run_dir_for
from ff_briefing.stages import deliver, fetch, render, synthesize


class StageFn(Protocol):
    def __call__(self, config: Config, run_dir: RunDir, today: date) -> None: ...


STAGES: Mapping[str, StageFn] = {
    "fetch": fetch.run,
    "synthesize": synthesize.run,
    "render": render.run,
    "deliver": deliver.run,
}


def run_stage(
    name: str,
    config: Config,
    data_dir: Path,
    today: date,
    stages: Mapping[str, StageFn] = STAGES,
) -> None:
    stages[name](config, run_dir_for(data_dir, today), today)


def run_pipeline(
    config: Config,
    data_dir: Path,
    today: date,
    force: bool = False,
    stages: Mapping[str, StageFn] = STAGES,
) -> bool:
    """Run every stage in order; return False when today's briefing already exists."""
    run_dir = run_dir_for(data_dir, today)
    if run_dir.briefing_html.exists() and not force:
        return False
    for stage in stages.values():
        stage(config, run_dir, today)
    return True
