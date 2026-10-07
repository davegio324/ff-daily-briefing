import html
from datetime import date

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir


def run(config: Config, run_dir: RunDir, today: date) -> None:
    markdown = run_dir.require(run_dir.briefing_md, "synthesize").read_text(encoding="utf-8")
    run_dir.briefing_html.write_text(
        '<!doctype html>\n<html><head><meta charset="utf-8"><title>Daily briefing</title></head>'
        f"<body><pre>{html.escape(markdown)}</pre></body></html>\n",
        encoding="utf-8",
    )
