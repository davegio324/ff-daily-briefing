import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from ff_briefing.config import Config
from ff_briefing.llm.seam import LLMError
from ff_briefing.rundir import MissingInputError, RunDir
from ff_briefing.stages.synthesize import synthesize_with
from ff_briefing.synthesis.prompt import PLACEHOLDER_PROMPT
from tests.fakes import FakeLLMClient

TODAY = date(2026, 10, 7)
CONFIG = Config(sleeper_username="eli", source_urls=[])


def _player(name: str) -> dict[str, Any]:
    return {"name": name, "position": "WR", "team": "KC", "status": "Active", "injury_status": None}


def _league(league_id: str, name: str, roster_player: str, waiver_day: int) -> dict[str, Any]:
    return {
        "league_id": league_id,
        "name": name,
        "scoring_settings": {"rec": 1.0 if league_id == "L1" else 0.5},
        "roster_positions": ["QB", "WR", "BN"],
        "waiver": {"waiver_day_of_week": waiver_day},
        "roster": {"roster_id": 1, "starters": [roster_player], "players": [roster_player]},
        "rostered_player_ids": [roster_player],
    }


SLEEPER: dict[str, Any] = {
    "leagues": [
        _league("L1", "Sunday Funday", "p1", 2),
        _league("L2", "Office League", "p2", 3),
    ],
    "trending": {
        "add": [
            {"player_id": "p3", "count": 90, "available_in": {"L1": True, "L2": False}},
            {"player_id": "p4", "count": 40, "available_in": {"L1": False, "L2": True}},
        ],
        "drop": [],
    },
    "players": {
        "p1": _player("Rostered Alpha"),
        "p2": _player("Rostered Beta"),
        "p3": _player("Pickup Gamma"),
        "p4": _player("Pickup Delta"),
    },
}


def _write(run_dir: RunDir, sleeper: Any = SLEEPER, sources: Any = None) -> None:
    run_dir.sleeper_json.write_text(json.dumps(sleeper), encoding="utf-8")
    if sources is not None:
        run_dir.sources_json.write_text(json.dumps(sources), encoding="utf-8")


def _run(tmp_path: Path, fake: FakeLLMClient, sources: Any = None) -> RunDir:
    run_dir = RunDir(tmp_path)
    _write(run_dir, sources=sources)
    synthesize_with(fake, CONFIG, run_dir, TODAY)
    return run_dir


def test_one_llm_call_covers_both_leagues_with_the_placeholder_prompt(tmp_path: Path) -> None:
    fake = FakeLLMClient()

    _run(tmp_path, fake)

    assert len(fake.calls) == 1
    context, prompt = fake.calls[0]
    assert prompt == PLACEHOLDER_PROMPT
    for expected in ("Sunday Funday", "Office League", "Rostered Alpha", "Rostered Beta"):
        assert expected in context
    assert "2026-10-07" in context


def test_returned_markdown_is_written_verbatim_to_the_briefing_file(tmp_path: Path) -> None:
    run_dir = _run(tmp_path, FakeLLMClient(response="# Hello\n\nbody\n"))

    assert run_dir.briefing_md.read_text(encoding="utf-8") == "# Hello\n\nbody\n"


def test_free_agents_are_limited_to_trending_players_available_in_that_league(
    tmp_path: Path,
) -> None:
    fake = FakeLLMClient()

    _run(tmp_path, fake)

    context = fake.calls[0][0]
    first, second = context.split("## League: Office League")
    assert "Pickup Gamma" in first and "Pickup Delta" not in first
    assert "Pickup Delta" in second and "Pickup Gamma" not in second


def test_llm_failure_propagates_and_no_briefing_is_written(tmp_path: Path) -> None:
    run_dir = RunDir(tmp_path)
    _write(run_dir)

    with pytest.raises(LLMError, match="boom"):
        synthesize_with(FakeLLMClient(error=LLMError("boom")), CONFIG, run_dir, TODAY)

    assert not run_dir.briefing_md.exists()


def test_missing_sleeper_output_fails_naming_the_file_without_calling_the_llm(
    tmp_path: Path,
) -> None:
    fake = FakeLLMClient()

    with pytest.raises(MissingInputError, match="sleeper.json"):
        synthesize_with(fake, CONFIG, RunDir(tmp_path), TODAY)

    assert fake.calls == []


def test_fetched_source_text_and_failure_notes_reach_the_llm_context(tmp_path: Path) -> None:
    fake = FakeLLMClient()
    sources = {
        "items": [
            {
                "source_name": "news.example",
                "source_url": "https://news.example/feed",
                "kind": "page",
                "title": "Waiver wire",
                "link": "https://news.example/waivers",
                "published": None,
                "text": "Grab Pickup Gamma now.",
            }
        ],
        "notes": [
            {
                "source_name": "bad.example",
                "source_url": "https://bad.example/x",
                "reason": "HTTP 503",
            }
        ],
    }

    _run(tmp_path, fake, sources)

    context = fake.calls[0][0]
    assert "https://news.example/waivers" in context
    assert "Grab Pickup Gamma now." in context
    assert "https://bad.example/x" in context
    assert "HTTP 503" in context


def test_missing_sources_output_is_not_fatal(tmp_path: Path) -> None:
    fake = FakeLLMClient()

    run_dir = _run(tmp_path, fake, sources=None)

    assert len(fake.calls) == 1
    assert run_dir.briefing_md.exists()
