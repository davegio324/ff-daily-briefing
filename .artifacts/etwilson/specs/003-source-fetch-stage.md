---
number: 003
story: STR-003
status: ready
base_branch: main
depends_on: [STR-001]
scope_files:
  - pyproject.toml
  - uv.lock
  - src/ff_briefing/stages/fetch.py
  - src/ff_briefing/stages/sources.py
  - src/ff_briefing/sources/__init__.py
  - src/ff_briefing/sources/extract.py
  - src/ff_briefing/sources/fetch.py
  - src/ff_briefing/sources/models.py
  - tests/sources/
  - tests/fixtures/sources/
  - tests/test_sources_stage.py
---

# Feature: Source Fetch Stage

## Summary
A pipeline stage that reads the configured trusted web sources (plain HTML pages and RSS/Atom feeds) from `config.toml`, fetches each, reduces it to clean LLM-ready text, and persists the results as the stage output. Every item keeps its source name and URL so synthesis can cite it. A source that fails or yields nothing useful is skipped and recorded as a note; the run continues. This proves the web-source node of the pipeline for a handful of URLs and nothing more.

---

## Reconciliation with the skeleton (authoritative; overrides conflicting text below)
The skeleton spec is now fixed and replaces the "Interface assumptions" section below.
- **Config:** the skeleton defines sources as `[sources] urls = [...]`, exposed as `Config.source_urls: list[str]`. Do not change the config format or `config.py`. There is no per-source `name`: derive `SourceConfig.name` from the URL's hostname (minus a leading `www.`). The `[[sources]]` table form, the "entry missing `name` or `url`" case, and the related config-parsing task are dropped. An empty `urls` list yields `{"items": [], "notes": []}`.
- **Stage wiring:** replace only the `_fetch_sources` helper in the skeleton's `stages/fetch.py`; it calls `stages/sources.py` and writes the `{"items": ..., "notes": ...}` dict to `run_dir.sources_json` (this replaces the stub's `{"sources": []}` shape). Do not touch `_fetch_sleeper`. There is no separate "pipeline persistence helper": write the file directly (`json`, `indent=2`, utf-8).
- **Dependencies:** `httpx` is already added by the Sleeper fetch story; add only `feedparser` and `beautifulsoup4`.
- **Config example:** `config.example.toml` already has placeholder `urls`; no change.

---

## Requirements
- The stage reads the source URLs from `config.toml`; each becomes a `SourceConfig` with a hostname-derived `name`.
- An HTML page source yields clean text: scripts, styles, navigation/boilerplate tags removed, whitespace normalized.
- An RSS/Atom feed source yields one entry per feed item (title, link, published date when present, summary/content reduced to clean text).
- Feed vs. page is detected from the response (content type or content sniffing), not configured by the user.
- Every output item carries its source `name` and source `url` (and the item's own link for feed entries).
- A source that errors (network error, non-2xx, timeout), is unparseable, or reduces to empty/near-empty text is skipped and recorded as a note naming the source and the reason; other sources are unaffected.
- Pages that are JS-rendered shells (no meaningful text after extraction) fall under "returns nothing useful" and are dropped with a note; no workaround is attempted.
- A missing/empty source list produces a valid empty output, not an error.
- Results and notes are persisted via the pipeline's stage output format.

---

## Scope

### In Scope
- `[[sources]]` config parsing for this stage
- HTTP fetch (with timeout), HTML text extraction, feed parsing
- Skip-and-note failure handling
- Stage wiring and persistence

### Out of Scope
- Headless browsers, JS rendering, login-gated sources
- Caching, rate limiting, retries, concurrency, crawling, large lists
- Relevance filtering, summarization, or truncation policy for the LLM (synthesis owns this)
- Choosing the real URLs (user supplies; use placeholders in `config.example.toml`)

---

## Technical Approach

### Interface assumptions (STR-001 spec was not yet available)
The STR-001 spec did not exist when this was written. These assumptions must be reconciled with it before implementation; the logic is isolated in pure functions so only the thin stage adapter changes:
- Package layout `src/ff_briefing/` with stages under `src/ff_briefing/stages/`.
- A stage is a callable that receives the loaded config (a `dict` from `tomllib`) and a way to persist its output as JSON on disk, per the pipeline's stage output format. This spec assumes the stage output is a JSON-serializable dict written by the pipeline's persistence helper; `stages/sources.py` produces that dict and calls the helper. If STR-001 defines a different registration or persistence mechanism, adapt only `stages/sources.py`.
- Config is loaded by the STR-001 config loader; this stage reads the `sources` key from the resulting dict and does not load the file itself.

### Entry points / interfaces
- `stages/sources.py`: stage entry; reads `config["sources"]`, calls the fetch/extract functions, returns/persists the output dict.

### Key modules
- `sources/models.py`: dataclasses (below) with a `to_dict()` for JSON output.
- `sources/extract.py` (pure, no I/O): `extract_page_text(html: str) -> str` and `parse_feed(body: str) -> list[FeedEntry]` plus `looks_like_feed(content_type: str | None, body: str) -> bool`.
- `sources/fetch.py`: `fetch_source(source: SourceConfig, get: Callable[[str], FetchResponse]) -> SourceResult`. The HTTP call is injected as `get` so tests supply recorded fixtures; the default `get` wraps `httpx` with a timeout and redirect-following. `fetch_all(sources, get) -> tuple[list[Item], list[Note]]` catches per-source exceptions.
- Dependencies to add: `httpx`, `feedparser` (parse from string), `beautifulsoup4` (HTML parser stdlib `html.parser` or `lxml` not required).

### Data model
```python
@dataclass(frozen=True)
class SourceConfig:   name: str; url: str
@dataclass(frozen=True)
class FetchResponse:  status: int; content_type: str | None; text: str
@dataclass(frozen=True)
class Item:           source_name: str; source_url: str; kind: Literal["page", "feed_entry"]
                      title: str | None; link: str; published: str | None; text: str
@dataclass(frozen=True)
class Note:           source_name: str; source_url: str; reason: str
```
For a page, `link == source_url`. Stage output shape:
```json
{"items": [Item.to_dict(), ...], "notes": [Note.to_dict(), ...]}
```

### Exposed contract (consumed by synthesis)
Stage output is a dict `{"items": list[ItemDict], "notes": list[NoteDict]}` with `ItemDict` keys `source_name, source_url, kind, title, link, published, text` (all `str`, `title`/`published` may be `None`) and `NoteDict` keys `source_name, source_url, reason` (`str`). Synthesis and render read notes to mention skipped sources.

### Key design decisions
- Per-source `try/except Exception` at the `fetch_all` boundary is the only place failures become notes; extract functions raise or return empty and the caller classifies.
- "Nothing useful" threshold: extracted text shorter than a module constant `MIN_TEXT_CHARS = 200` for a page; a feed with zero entries. Constant is named and tunable.
- Injected `get` keeps fetch logic testable without patching the network; matches the project rule to inject side effects.
- Extendable shape (list of sources in, items/notes out) without speculative abstractions.

---

## Success Criteria
- [ ] `extract_page_text` on an HTML fixture returns text containing the article body and none of the `<script>`, `<style>`, `<nav>`, `<footer>` content, with runs of whitespace collapsed to single spaces/newlines.
- [ ] `parse_feed` on an RSS fixture and on an Atom fixture each return one `FeedEntry` per item with title, link, published (when present) and tag-free summary text.
- [ ] `looks_like_feed` returns True for an RSS/Atom body served as `application/rss+xml`, `application/atom+xml`, and as `text/xml`/`text/html` with an `<rss`/`<feed` root; False for an ordinary HTML page.
- [ ] Given one page source and one feed source, `fetch_all` returns page text as one `Item(kind="page")` and one `Item(kind="feed_entry")` per feed entry, each with the configured `source_name` and `source_url`.
- [ ] A source whose `get` raises, one returning status 404/500, one returning an unparseable/empty feed, and one returning a JS-shell HTML page (fixture with only a script and an empty `<div id="root">`) each produce exactly one `Note` with that source's name, url and a non-empty reason, and zero items.
- [ ] When one source fails and another succeeds, `fetch_all` still returns the successful source's items alongside the failure note.
- [ ] Empty or absent `sources` config produces `{"items": [], "notes": []}` without raising.
- [ ] The stage persists output in the pipeline's stage output format and the persisted dict equals the `{"items": ..., "notes": ...}` shape above (verified with the injected `get` and a temp output location; no network).
- [ ] No test performs network I/O; all responses come from fixtures under `tests/fixtures/sources/`.
- [ ] `uv run pytest`, `uv run mypy`, and `uv run ruff check` pass.

---

## Tasks
- [ ] **Models and source list:** Create `sources/models.py` and a function turning `Config.source_urls` into `list[SourceConfig]` with hostname-derived names (TDD: `www.` stripped, empty list -> empty list). Add `feedparser` and `beautifulsoup4` to `pyproject.toml`; add recorded fixtures (article HTML, JS-shell HTML, RSS, Atom, broken feed).
- [ ] **Extraction (TDD, pure):** `sources/extract.py` with `extract_page_text`, `looks_like_feed`, `parse_feed`. Fully tested against fixtures before next task.
- [ ] **Fetch and skip-and-note (TDD):** `sources/fetch.py` with `fetch_source`, `fetch_all`, default httpx `get`. Test with injected fake `get` built from fixtures covering success, exception, bad status, empty/unparseable, JS shell, and mixed success/failure.
- [ ] **Stage wiring:** `stages/sources.py` (builds the output dict from `Config.source_urls` and an injected `get`) called by the `_fetch_sources` helper in `stages/fetch.py`, which writes `run_dir.sources_json`. Test with injected `get` and a `tmp_path` run dir; no network.

---

## Considerations
- Do not test httpx or feedparser/BeautifulSoup themselves; test only that our reduction and classification of fixture inputs is right.
- feedparser is lenient and rarely raises; "unparseable" is detected by zero entries plus `bozo` with no entries, so classify on entry count.
- Some sites serve feeds as `text/html`; sniffing the body root element is required.
- Send a descriptive `User-Agent` header; some sites reject the default.
- Fixtures should be small trimmed real captures; keep a feed entry with HTML in its summary to prove tag stripping.
- Do not add comments or test names referencing story/spec numbers.
- Output text is not truncated here; synthesis decides what fits context.
