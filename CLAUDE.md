# FF Daily Briefing

Personal, single-user pipeline: fetches Sleeper data and configured web sources, synthesizes a daily fantasy football briefing with an LLM, and opens it as a styled HTML page.

## Source of intent
- Product intent: `.artifacts/etwilson/vision.md`
- Current work: `.artifacts/etwilson/epics/`

## Settled constraints
- Python, TOML config (`tomllib`), secrets in gitignored `.env`
- Sleeper is accessed via the raw HTTP API, read-only; no MCP and no writes to Sleeper
- The LLM sits behind a narrow seam (context and prompt in, text out); provider specifics stay inside it
- `ANTHROPIC_API_KEY` must stay unset so `claude -p` uses the subscription rather than API billing

## Testing approach
- Tooling: `uv`, `pytest`, `mypy` (the type-check gate), `ruff`. Tests use recorded fixtures and never hit the network or a real LLM.
- Follow TDD for behavior: parsing, data shaping, idempotence, failure handling, anything with logic that can be wrong.
- Do not force RED-first tests onto pure scaffolding or wiring: project init, tool config, a launchd plist, a one-line `open` call. Verify those by running them. A test that only restates configuration earns no place.
- Where wiring wraps a side effect (running `open`, calling `claude -p`), inject the side effect and test the logic around it.

## Commands
Not yet defined; added once the project skeleton exists.
