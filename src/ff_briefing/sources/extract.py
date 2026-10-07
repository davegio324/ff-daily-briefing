import re
from dataclasses import dataclass

import feedparser
from bs4 import BeautifulSoup

_BOILERPLATE_TAGS = [
    "head",
    "script",
    "style",
    "noscript",
    "nav",
    "footer",
    "header",
    "aside",
    "form",
]
_FEED_CONTENT_TYPES = ("application/rss+xml", "application/atom+xml")
_FEED_ROOT = re.compile(r"<(rss|feed|rdf:RDF)[\s>]", re.IGNORECASE)
_SNIFF_CHARS = 1024


@dataclass(frozen=True)
class FeedEntry:
    title: str | None
    link: str
    published: str | None
    text: str


def extract_page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(_BOILERPLATE_TAGS):
        tag.decompose()
    return _clean(soup.get_text(" "))


def looks_like_feed(content_type: str | None, body: str) -> bool:
    if content_type and any(t in content_type.lower() for t in _FEED_CONTENT_TYPES):
        return True
    return _FEED_ROOT.search(_strip_prolog(body)[:_SNIFF_CHARS]) is not None


def parse_feed(body: str) -> list[FeedEntry]:
    parsed = feedparser.parse(body)
    entries = []
    for raw in parsed.entries:
        content = raw.get("content")
        html = content[0].get("value", "") if content else raw.get("summary", "")
        entries.append(
            FeedEntry(
                title=raw.get("title"),
                link=raw.get("link", ""),
                published=raw.get("published") or raw.get("updated"),
                text=_clean(BeautifulSoup(html, "html.parser").get_text(" ")),
            )
        )
    return entries


def _strip_prolog(body: str) -> str:
    return re.sub(r"<\?xml[^>]*\?>", "", body)


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
