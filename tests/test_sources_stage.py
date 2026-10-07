import json
from pathlib import Path

from ff_briefing.config import Config
from ff_briefing.rundir import RunDir
from ff_briefing.stages.fetch import _fetch_sources
from tests.sources.fakes import fake_get, fixture_response


def _config(urls: list[str]) -> Config:
    return Config(sleeper_username="eli", source_urls=urls)


def test_sources_json_holds_items_and_notes_from_configured_urls(tmp_path: Path) -> None:
    run_dir = RunDir(tmp_path)
    get = fake_get(
        {
            "https://www.page.example/post": fixture_response("article.html"),
            "https://feed.example/rss": fixture_response("feed.rss", "application/rss+xml"),
            "https://bad.example/x": fixture_response("js_shell.html"),
        }
    )

    _fetch_sources(
        _config(
            ["https://www.page.example/post", "https://feed.example/rss", "https://bad.example/x"]
        ),
        run_dir,
        get,
    )

    data = json.loads(run_dir.sources_json.read_text(encoding="utf-8"))
    assert set(data) == {"items", "notes"}
    assert [(i["source_name"], i["kind"]) for i in data["items"]] == [
        ("page.example", "page"),
        ("feed.example", "feed_entry"),
        ("feed.example", "feed_entry"),
    ]
    assert [(n["source_name"], n["source_url"]) for n in data["notes"]] == [
        ("bad.example", "https://bad.example/x")
    ]


def test_no_configured_urls_persists_empty_output_without_fetching(tmp_path: Path) -> None:
    run_dir = RunDir(tmp_path)

    _fetch_sources(_config([]), run_dir, fake_get({}))

    data = json.loads(run_dir.sources_json.read_text(encoding="utf-8"))
    assert data == {"items": [], "notes": []}
