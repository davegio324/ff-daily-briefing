import logging
import subprocess
from collections.abc import Callable
from datetime import date
from pathlib import Path

from ff_briefing.config import Config
from ff_briefing.errors import BriefingError
from ff_briefing.rundir import RunDir

Opener = Callable[[Path], None]


log = logging.getLogger("ff_briefing")


class DeliveryError(BriefingError):
    pass


def open_in_browser(path: Path) -> None:
    # Absolute so it works regardless of the launchd working directory.
    result = subprocess.run(["open", str(path.resolve())], check=False)
    if result.returncode != 0:
        raise DeliveryError(f"`open` exited with status {result.returncode} for {path}")


def deliver(html_path: Path, opener: Opener | None = None) -> None:
    if not html_path.is_file():
        raise DeliveryError(f"cannot deliver: briefing HTML not found at {html_path}")
    log.info("deliver: opening %s in the default browser", html_path)
    # Resolved at call time so pipeline tests can monkeypatch open_in_browser.
    (opener or open_in_browser)(html_path)


def run(config: Config, run_dir: RunDir, today: date) -> None:
    deliver(run_dir.briefing_html)
