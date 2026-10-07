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

## Commands
Not yet defined; added once the project skeleton exists.
