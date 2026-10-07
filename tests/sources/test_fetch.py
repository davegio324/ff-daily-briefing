import pytest

from ff_briefing.sources.fetch import fetch_all
from ff_briefing.sources.models import FetchResponse, SourceConfig
from tests.sources.fakes import fake_get, fixture_response

PAGE = SourceConfig("page.example", "https://page.example/post")
FEED = SourceConfig("feed.example", "https://feed.example/rss")
BAD = SourceConfig("bad.example", "https://bad.example/x")


def test_page_and_feed_sources_yield_tagged_items() -> None:
    get = fake_get(
        {
            PAGE.url: fixture_response("article.html"),
            FEED.url: fixture_response("feed.rss", "application/rss+xml"),
        }
    )

    items, notes = fetch_all([PAGE, FEED], get)

    assert notes == []
    page_items = [i for i in items if i.kind == "page"]
    feed_items = [i for i in items if i.kind == "feed_entry"]
    assert len(page_items) == 1
    assert (page_items[0].source_name, page_items[0].source_url) == (PAGE.name, PAGE.url)
    assert page_items[0].link == PAGE.url
    assert "running back room is thin" in page_items[0].text
    assert [i.link for i in feed_items] == ["https://news.example/a", "https://news.example/b"]
    assert {(i.source_name, i.source_url) for i in feed_items} == {(FEED.name, FEED.url)}
    assert feed_items[0].title == "Starter injured"


def test_feed_served_as_html_is_still_parsed_as_feed() -> None:
    get = fake_get({FEED.url: fixture_response("feed.atom", "text/html")})

    items, _ = fetch_all([FEED], get)

    assert [i.kind for i in items] == ["feed_entry", "feed_entry"]


@pytest.mark.parametrize(
    "outcome",
    [
        TimeoutError("timed out"),
        FetchResponse(404, "text/html", "not found"),
        FetchResponse(500, "text/html", "oops"),
        fixture_response("broken_feed.xml", "application/rss+xml"),
        fixture_response("js_shell.html"),
        FetchResponse(200, "text/html", "<html><body><p>too short</p></body></html>"),
    ],
    ids=["exception", "404", "500", "empty-feed", "js-shell", "near-empty-page"],
)
def test_unusable_source_yields_one_note_and_no_items(
    outcome: FetchResponse | Exception,
) -> None:
    items, notes = fetch_all([BAD], fake_get({BAD.url: outcome}))

    assert items == []
    assert len(notes) == 1
    assert (notes[0].source_name, notes[0].source_url) == (BAD.name, BAD.url)
    assert notes[0].reason


def test_failing_source_does_not_hide_successful_source() -> None:
    get = fake_get({BAD.url: RuntimeError("boom"), PAGE.url: fixture_response("article.html")})

    items, notes = fetch_all([BAD, PAGE], get)

    assert [i.source_name for i in items] == [PAGE.name]
    assert [n.source_name for n in notes] == [BAD.name]
    assert "boom" in notes[0].reason


def test_no_sources_yield_empty_results() -> None:
    assert fetch_all([], fake_get({})) == ([], [])
