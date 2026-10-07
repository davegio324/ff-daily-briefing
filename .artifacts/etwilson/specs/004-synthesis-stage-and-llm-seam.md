---
number: 004
story: STR-004
status: ready
base_branch: main
depends_on: [STR-001, STR-002, STR-003]
scope_files:
  - src/ff_briefing/llm/__init__.py
  - src/ff_briefing/llm/seam.py
  - src/ff_briefing/llm/claude_cli.py
  - src/ff_briefing/stages/synthesize.py
  - src/ff_briefing/synthesis/context.py
  - src/ff_briefing/synthesis/prompt.py
  - src/ff_briefing/synthesis/__init__.py
  - tests/test_synthesis_context.py
  - tests/test_synthesize_stage.py
  - tests/test_claude_cli.py
  - tests/fakes.py
  - tests/conftest.py
  - CLAUDE.md
---

# Feature: Synthesis stage and LLM seam

## Summary
Adds the synthesize stage: it reads the persisted Sleeper and source fetch outputs, assembles one context covering both leagues (rosters, league rules, free agents, source text, source failure notes, today's date, per-league waiver schedule), sends it with a minimal placeholder prompt through a narrow `LLMClient` seam, and persists the returned markdown in the stage output format. One implementation of the seam shells out to headless `claude -p` on the user's subscription, with `ANTHROPIC_API_KEY` removed from the child environment. The stage depends only on the seam, so tests use a fake and never call a real LLM.

---

## Reconciliation with upstream specs (authoritative; overrides "Assumed upstream contracts" and the `SourceResult`/`LeagueData` models below)
All three upstream contracts are now fixed. The package is `ff_briefing` (not `ff_daily_briefing`).
- **Stage interface:** `stages/synthesize.py` already exists as a stub with signature `(config, run_dir, today) -> None`. Replace its body. Read inputs via `run_dir.require(run_dir.sleeper_json, "fetch")`; a missing Sleeper file raises the skeleton's `MissingInputError` (which names the file). Write the markdown to `run_dir.briefing_md`. The registered stage function keeps the fixed signature and builds the default `ClaudeCliClient` itself; put the real logic in an inner function that takes the `LLMClient` (for example `synthesize_with(client, config, run_dir, today)`) so tests inject the fake. Do not change the registry or signature.
- **Errors:** `LLMError` subclasses the skeleton's `BriefingError`.
- **Sleeper input shape** (from the Sleeper fetch spec): `sleeper.json` has `leagues[]` (each with `league_id`, `name`, `scoring_settings`, `roster_positions`, `waiver{...}`, `roster{...}`, `rostered_player_ids`), `trending{add,drop}` (each entry has `player_id`, `count`, `available_in{league_id: bool}`), and a `players{}` lookup. There is no free-agent list. Replace `LeagueData.free_agents` with that league's trending adds/drops filtered to `available_in[league_id] == true`, with player details resolved from `players`. Roster player ids are resolved the same way.
- **Source input shape** (from the source fetch spec): `sources.json` is `{"items": [{source_name, source_url, kind, title, link, published, text}], "notes": [{source_name, source_url, reason}]}`. Replace `SourceResult` with these two lists: each item is cited by `source_name` and `link`; each note becomes a failed-sources entry. Empty `items` and `notes` is not an error.
- **Adapter:** `load_inputs` maps these real shapes to `build_context`'s plain-data parameters. `build_context` stays a pure function.

---

## Requirements
- The seam is a single-method interface: assembled context text and a prompt in, markdown text out. Nothing provider-specific appears in its signature or in the stage.
- The synthesize stage obtains its LLM exclusively through the seam; swapping implementations requires no change to stage code.
- One LLM call covers both leagues.
- The assembled context includes, for each league: roster, league rules (scoring), waiver schedule, and free agents/trending players.
- The assembled context includes today's date.
- The assembled context includes the text of every successfully fetched source, with its URL so the model can cite it.
- The assembled context includes a failure note for every source that failed to fetch, so the briefing can mention missing sources.
- The placeholder prompt instructs the model to produce a markdown briefing with one section per league, to follow the waiver calendar, to cite sources by URL, and to mention missing sources. It stays minimal.
- The `claude -p` implementation runs with `ANTHROPIC_API_KEY` absent from the child process environment, even if set in the parent.
- The `claude -p` implementation maps a nonzero exit, a missing `claude` binary, and empty output to a single seam error type carrying the stderr/reason; it never returns empty text as success.
- The stage persists the markdown briefing to its output location in the stage output format and fails (does not write a briefing) if the seam raises.
- If the Sleeper fetch output is missing, the stage fails with a clear error. Missing or empty source output is not fatal: the briefing proceeds with whatever source data and failure notes exist.

---

## Scope

### In Scope
- `LLMClient` seam, `LLMError`, and the `claude -p` implementation
- Context assembly (pure function) and placeholder prompt
- Synthesize stage wiring: load inputs, assemble, call seam, persist markdown
- A fake seam implementation for tests
- A one-time manual run of the real `claude -p` path (not automated)

### Out of Scope
- Prompt quality, briefing template, instruction design
- Other providers, API-key billing
- Streaming, retries, cost tracking, context truncation or token budgeting
- Rendering the markdown (render stage) and delivery

---

## Technical Approach

### Assumed upstream contracts (to reconcile)
At drafting time the skeleton, Sleeper fetch, and source fetch specs were not yet written, so no authoritative contracts existed. The implementer must reconcile the following against the real specs/code and adapt only the thin loading adapter described below, not the pure assembly logic:
- **Stage interface (skeleton):** stages are invoked with the run's date and a way to resolve per-stage output paths, and persist outputs under a per-day directory. Assumed shape: a stage is a callable receiving a context object exposing `today: datetime.date`, and read/write paths for the fetch outputs and the synthesize output. Use whatever the real skeleton defines, including its "stage output format" for the markdown file and its stage-failure convention.
- **Sleeper output (fetch):** persisted JSON that can be loaded to a dict with, per league: a name/id, roster, league settings including scoring and waiver timing, and free-agent/trending players.
- **Source output (fetch):** persisted data listing per source: URL, fetched text (on success) or an error reason (on failure).

To keep reconciliation cheap, context assembly takes already-loaded plain data (below) and a small `load_inputs` adapter in the stage maps the real persisted files to those shapes.

- **Entry points / interfaces:** `stages/synthesize.py` is the stage entry, registered the way the skeleton registers stages. Its LLM is injected (default: the `claude -p` implementation built from config/env), so tests pass a fake.
- **Key modules:**
  - `llm/seam.py`: the interface and error type.
  - `llm/claude_cli.py`: `ClaudeCliClient`, taking an injectable `runner` (defaults to `subprocess.run`) and an `environ` mapping (defaults to `os.environ`). Builds the child env as a copy of `environ` minus `ANTHROPIC_API_KEY`. Invokes `claude -p` passing the prompt and context (context via stdin, prompt as the `-p` argument), captures stdout/stderr as text, and translates failures to `LLMError`.
  - `synthesis/context.py`: pure assembly of the context string.
  - `synthesis/prompt.py`: the placeholder prompt constant.
  - `stages/synthesize.py`: load inputs, assemble, call seam, write output.
- **Data model:**
  - `SourceResult`: `url: str`, `text: str | None`, `error: str | None` (exactly one of text/error set).
  - `LeagueData`: `name: str`, `roster: Any`, `rules: Any`, `waiver_schedule: Any`, `free_agents: Any` (values are the Sleeper JSON fragments as persisted; they are serialized into the context, not interpreted).
- **Exposed contract:**
  - `class LLMError(Exception)`
  - `class LLMClient(Protocol): def complete(self, context: str, prompt: str) -> str`
  - `def build_context(leagues: Sequence[LeagueData], sources: Sequence[SourceResult], today: datetime.date) -> str`
  - `PLACEHOLDER_PROMPT: str`
  - `class ClaudeCliClient: def __init__(self, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run, environ: Mapping[str, str] | None = None) -> None` implementing `LLMClient`
  - `tests/fakes.py: class FakeLLMClient` recording `(context, prompt)` calls and returning a canned string, or raising a configured `LLMError`.
- **Key design decisions:**
  - Context is plain text/markdown sections (date, per league sections with JSON-serialized fragments, sources, failed sources) so it is readable and diffable; no schema is imposed on the model.
  - Data is serialized as received rather than interpreted, so changes to Sleeper field detail do not touch this stage.
  - Env scrubbing happens inside `ClaudeCliClient` so the stage and callers cannot forget it.
  - Seam takes strings only, so provider specifics (CLI flags, env) cannot leak out.

---

## Success Criteria
- [ ] `build_context` output contains today's date in ISO format (`2026-10-07` style) for a given `today`.
- [ ] `build_context` output contains a distinct section per league, each including that league's roster, rules, waiver schedule, and free agents data.
- [ ] `build_context` output includes the URL and text of each successful source, and for each failed source its URL and error reason under a clearly labeled failed-sources section.
- [ ] `build_context` with zero sources, or only failed sources, still produces valid output (no exception) and names the failures.
- [ ] Stage test with `FakeLLMClient`: the stage makes exactly one `complete` call, the received context contains data from both leagues, and the received prompt is `PLACEHOLDER_PROMPT`.
- [ ] Stage test: the fake's returned markdown is written verbatim to the synthesize output location in the skeleton's stage output format.
- [ ] Stage test: when the fake raises `LLMError`, the stage reports failure per the skeleton's convention and writes no briefing file.
- [ ] Stage test: missing Sleeper output makes the stage fail with an error naming the missing input; the fake is not called.
- [ ] Stage test: a source failure note in the persisted source output appears in the context passed to the fake.
- [ ] The stage module imports nothing from `llm/claude_cli.py` except where it constructs the default client (the stage's logic accepts any `LLMClient`).
- [ ] `ClaudeCliClient` test with a recording runner and `environ={"ANTHROPIC_API_KEY": "sk-x", "PATH": "/bin"}`: the env passed to the runner lacks `ANTHROPIC_API_KEY` and retains `PATH`; the parent mapping is not mutated.
- [ ] `ClaudeCliClient` test: the runner's argv begins with `claude` and includes `-p`; the context reaches the runner via stdin input and the prompt via the `-p` argument.
- [ ] `ClaudeCliClient` test: nonzero return code raises `LLMError` including stderr; `FileNotFoundError` from the runner raises `LLMError`; whitespace-only stdout raises `LLMError`; successful stdout is returned stripped.
- [ ] `mypy` passes via the project's type-check command, and `ruff` passes.
- [ ] Manual (not automated): running the real stage once with `claude` installed and `ANTHROPIC_API_KEY` set in the shell produces a markdown briefing covering both leagues, without API billing. Result recorded in the run's decisions notes.

---

## Tasks
- [ ] **Seam and fake:** Create `llm/seam.py` (`LLMClient`, `LLMError`) and `tests/fakes.py` (`FakeLLMClient`). Pure scaffolding; verify via type-check, no dedicated tests.
- [ ] **Context assembly (TDD):** `synthesis/context.py` and `synthesis/prompt.py` with `tests/test_synthesis_context.py`. Must be fully tested before the stage task.
- [ ] **`claude -p` implementation (TDD):** `llm/claude_cli.py` with `tests/test_claude_cli.py` using an injected runner for env scrubbing, argv/stdin shape, and error mapping. Confirm the exact `claude` CLI flags with `claude --help` while implementing; keep to the minimal prompt-plus-stdin non-interactive form.
- [ ] **Synthesize stage (TDD):** `stages/synthesize.py` with the `load_inputs` adapter reconciled to the real fetch outputs and skeleton stage interface; `tests/test_synthesize_stage.py` with the fake and recorded-fixture-style persisted inputs. Register the stage with the skeleton's pipeline and add the stage to `CLAUDE.md` Commands only if the skeleton spec's task for it leaves that to later stories.
- [ ] **Manual verification:** one real run per the last success criterion; record outcome in decisions notes.

---

## Considerations
- The first task of the implementer is to reconcile the assumed upstream contracts with the merged skeleton, Sleeper, and source fetch code; if they diverge materially, change only `load_inputs` and the stage registration.
- Context size is unbounded in v1 (no truncation). Large source text is accepted risk; passing context via stdin avoids argv length limits.
- If `ANTHROPIC_API_KEY` was used previously and `claude` is not logged in on the subscription, the call fails; that surfaces as `LLMError` and is the user's dogfooding concern.
- Do not tune the prompt. Do not name tests or comments after story/spec numbers.
- Tests must not spawn a real `claude` process or touch the network.
