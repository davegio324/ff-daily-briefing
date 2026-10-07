from typing import Any

from ff_briefing.sources.fetch import Get, fetch_all, httpx_get
from ff_briefing.sources.models import sources_from_urls


def fetch_sources(urls: list[str], get: Get | None = None) -> dict[str, Any]:
    items, notes = fetch_all(sources_from_urls(urls), get or httpx_get)
    return {
        "items": [item.to_dict() for item in items],
        "notes": [note.to_dict() for note in notes],
    }
