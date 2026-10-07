---
number: 006
story: STR-006
status: complete
base_branch: main
depends_on: [STR-001, STR-005]
scope_files:
  - src/ff_briefing/stages/deliver.py
  - tests/test_deliver.py
  - tests/test_pipeline.py
  - CLAUDE.md
---

# Feature: Delivery

## Summary
Delivery is the last pipeline stage. When a run produces a new day's briefing, it opens the rendered HTML file in the user's default browser using macOS `open`. A run skipped by the per-day idempotence rule opens nothing. If the HTML file is missing, delivery fails with a clear error. The `open` call is an injected side effect; only the logic around it is tested.

---

## Reconciliation with the skeleton (authoritative; overrides conflicting text below)
The package is `ff_briefing`, and the skeleton already provides most of the wiring this spec describes.
- **Orchestration is already done:** the skeleton's `run_pipeline` skips the whole run (no stage runs, so no `open`) when `briefing.html` exists, and runs all four stages, deliver last, otherwise; `--force` re-runs all four. No change to `pipeline.py` or `cli.py`. The standalone `deliver` subcommand also already exists and dispatches through the stage registry. The "orchestration wiring" and "CLI subcommand" tasks reduce to tests.
- **Stage:** `stages/deliver.py` already exists as a no-op stub with signature `(config, run_dir, today) -> None`. Replace its body with a call to `deliver(run_dir.briefing_html)`. Keep the testable `deliver(html_path, opener)` function and `DeliveryError` as specified, with `DeliveryError` subclassing the skeleton's `BriefingError`.
- **Injection:** give `deliver` the parameter `opener: Opener | None = None` and resolve `opener or open_in_browser` at call time. That lets pipeline tests monkeypatch `open_in_browser` on the module, because `run_pipeline`'s signature is fixed and has no opener argument.
- **Orchestration tests** (new, skipped, forced) go in the skeleton's existing `tests/test_pipeline.py`; extend it rather than adding a parallel file. Pass `run_pipeline` a `stages=` mapping where fetch, synthesize, and render are fakes that write files through `RunDir` and deliver is the real deliver stage, with `open_in_browser` monkeypatched to a recorder. Never run the real registry in tests. A missing HTML file on `deliver` comes from `DeliveryError`, which the CLI maps to exit 1 via `BriefingError`.

---

## Requirements
- After a run that produced a new briefing, the day's HTML file is opened with macOS `open`.
- A run skipped because today's final briefing already exists does not open anything.
- If the HTML file does not exist, delivery raises a clear error naming the missing path, and `open` is not invoked.
- If `open` itself exits non-zero, delivery raises a clear error (not a silent success).
- Delivery can be run alone as a stage subcommand against the already-rendered file for a given day (consistent with the other stages), and in that mode always opens (an explicit request is not a "skip").

---

## Scope

### In Scope
- `deliver` stage function with an injectable opener
- Default opener that shells out to `open <path>`
- Wiring into the `run` orchestration so it runs after render only when a new briefing was produced
- Standalone `deliver` subcommand

### Out of Scope
- Email, notifications, terminal/Ghostty display, any other channel
- Verifying that `open` actually displays a page (verified manually by running once)
- Choosing the browser (default browser only)
- The idempotence rule itself and the render stage (owned by the dependencies)

---

## Technical Approach
- **Entry points / interfaces:** a `deliver` subcommand on the CLI, and a final step in the `run` orchestration after render.
- **Key modules:**
  - `stages/deliver.py`: the stage logic and the default opener.
  - The `run` orchestration (location per the STR-001 skeleton; assumed `pipeline.py`) calls `deliver` only when the render stage actually ran this invocation.
- **Interface assumptions (the STR-001 and STR-005 specs did not exist when this was written; the implementer must reconcile with the actual code and adapt paths/names, keeping the exposed contract below intact):**
  - The render stage persists the day's HTML to a known path in the dated output directory, and the path is derivable from the same helper the idempotence check uses ("final briefing" file).
  - The `run` orchestration knows whether it skipped (idempotence) or executed the stages; the skip decision is made before any stage runs, so a skipped run never reaches deliver. If the skeleton returns a result/flag instead, key off that.
  - `--force` re-runs all stages, so it produces a new briefing and therefore delivers.
- **Exposed contract:**
  - `Opener = Callable[[Path], None]`
  - `def open_in_browser(path: Path) -> None` — runs `subprocess.run(["open", str(path)], check=False)` and raises `DeliveryError` on non-zero return code.
  - `def deliver(html_path: Path, opener: Opener = open_in_browser) -> None` — raises `DeliveryError` if `html_path` is not an existing file (without calling `opener`); otherwise calls `opener(html_path)` exactly once.
  - `class DeliveryError(Exception)` — message includes the path; use the project's existing error type/CLI error-to-exit-code handling if STR-001 defined a base class (subclass it).
- **Key design decisions:** the opener is injected so tests never launch a browser; the skip logic stays in the orchestration (single owner of idempotence) rather than duplicated inside `deliver`.

---

## Success Criteria
- [ ] `deliver(path, opener=fake)` with an existing file calls `fake` exactly once with that path.
- [ ] `deliver(missing_path, opener=fake)` raises `DeliveryError` whose message contains the missing path, and `fake` is never called.
- [ ] `open_in_browser` raises `DeliveryError` when the subprocess returns non-zero (subprocess run is monkeypatched; no real `open`).
- [ ] Orchestration test with a fake opener: a run that renders a new briefing calls the opener once with that day's HTML path.
- [ ] Orchestration test with a fake opener: a run skipped by the per-day rule (today's briefing already exists) never calls the opener.
- [ ] Orchestration test: a run with `--force` over an existing briefing calls the opener once.
- [ ] The `deliver` subcommand opens the existing file for the given day, and exits non-zero with the clear error when the file is missing.
- [ ] Manual verification, once: running the real pipeline (or `deliver`) on this Mac opens the HTML in the default browser.
- [ ] `uv run mypy`, `ruff`, and `pytest` pass using the project's commands.

---

## Tasks
- [ ] **Deliver stage logic (TDD):** `stages/deliver.py` with `DeliveryError`, `deliver`, and `open_in_browser`. Tests in `tests/test_deliver.py`: opener called once on existing file; missing file raises and opener not called; non-zero `open` exit raises. Fully tested before next task.
- [ ] **Orchestration wiring (TDD):** add the deliver step to `run` so it runs after render only when a new briefing was produced; make the opener injectable through the orchestration entry point for tests. Tests in `tests/test_pipeline.py` for new / skipped / forced cases. Extend existing pipeline tests rather than adding a parallel describe/file if STR-001 already created them.
- [ ] **CLI subcommand:** register `deliver` for standalone use, mapping `DeliveryError` to the CLI's existing error handling. Thin wiring; verify by running, plus the missing-file case if the CLI error mapping is testable per the skeleton's pattern.
- [ ] **Manual verification and docs:** run once for real and confirm the browser opens; add the deliver command to CLAUDE.md Commands if that section is by then populated.

---

## Considerations
- Do not test that `open` works or that the shell is invoked with particular flags beyond the non-zero-exit handling; the one-line side effect is verified by running it.
- Pass the path as an absolute path to `open` so it works regardless of the launchd working directory.
- launchd runs in the GUI session, so `open` displays the page; no extra handling needed here.
- Test names should state behavior (e.g. "does not open when the day's briefing already exists"), with no spec or story numbers in code or tests.
