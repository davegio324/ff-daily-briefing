from dataclasses import asdict, dataclass
from typing import Any, Literal
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceConfig:
    name: str
    url: str


@dataclass(frozen=True)
class FetchResponse:
    status: int
    content_type: str | None
    text: str


@dataclass(frozen=True)
class Item:
    source_name: str
    source_url: str
    kind: Literal["page", "feed_entry"]
    title: str | None
    link: str
    published: str | None
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Note:
    source_name: str
    source_url: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sources_from_urls(urls: list[str]) -> list[SourceConfig]:
    return [SourceConfig(name=_name_for(url), url=url) for url in urls]


def _name_for(url: str) -> str:
    host = urlparse(url).hostname or url
    return host.removeprefix("www.")
