---
id: STR-001
title: Project skeleton and stage pipeline
epic: EPIC-001
status: specced
priority: high
---

## Goal

Stand up the Python project and a working end-to-end pipeline made of stub stages, so every later story plugs into something that already runs.

---

## Scope

### In
- `uv` project with `pytest`, `mypy`, and `ruff` configured, and a project type-check script
- CLI with a `run` command and one subcommand per stage (fetch, synthesize, render, deliver)
- `config.toml` loading via `tomllib`, with the shape that later stories extend (Sleeper username, source URLs)
- Per-stage output persisted to a dated directory on disk; each stage reads the previous stage's persisted output so stages can be re-run independently
- Stub stages that produce a placeholder briefing end to end
- `run` is idempotent per day: it skips if today's final briefing already exists, and `--force` overrides

### Out
- Any real Sleeper, source, LLM, rendering, or delivery behavior (later stories replace the stubs)
- Scheduling

---

## Acceptance Criteria

- [ ] `uv run` of the CLI's `run` command completes and writes a placeholder briefing into today's dated directory
- [ ] Each stage subcommand can run alone, reading the prior stage's persisted output
- [ ] A second `run` on the same day does nothing; `--force` reruns it
- [ ] A missing or malformed `config.toml` fails with a clear error
- [ ] The project's type-check script, tests, and ruff all pass

---

## Context & Decisions

- Python, TOML config, `uv`, `pytest`, `mypy`, `ruff`. There are no secrets in the pipeline, so there is no `.env`.
- Stages persist to disk deliberately: it makes each stage debuggable and re-runnable, which matters most when iterating on synthesis.
- The output directory (`data/` or `output/`) is already gitignored.
- Stage interfaces (what each stage reads and writes) are set here and extended by later stories; keep them simple and file-based.

---

## Dependencies

- **Depends on:** none
- **Blocks:** STR-002, STR-003, STR-004, STR-005, STR-006, STR-007 (all build on this skeleton)

---

## Notes

Testing approach: project init and tool configuration are scaffolding. Verify them by running them; do not write RED-first tests for pyproject or tool settings. Apply TDD to the real logic: config loading and validation errors, the per-day idempotence rule, and stage input/output handoff. The project's `CLAUDE.md` is the update point for the real test, type-check, and run commands once they exist.
