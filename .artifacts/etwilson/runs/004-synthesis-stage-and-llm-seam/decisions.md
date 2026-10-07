
## coder-004 decisions
- build_context takes (leagues, items, notes, today); items/notes are the sources.json lists as-is, replacing the spec's SourceResult. Pure function; load_inputs in the stage is the adapter.
- Missing sources.json is treated as empty (spec: not fatal); this drops the stub's require on sources.json. Missing sleeper.json raises MissingInputError.
- Per-league free agents = trending add/drop entries with available_in[league_id] true, merged with resolved player details. Roster starters/players/reserve ids are expanded with details.
- ClaudeCliClient gained an optional `timeout` ctor arg (default 600s); runs in a TemporaryDirectory cwd; flags used: -p, --output-format text, --tools "", --strict-mcp-config (all confirmed in `claude --help`).
- CLAUDE.md Commands section left unchanged (skeleton left it undefined).
- Gate order was followed for every TDD task; the seam/fake task was scaffolding with no tests, verified by mypy/ruff.

## Pending manual verification (user)
- Run the real synthesize stage once with `claude` installed and ANTHROPIC_API_KEY set in the shell; confirm a briefing covering both leagues and no API billing.
