
## Coder notes
- feedparser ships no type stubs; added a mypy `ignore_missing_imports` override for it in pyproject.toml.
- `head` is stripped as boilerplate so `<title>` text does not make a JS-shell page look non-empty.
- `fetch_source` raises `UnusableSource` / propagates exceptions; `fetch_all` is the only place they become notes.
- Page items have `title=None`; the spec did not require extracting a page title.
- The default `httpx_get` is untested wiring (no network in tests). Pending for the user: run the fetch stage against real configured URLs and confirm sources.json looks sensible.
