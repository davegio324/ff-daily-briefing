from datetime import date

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir


def run(config: Config, run_dir: RunDir, today: date) -> None:
    run_dir.require(run_dir.briefing_html, "render")
