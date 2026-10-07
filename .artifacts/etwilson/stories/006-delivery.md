---
id: STR-006
title: Delivery
epic: EPIC-001
status: specced
priority: high
---

## Goal

Show the finished briefing to the user by opening it in their default browser when a new one is produced.

---

## Scope

### In
- Opening the day's HTML briefing with macOS `open`
- Opening only when a new briefing was produced, never for a skipped (already-done) day

### Out
- Email, notifications, terminal or Ghostty display
- Any delivery channel other than opening the file

---

## Acceptance Criteria

- [ ] After a successful run that produced a new briefing, the HTML file opens in the default browser
- [ ] A run skipped by the per-day idempotence rule does not open anything
- [ ] If the file is missing, delivery fails with a clear error

---

## Context & Decisions

- The user does not care how the briefing is shown, only that it is shown when they open the laptop. Opening a styled HTML file is the simplest reliable way.
- A launchd agent runs in the user's GUI session, so `open` can display the page.

---

## Dependencies

- **Depends on:** STR-001, STR-005
- **Blocks:** STR-007 (scheduling runs the whole pipeline including delivery)

---

## Notes

Testing approach: this is mostly wiring around a one-line side effect. Inject the `open` call and TDD only the logic around it (open only when a new briefing exists, missing-file error). Do not test that `open` itself works; verify by running it once.
