---
id: STR-004
title: Synthesis stage and LLM seam
epic: EPIC-001
status: open
priority: high
---

## Goal

Turn the fetched Sleeper and source data into a briefing in markdown through a swappable LLM seam, with a working `claude -p` implementation.

---

## Scope

### In
- The seam: assembled context and a prompt go in, text comes out. Provider specifics live only behind it.
- One implementation using the headless `claude -p` CLI on the user's subscription, with `ANTHROPIC_API_KEY` unset so it is not billed at API rates
- One call covering both leagues
- Context assembly: Sleeper data (rosters, league rules, free agents), source text and failure notes, today's date, and each league's waiver schedule
- A minimal placeholder prompt that proves the flow end to end and cites sources
- Persisting the markdown briefing in the stage output format

### Out
- Prompt quality, briefing template, and instruction design: these are deliberately deferred and will be their own project
- Other providers or API-key billing
- Streaming, retries, or cost tracking

---

## Acceptance Criteria

- [ ] With the real `claude -p` implementation, the stage turns fetched data into a markdown briefing that covers both leagues
- [ ] The synthesis stage depends only on the seam, so a fake implementation can replace `claude -p` without touching the stage
- [ ] If `ANTHROPIC_API_KEY` is set in the environment, the `claude -p` call does not use it
- [ ] Source failure notes reach the model so the briefing can mention missing sources
- [ ] Tests use a fake implementation of the seam and never call a real LLM

---

## Context & Decisions

- The swappable seam is the only design commitment here; the user does not want provider choice to spread through the code.
- One call for both leagues keeps cross-league insight possible and uses less subscription quota than one call per league.
- Prompt design is intentionally shallow: the placeholder only needs to produce a sane briefing so downstream stages can be exercised. Do not spend effort tuning it.
- Whether the subscription route is permitted and reliable unattended is the user's to find out by dogfooding; this story only builds it.

---

## Dependencies

- **Depends on:** STR-001, STR-002, STR-003 (it consumes their persisted outputs)
- **Blocks:** STR-005 (render consumes the markdown)

---

## Notes

Testing approach: TDD context assembly and the stage's use of the seam, with a fake seam implementation. The `claude -p` wrapper is thin: inject the subprocess call, test the logic around it (environment handling, error mapping), and verify the real call by running it once manually.
