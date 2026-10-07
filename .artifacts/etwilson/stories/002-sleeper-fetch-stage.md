---
id: STR-002
title: Sleeper fetch stage
epic: EPIC-001
status: open
priority: high
---

## Goal

Replace the stub fetch for Sleeper with real data about the user's teams and leagues, so synthesis can reason about actual rosters and each league's rules.

---

## Scope

### In
- Raw HTTP, read-only Sleeper API access using the username from `config.toml`
- The user's rosters in each of their leagues
- Each league's settings: scoring and waiver schedule (waiver clear timing is read from Sleeper, not config)
- Free-agent and trending player data
- Persisting the result in the stage output format set by the skeleton

### Out
- Any write to Sleeper
- MCP or LLM-driven calls
- Interpreting the data (that is synthesis)
- Multi-user support

---

## Acceptance Criteria

- [ ] For the configured username, the stage outputs rosters and settings for every league that user is in
- [ ] Output includes each league's scoring settings and waiver schedule
- [ ] Output includes the data needed to identify free agents and trending adds
- [ ] A Sleeper failure produces a clear error, not a partial or silent output
- [ ] Tests run against recorded fixtures and never hit the network

---

## Context & Decisions

- Raw API, not MCP: this is a fixed deterministic fetch and the LLM does not choose calls.
- Waiver timing comes from Sleeper league settings (the architect should verify the exact fields) so config stays minimal.
- Free agents are players not rostered in a given league; whether to derive them locally from the full player data or use another endpoint is the architect's call. The full player dump is large, so it should be fetched sparingly.

---

## Dependencies

- **Depends on:** STR-001 (stage pipeline and config)
- **Blocks:** STR-004 (synthesis consumes this data)

---

## Notes

Testing approach: TDD the logic (selecting the user's leagues, shaping rosters and settings, deriving free agents, error handling) against recorded fixtures. The thin HTTP calls themselves do not need their own tests beyond being exercised through that logic.
