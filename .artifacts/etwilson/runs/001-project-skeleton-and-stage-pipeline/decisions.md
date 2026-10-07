
## Coder decisions
- Worked in the main checkout on the feature branch (no worktree), per team-lead instruction.
- ruff is configured with `extend-exclude = [".artifacts"]`: ruff 0.16 format-checks Markdown code blocks, so the spec files failed `ruff format --check`.
- Dropped an end-to-end CLI `render` test (reviewer flagged it as running the real registry and duplicating the BriefingError mapping test).
- Misc: `config.toml` is committed as a copy of `config.example.toml` (holds nothing private, per spec).
- Real `uv run ff-briefing run` twice in a scratch data dir: first run produced the four files, second skipped with exit 0 and bytes unchanged.
- No manual verification steps pending (no real Sleeper/LLM/browser behavior in this spec).
