---
id: STR-007
title: launchd scheduling
epic: EPIC-001
status: open
priority: high
---

## Goal

Run the full pipeline automatically every day on the user's Mac, so the briefing shows up without anyone running anything.

---

## Scope

### In
- A `launchd` user agent with a calendar interval that runs the pipeline daily
- A job that also fires on wake if the Mac was asleep at the scheduled time
- Absolute paths to the project's Python environment and working directory, since launchd runs with a minimal environment
- stdout and stderr written to log files so failures are not silent
- Install and uninstall instructions

### Out
- Battery, sleep, or lid-closed hardening beyond launchd's run-on-wake behavior
- `pmset` wake scheduling, retries, or failure alerts
- Any scheduler other than launchd

---

## Acceptance Criteria

- [ ] After installing the agent, a scheduled run executes the full pipeline unattended and the styled briefing opens in the browser
- [ ] The agent logs stdout and stderr to a known location
- [ ] The agent can be installed and removed from the documented instructions
- [ ] Rerunning on the same day does nothing, via the pipeline's own idempotence

---

## Context & Decisions

- launchd, not cron: a missed calendar-interval job runs on wake, which is the user's laptop-sleep case.
- The user will find lid-closed and battery issues by dogfooding; those are follow-up work, not part of this story.
- The `claude -p` call needs the user's login session; a user agent in the GUI session provides it.

---

## Dependencies

- **Depends on:** STR-001 through STR-006 (schedules the whole pipeline)
- **Blocks:** none

---

## Notes

Testing approach: the plist and install steps are configuration, so verify them by installing the agent and watching a scheduled run, not with RED-first tests. If any Python code generates the plist or computes paths, TDD that logic. The epic's done condition is met by one unattended scheduled run.
