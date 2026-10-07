---
number: 001
story: STR-001
status: ready
base_branch: main
depends_on: []
scope_files:
  - pyproject.toml
  - uv.lock
  - config.toml
  - config.example.toml
  - CLAUDE.md
  - src/ff_briefing/__init__.py
  - src/ff_briefing/__main__.py
  - src/ff_briefing/cli.py
  - src/ff_briefing/config.py
  - src/ff_briefing/errors.py
  - src/ff_briefing/rundir.py
  - src/ff_briefing/pipeline.py
  - src/ff_briefing/stages/__init__.py
  - src/ff_briefing/stages/fetch.py
  - src/ff_briefing/stages/synthesize.py
  - src/ff_briefing/stages/render.py
  - src/ff_briefing/stages/deliver.py
  - tests/test_config.py
  - tests/test_rundir.py
  - tests/test_pipeline.py
  - tests/test_cli.py
  - tests/__init__.py
  - tests/conftest.py
---

# Feature: Project skeleton and stage pipeline

## Summary
Stand up the `uv`-managed Python project and a working end-to-end pipeline of stub stages (fetch, synthesize, render, deliver). Each stage reads the previous stage's persisted file from a dated run directory and writes its own, so any stage can be re-run alone. The CLI exposes `run` (whole pipeline, idempotent per day, `--force` to override) and one subcommand per stage. This spec fixes the file-based stage interfaces that every later story replaces the stubs behind.

---

## Requirements
- `run` executes fetch, synthesize, render, deliver in order and leaves a placeholder briefing in today's dated directory.
- Each stage subcommand (`fetch`, `synthesize`, `render`, `deliver`) runs alone and reads only the prior stage's persisted file(s).
- A stage subcommand whose input file is missing fails with a clear error naming the missing file and the stage that produces it.
- `run` does nothing (exit 0, says so) when today's final briefing already exists; `--force` reruns all stages and overwrites.
- Individual stage subcommands always run (they are not subject to the per-day skip).
- A missing `config.toml`, invalid TOML, or a missing/mistyped required key fails with a clear error message and a non-zero exit, with no traceback.
- Every expected, user-facing failure derives from one base class, `BriefingError` (in `errors.py`). The CLI prints any `BriefingError` as `error: <msg>` to stderr and exits 1 with no traceback. Later stages define their own errors (Sleeper, LLM, render, delivery) as subclasses, so an unattended run fails cleanly into the log.
- Config path defaults to `config.toml` in the working directory and is overridable with `--config`.
- The data root defaults to `data/` and is overridable with `--data-dir` (used by tests).
- "Today" is the local calendar date; it is injectable for tests.

---

## Scope

### In Scope
- `uv` project, `pytest`, `mypy` (strict), `ruff` config, and a project type-check script
- CLI, config loading, run directory handling, pipeline orchestration, four stub stages
- Updating `CLAUDE.md` Commands section with real commands

### Out of Scope
- Real Sleeper, source, LLM, render, or delivery behavior
- Scheduling
- Secrets / `.env` (none needed)

---

## Technical Approach
- **Entry points / interfaces:** console script `ff-briefing = ff_briefing.cli:main` plus `python -m ff_briefing`. Use `argparse` from the stdlib (no new dependency). Commands: `run [--force]`, `fetch`, `synthesize`, `render`, `deliver`; global options `--config PATH`, `--data-dir PATH`. `main(argv: Sequence[str] | None = None) -> int` returns the exit code.
- **Layout:** `src/` layout, package `ff_briefing`. Python 3.12+ (`tomllib`). Build backend `hatchling`. Dev deps in a `dev` dependency group: `pytest`, `mypy`, `ruff`.
- **Test layout:** `tests/` is a package (`tests/__init__.py`), and any test subdirectory later stories add (e.g. `tests/sleeper/`, `tests/sources/`) gets its own `__init__.py`, so same-named test modules in different subdirectories don't collide under pytest's default import mode. Shared test helpers are imported as `tests.<module>` (e.g. `from tests.fakes import ...`).
- **Type-check script:** the project gate is `uv run mypy` with mypy configured in `pyproject.toml` (`strict = true`, `files = ["src", "tests"]`), so a bare `uv run mypy` is the gate. Record it in `CLAUDE.md` Commands alongside `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, and `uv run ff-briefing run`.
- **Key modules:**
  - `config.py`: loads and validates `config.toml`; raises `ConfigError(Exception)` with a user-readable message.
  - `rundir.py`: resolves `<data_dir>/<YYYY-MM-DD>/` and the file names below.
  - `pipeline.py`: `run_pipeline`, `run_stage`, idempotence check. Stage functions are held in an ordered registry so the CLI and `run` share one list.
  - `stages/*.py`: one stub per stage.
  - `errors.py`: `class BriefingError(Exception)`, the base for `ConfigError`, `MissingInputError`, and every later stage's errors.
  - `cli.py`: argument parsing, error-to-exit-code mapping (any `BriefingError` prints `error: <msg>` to stderr, returns 1).
- **Data model / on-disk stage contract** (the interface later stories build on). All files live in `<data_dir>/<YYYY-MM-DD>/`:

  | Stage | Reads | Writes |
  |---|---|---|
  | fetch | config | `sleeper.json`, `sources.json` |
  | synthesize | `sleeper.json`, `sources.json` | `briefing.md` |
  | render | `briefing.md` | `briefing.html` |
  | deliver | `briefing.html` | nothing (side effect only) |

  The final briefing, whose existence triggers the per-day skip, is `briefing.html`. Stub content: `sleeper.json` is `{}`, `sources.json` is `{"sources": []}`, `briefing.md` is a placeholder heading with the date, `briefing.html` is a minimal HTML document wrapping it. Later stories own the real JSON shapes of `sleeper.json` / `sources.json` and document them.
- **Exposed contract** (names and signatures later specs import):
  ```python
  # config.py
  @dataclass(frozen=True)
  class Config:
      sleeper_username: str
      source_urls: list[str]
  class ConfigError(BriefingError): ...
  def load_config(path: Path) -> Config: ...

  # rundir.py
  class MissingInputError(BriefingError): ...
  @dataclass(frozen=True)
  class RunDir:
      path: Path
      @property
      def sleeper_json(self) -> Path: ...    # path / "sleeper.json"
      @property
      def sources_json(self) -> Path: ...    # path / "sources.json"
      @property
      def briefing_md(self) -> Path: ...     # path / "briefing.md"
      @property
      def briefing_html(self) -> Path: ...   # path / "briefing.html"
      def require(self, file: Path, produced_by: str) -> Path: ...  # raises MissingInputError if absent
  def run_dir_for(data_dir: Path, day: date) -> RunDir: ...  # creates the directory

  # pipeline.py
  class StageFn(Protocol):
      def __call__(self, config: Config, run_dir: RunDir, today: date) -> None: ...
  STAGES: Mapping[str, StageFn]   # ordered: fetch, synthesize, render, deliver
  def run_stage(name: str, config: Config, data_dir: Path, today: date, stages: Mapping[str, StageFn] = STAGES) -> None: ...
  def run_pipeline(config: Config, data_dir: Path, today: date, force: bool = False, stages: Mapping[str, StageFn] = STAGES) -> bool: ...  # False if skipped
  ```
  **Pipeline tests must inject fake stages via `stages=`, never run the real registry.** Later stories replace the stubs with stages that hit the network, call `claude -p`, and open a browser; orchestration tests that ran the real registry would start doing all of that. The fake stages write the same files through `RunDir`, so handoff and idempotence are still proven. CLI tests likewise monkeypatch `run_pipeline` / `run_stage` for both `run` and per-stage dispatch.
  Every stage has the uniform signature `(config, run_dir, today) -> None`; stages read inputs only via `RunDir` properties and write only their own outputs. Later stories replace the body of `stages/<name>.py` and keep the signature. Delivery's side effect (`open`) is injected by the later delivery story; the stub does nothing.
- **Config shape** (`config.example.toml`, checked in; `config.toml` is the user's copy and is committed only if it holds nothing private — it holds none):
  ```toml
  [sleeper]
  username = "your_sleeper_username"

  [sources]
  urls = ["https://example.com/feed.xml"]
  ```
  `sleeper.username` required non-empty string; `sources.urls` required list of strings (may be empty). Unknown keys are ignored so later stories can extend the file.
- **Key design decisions:** Writes are plain files (JSON / markdown / HTML) so each stage is inspectable and re-runnable. `briefing.html` as the skip marker means a run that failed before render re-runs next time. Stage functions take `today` explicitly rather than reading the clock, keeping them deterministic. `argparse` over a CLI framework to avoid dependencies.

---

## Success Criteria
- [ ] `uv run ff-briefing run` with a valid config creates `data/<today>/` containing exactly `sleeper.json`, `sources.json`, `briefing.md`, `briefing.html`.
- [ ] `run_pipeline` returns `False` and leaves existing files' bytes unchanged when `briefing.html` already exists for the day; `force=True` returns `True` and rewrites all four files.
- [ ] `run_pipeline` for a day whose directory exists but lacks `briefing.html` runs all stages (returns `True`).
- [ ] `run_stage("synthesize", ...)` on a run dir with `sleeper.json` and `sources.json` writes `briefing.md` without running fetch; `run_stage("render", ...)` reads only `briefing.md` and writes `briefing.html`.
- [ ] `run_stage("render", ...)` with no `briefing.md` raises `MissingInputError` whose message contains `briefing.md` and `synthesize`; the CLI prints it as `error: ...` and exits 1 without a traceback.
- [ ] The CLI `run` subcommand wires `--force` through to `run_pipeline` (CLI-level test with the pipeline injected/monkeypatched), and `--config` / `--data-dir` through to loading and the run directory.
- [ ] `load_config` returns a `Config` with `sleeper_username == "<value>"` and `source_urls` equal to the TOML list for a valid file.
- [ ] `load_config` raises `ConfigError` for: nonexistent file (message contains the path), invalid TOML, missing `sleeper.username`, empty `sleeper.username`, `sources.urls` not a list of strings; each message names the offending key or file.
- [ ] `uv run mypy`, `uv run pytest`, `uv run ruff check`, and `uv run ruff format --check` all pass.
- [ ] `CLAUDE.md` Commands section lists the real test, type-check, lint, and run commands.

---

## Tasks
- [ ] **Project scaffolding (verify by running, no RED tests):** `pyproject.toml` (src layout, hatchling, Python >=3.12, `ff-briefing` script, `dev` group with pytest/mypy/ruff, strict mypy config, ruff config), package skeleton, `config.example.toml`, `uv sync`. Confirm `uv run mypy`, `uv run pytest` (zero tests ok), and `uv run ruff check` execute.
- [ ] **Config loading (TDD):** `config.py` with `Config`, `ConfigError`, `load_config`; tests in `tests/test_config.py` covering the valid case and each error case via `tmp_path` TOML files. Must be fully tested before the next task.
- [ ] **Run directory and pipeline (TDD):** `rundir.py`, `pipeline.py`, and the four stub stages. Tests in `tests/test_rundir.py` and `tests/test_pipeline.py` for idempotence (skip, `--force`, partial dir), stage handoff via files, and `MissingInputError`. Inject `today` and use `tmp_path` as the data dir.
- [ ] **CLI (TDD for wiring of args/errors, scaffold the rest):** `cli.py`, `__main__.py`; `tests/test_cli.py` covers `--force` / `--config` / `--data-dir` plumbing, per-stage subcommand dispatch, and error-to-exit-code mapping for any `BriefingError` subclass (`ConfigError`, `MissingInputError`). Then do one real `uv run ff-briefing run` in a scratch dir and a second to confirm the skip.
- [ ] **Docs:** update `CLAUDE.md` Commands section with the real commands and a short note that the stage contract lives in `rundir.py` / `pipeline.py`.

---

## Considerations
- Do not test argparse behavior itself (unknown flags, required args) or that tool configs are set.
- Stage file names are the shared contract; sibling specs (Sleeper fetch, source fetch, synthesis, render, delivery) import `RunDir` properties rather than hard-coding file names.
- The fetch stage writes both `sleeper.json` and `sources.json`; Sleeper and source fetch stories each own filling one of them. The stub fetch should be structured as two small helper functions (`_fetch_sleeper`, `_fetch_sources`) so those stories can replace them independently without file overlap beyond `stages/fetch.py`.
- `data/` is already gitignored; do not commit run output.
- Write files with `encoding="utf-8"`; JSON with `indent=2`.
- Do not cite story or spec numbers in code comments or test names.
