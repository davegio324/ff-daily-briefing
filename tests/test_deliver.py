import subprocess
from pathlib import Path

import pytest

from ff_briefing.errors import BriefingError
from ff_briefing.stages import deliver as deliver_stage
from ff_briefing.stages.deliver import DeliveryError, deliver, open_in_browser


def test_opens_existing_html_file_exactly_once(tmp_path: Path) -> None:
    html = tmp_path / "briefing.html"
    html.write_text("<p>hi</p>", encoding="utf-8")
    opened: list[Path] = []

    deliver(html, opener=opened.append)

    assert opened == [html]


def test_missing_html_file_raises_naming_path_without_opening(tmp_path: Path) -> None:
    missing = tmp_path / "briefing.html"
    opened: list[Path] = []

    with pytest.raises(DeliveryError) as excinfo:
        deliver(missing, opener=opened.append)

    assert str(missing) in str(excinfo.value)
    assert opened == []


def test_delivery_error_is_a_user_facing_briefing_error() -> None:
    assert issubclass(DeliveryError, BriefingError)


def test_nonzero_open_exit_raises_delivery_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    html = tmp_path / "briefing.html"
    monkeypatch.setattr(
        deliver_stage.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, returncode=1),
    )

    with pytest.raises(DeliveryError) as excinfo:
        open_in_browser(html)

    assert str(html) in str(excinfo.value)


def test_open_in_browser_passes_absolute_path_and_succeeds_on_zero_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0)

    monkeypatch.setattr(deliver_stage.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)

    open_in_browser(Path("briefing.html"))

    assert len(calls) == 1
    assert Path(calls[0][-1]).is_absolute()
