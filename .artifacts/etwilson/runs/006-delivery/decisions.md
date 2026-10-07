
## Decisions (coder-006)
- Scope deviation: added deliver subcommand tests to tests/test_cli.py (not in scope_files); success criteria require them and the CLI test pattern lives there. Reviewer agreed.
- Tasks 2 and 3 tests passed on arrival: orchestration and CLI wiring pre-exist in the skeleton (per spec reconciliation). Written as regression guards; disclosed to reviewer.
- test_deliver.py originally monkeypatched `deliver_stage.subprocess.run`, which failed mypy; switched to patching `subprocess.run` directly.
- CLAUDE.md Commands section is still "Not yet defined", so the docs step was skipped per the spec's conditional.
- PENDING manual verification (user): run `uv run python -m ff_briefing deliver` (or the full pipeline) once on this Mac and confirm the default browser opens the HTML.
