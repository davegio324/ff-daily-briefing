from pathlib import Path

import pytest

from ff_briefing.sources.extract import extract_page_text, looks_like_feed, parse_feed

FIXTURES = Path(__file__).parent.parent / "fixtures" / "sources"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_page_text_keeps_article_body_and_drops_boilerplate() -> None:
    text = extract_page_text(_read("article.html"))

    assert "running back room is thin" in text
    assert "Week 5 Waiver Wire" in text
    for marker in ("SCRIPT_MARKER", "NAV_MARKER", "FOOTER_MARKER", "color: red"):
        assert marker not in text


def test_page_text_collapses_whitespace_runs() -> None:
    text = extract_page_text(_read("article.html"))

    assert "Second paragraph with odd spacing." in text
    assert "  " not in text
    assert "\n\n" not in text


def test_js_shell_page_reduces_to_no_text() -> None:
    assert extract_page_text(_read("js_shell.html")) == ""


def test_rss_entries_have_title_link_published_and_tag_free_text() -> None:
    entries = parse_feed(_read("feed.rss"))

    assert [e.title for e in entries] == ["Starter injured", "Waiver pickups"]
    assert [e.link for e in entries] == ["https://news.example/a", "https://news.example/b"]
    assert entries[0].published is not None and "2026" in entries[0].published
    assert entries[1].published is None
    assert entries[0].text == "Star RB is out for the week."


def test_atom_entries_use_summary_or_content_as_tag_free_text() -> None:
    entries = parse_feed(_read("feed.atom"))

    assert [e.link for e in entries] == ["https://atom.example/1", "https://atom.example/2"]
    assert entries[0].text == "Buy low on this WR."
    assert entries[1].text == "Sit the kicker."
    assert entries[0].published is not None


def test_feed_without_entries_parses_to_empty_list() -> None:
    assert parse_feed(_read("broken_feed.xml")) == []
    assert parse_feed("not xml at all") == []


@pytest.mark.parametrize(
    ("fixture", "content_type"),
    [
        ("feed.rss", "application/rss+xml; charset=utf-8"),
        ("feed.atom", "application/atom+xml"),
        ("feed.rss", "text/xml"),
        ("feed.rss", "text/html"),
        ("feed.atom", "text/html"),
        ("feed.rss", None),
    ],
)
def test_feed_detected_from_content_type_or_root_element(
    fixture: str, content_type: str | None
) -> None:
    assert looks_like_feed(content_type, _read(fixture))


def test_ordinary_html_page_is_not_a_feed() -> None:
    assert not looks_like_feed("text/html", _read("article.html"))
    assert not looks_like_feed(None, _read("js_shell.html"))
