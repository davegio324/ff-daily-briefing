from collections.abc import Callable

import httpx

from ff_briefing.sources.extract import extract_page_text, looks_like_feed, parse_feed
from ff_briefing.sources.models import FetchResponse, Item, Note, SourceConfig

MIN_TEXT_CHARS = 200
TIMEOUT_SECONDS = 15.0
USER_AGENT = "ff-daily-briefing/0.1 (personal fantasy football briefing)"

Get = Callable[[str], FetchResponse]


class UnusableSource(Exception):
    """The source responded but yielded nothing worth passing to synthesis."""


def httpx_get(url: str) -> FetchResponse:
    response = httpx.get(
        url,
        timeout=TIMEOUT_SECONDS,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )
    return FetchResponse(
        status=response.status_code,
        content_type=response.headers.get("content-type"),
        text=response.text,
    )


def fetch_source(source: SourceConfig, get: Get) -> list[Item]:
    response = get(source.url)
    if not 200 <= response.status < 300:
        raise UnusableSource(f"HTTP status {response.status}")

    if looks_like_feed(response.content_type, response.text):
        entries = parse_feed(response.text)
        if not entries:
            raise UnusableSource("feed has no entries")
        return [
            Item(source.name, source.url, "feed_entry", e.title, e.link, e.published, e.text)
            for e in entries
        ]

    text = extract_page_text(response.text)
    if len(text) < MIN_TEXT_CHARS:
        raise UnusableSource(f"page has too little text ({len(text)} chars)")
    return [Item(source.name, source.url, "page", None, source.url, None, text)]


def fetch_all(sources: list[SourceConfig], get: Get) -> tuple[list[Item], list[Note]]:
    items: list[Item] = []
    notes: list[Note] = []
    for source in sources:
        try:
            items.extend(fetch_source(source, get))
        except Exception as exc:
            reason = str(exc) or type(exc).__name__
            notes.append(Note(source.name, source.url, reason))
    return items, notes
