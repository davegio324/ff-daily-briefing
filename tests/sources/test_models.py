from ff_briefing.sources.models import Item, Note, SourceConfig, sources_from_urls


def test_source_name_is_hostname_without_leading_www() -> None:
    sources = sources_from_urls(["https://www.example.com/feed.xml", "https://news.site.org/a"])

    assert sources == [
        SourceConfig(name="example.com", url="https://www.example.com/feed.xml"),
        SourceConfig(name="news.site.org", url="https://news.site.org/a"),
    ]


def test_empty_url_list_yields_no_sources() -> None:
    assert sources_from_urls([]) == []


def test_item_and_note_serialize_to_plain_dicts_with_contract_keys() -> None:
    item = Item("n", "https://n/", "feed_entry", None, "https://n/a", None, "body")
    note = Note("n", "https://n/", "boom")

    assert item.to_dict() == {
        "source_name": "n",
        "source_url": "https://n/",
        "kind": "feed_entry",
        "title": None,
        "link": "https://n/a",
        "published": None,
        "text": "body",
    }
    assert note.to_dict() == {"source_name": "n", "source_url": "https://n/", "reason": "boom"}
