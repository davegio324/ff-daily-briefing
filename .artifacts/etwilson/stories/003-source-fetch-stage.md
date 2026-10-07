---
id: STR-003
title: Source fetch stage
epic: EPIC-001
status: specced
priority: high
---

## Goal

Fetch the user's configured trusted web sources and reduce them to clean text, proving this node of the pipeline works with a handful of URLs.

---

## Scope

### In
- Reading the source list from `config.toml`
- Plain HTTP and RSS fetching
- Reducing pages and feeds to clean text suitable for an LLM
- A source that fails or returns nothing useful is skipped and recorded as a note; the run continues
- Persisting results and failure notes in the stage output format

### Out
- Headless browsers and JS-rendered pages (such URLs are dropped, not worked around)
- Login-gated sources
- Large source lists, caching, rate-limit strategy, or crawling

---

## Acceptance Criteria

- [ ] Each configured source yields clean text in the stage output, tagged with its name and URL for attribution
- [ ] One failing source does not stop the others, and the failure appears as a note in the output
- [ ] Both HTML pages and RSS feeds are handled
- [ ] Tests run against recorded fixtures and never hit the network

---

## Context & Decisions

- This node is the most likely to grow later (many sources). v1 only has to prove it works for a handful, so keep the shape extendable but build nothing speculative.
- The user supplies the real URLs and puts them in `config.toml` when ready; this story does not depend on them.
- Attribution matters: downstream synthesis cites sources, so every item keeps its origin.

---

## Dependencies

- **Depends on:** STR-001 (stage pipeline and config)
- **Blocks:** STR-004 (synthesis consumes this data)

---

## Notes

Testing approach: TDD the logic (text extraction, RSS parsing, skip-and-note failure handling) against recorded fixtures. Do not test the HTTP library or the feed parser library themselves.
