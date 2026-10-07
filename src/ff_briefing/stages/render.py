import os
import tempfile
from datetime import date
from pathlib import Path

from ff_briefing.config import Config
from ff_briefing.render.converter import render_html
from ff_briefing.rundir import RunDir


def _write_atomic(target: Path, text: str) -> None:
    # briefing.html is the idempotence skip marker, so it must never exist half-written.
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(text)
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def run(config: Config, run_dir: RunDir, today: date) -> None:
    markdown = run_dir.require(run_dir.briefing_md, "synthesize").read_text(encoding="utf-8")
    page = render_html(markdown, f"Fantasy briefing for {today.isoformat()}")
    _write_atomic(run_dir.briefing_html, page)
