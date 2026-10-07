---
id: STR-005
title: Render stage
epic: EPIC-001
status: open
priority: medium
---

## Goal

Convert the synthesized markdown into a self-contained, nicely styled HTML page the user can read comfortably in a browser.

---

## Scope

### In
- Markdown to HTML conversion with the project's own template and CSS
- A single self-contained file (no external assets), readable in light and dark system themes
- Clickable source links, and clear per-league sections when the briefing has them
- The dated HTML file kept on disk as the day's history

### Out
- Visual polish beyond a clean, readable design
- Multiple templates, theming options, or JavaScript interactivity
- Changing what the briefing says (that is synthesis)

---

## Acceptance Criteria

- [ ] Given a markdown briefing, the stage writes a single HTML file that opens correctly in a browser with no external requests
- [ ] Headings, lists, tables, and links in the markdown render as such
- [ ] The file is written to the dated directory and is the "final briefing" the idempotence check looks for
- [ ] Malformed or empty markdown produces a clear error, not a blank page

---

## Context & Decisions

- Presentation lives in the HTML template, not the prompt, so the briefing can be restyled without touching synthesis.
- A small markdown library is acceptable; no heavier dependencies.

---

## Dependencies

- **Depends on:** STR-001, STR-004 (consumes the markdown)
- **Blocks:** STR-006 (delivery opens this file)

---

## Notes

Testing approach: TDD the conversion behavior and the error cases. Do not test the markdown library, and do not write tests that merely restate CSS. Confirm the visual result by opening one generated file by eye.
