---
number: 005
story: STR-005
status: ready
base_branch: main
depends_on: [STR-001, STR-004]
scope_files:
  - pyproject.toml
  - src/ff_briefing/stages/render.py
  - src/ff_briefing/render/__init__.py
  - src/ff_briefing/render/converter.py
  - src/ff_briefing/render/template.html
  - tests/test_render.py
  - tests/test_render_stage.py
---

# Feature: Render Stage

## Summary
The render stage turns the synthesized markdown briefing into a single self-contained HTML file (inline CSS, no external requests, readable in light and dark system themes) and writes it into the day's dated directory. That file is the "final briefing" artifact the per-day idempotence check looks for and the file delivery opens. Presentation lives in the project's own template and CSS, never in the prompt. Empty or malformed input fails loudly rather than producing a blank page.

---

## Reconciliation with the skeleton (authoritative; overrides "Interface assumptions" below)
- **Stage interface:** `stages/render.py` already exists as a stub with signature `(config, run_dir, today) -> None`. Replace its body. Read via `run_dir.require(run_dir.briefing_md, "synthesize")` (a missing file raises the skeleton's `MissingInputError` naming `briefing.md`). Write the final HTML to `run_dir.briefing_html` using the atomic write. Use those `RunDir` properties; do not add new filename constants.
- **Errors:** `RenderError` subclasses the skeleton's `BriefingError`.
- **Title:** built from `today` (for example `Fantasy briefing for 2026-10-07`).
- **Idempotence interaction:** `briefing.html` is the skeleton's skip marker, so the atomic write is what makes the skip safe.

---

## Requirements
- Given markdown containing headings, lists, tables and links, the output HTML renders each as the corresponding HTML element (`h1`-`h6`, `ul`/`ol`, `table`, `a href`).
- Source links in the markdown become clickable anchors with their original `href`.
- Per-league sections in the markdown (headings) appear as distinct headed sections in the HTML.
- The output is one file with all CSS inline and no references to external resources (no `<link>`, external `<script>`, remote fonts, remote images added by the template).
- The page declares a light and dark color scheme via `prefers-color-scheme`.
- Markdown that is empty or whitespace-only raises a clear render error and writes no output file.
- Markdown with no renderable body (for example, produces no block content after conversion) raises the same error and writes no output file.
- The HTML is written to the dated directory under the final-briefing filename defined by the pipeline skeleton; a re-run overwrites it atomically (no partial file left on failure).
- Missing input markdown file raises a clear error naming the expected path.
- Page title/heading includes the briefing date.
- Raw HTML in the markdown is escaped, not passed through (the briefing is LLM output and web-sourced).

---

## Scope

### In Scope
- Markdown to HTML conversion via a small library, wrapped in the project's template and CSS
- Stage entry point conforming to the pipeline's stage interface
- Error cases: empty, no-content, missing input
- Writing the dated final-briefing file

### Out of Scope
- Visual polish beyond clean and readable; multiple templates; JavaScript
- Changing briefing content (synthesis)
- Opening the file (delivery)
- Idempotence check logic itself (owned by the skeleton; this stage only produces the file it looks for)

---

## Technical Approach
- **Interface assumptions (to reconcile with the pipeline skeleton spec; none existed when this was written):**
  - Package is `ff_briefing` under `src/` (`uv` project).
  - Each stage is a callable receiving a run context carrying at least the dated run directory (`pathlib.Path`) and the run date (`datetime.date`), and persisting its output to disk. The synthesis stage writes the briefing markdown to a known filename in that directory; the skeleton defines the filenames for synthesized markdown and the final HTML. The implementer must use the skeleton's constants/accessors for both names and the stage signature, and must not hard-code new names. If the skeleton does not expose them, add them there in the least invasive way and note it in the run decisions.
  - A shared pipeline error base class may exist in the skeleton; if so `RenderError` subclasses it, otherwise it subclasses `Exception`.
- **Key modules:**
  - `render/converter.py`: pure function, no I/O.
  - `render/template.html`: the page template with inline `<style>` and `{{title}}` / `{{body}}` placeholders, loaded via `importlib.resources` (package data must be included in the build in `pyproject.toml`).
  - `stages/render.py`: thin stage wrapper that reads markdown, calls the converter, writes the file atomically (write to temp file in the same directory, then `os.replace`).
- **Exposed contract:**
  - `class RenderError(Exception)`
  - `def render_html(markdown_text: str, title: str) -> str` raises `RenderError` on empty or no-content input; returns a complete HTML document string.
  - `def run_render(...)` stage entry point, signature per the skeleton's stage interface (assumed: takes the run context, returns None or the output `Path`, writes the final-briefing file).
- **Markdown library:** `markdown-it-py` (small, pure Python, CommonMark, tables enabled via `.enable("table")`, `html=False` so raw HTML is escaped). Add as a runtime dependency. Do not add heavier dependencies.
- **Template:** `<meta name="viewport">`, `color-scheme: light dark`, CSS variables switched in `@media (prefers-color-scheme: dark)`, readable max-width column, table borders, visible link styling. Title and body substituted via plain string replacement, with the title HTML-escaped.
- **Key design decisions:** pure converter plus thin I/O wrapper so errors are testable without disk; atomic write so a failed run never leaves a file the idempotence check would mistake for a finished briefing.

---

## Success Criteria
- [ ] `render_html("# Title\n\n- a\n- b\n\n[src](https://example.com/x)", "t")` output contains an `<h1>`, a `<ul>` with two `<li>`, and `<a href="https://example.com/x">`.
- [ ] A markdown table renders as `<table>` with `<th>` and `<td>` cells.
- [ ] Markdown with two `##` league headings yields two `<h2>` elements in order.
- [ ] Output contains no `<link`, no `<script src`, no `http://`/`https://` other than hrefs originating from the markdown (assert on a markdown with no links: output contains no `http`).
- [ ] Output contains `prefers-color-scheme: dark`.
- [ ] `render_html("", ...)` and `render_html("  \n\n", ...)` raise `RenderError`.
- [ ] Input `<script>alert(1)</script>` appears escaped (`&lt;script&gt;`) and not as a live tag.
- [ ] The title (with the date) appears in `<title>` and is HTML-escaped.
- [ ] Stage: given a run directory with valid markdown, the final-briefing HTML file exists at the skeleton-defined path and contains the rendered body.
- [ ] Stage: given empty markdown, `RenderError` is raised and no final-briefing file exists (and a pre-existing one is not clobbered).
- [ ] Stage: given a missing markdown file, an error naming the expected path is raised and no output file is written.
- [ ] Stage: re-running over an existing output replaces it with the new content.
- [ ] `uv run mypy` and `uv run ruff check` pass; the packaged template is found when running from the installed project (not only from the source tree).
- [ ] Manual: open one generated file in a browser and confirm it looks clean in light and dark system themes (verified by eye, not tested).

---

## Tasks
- [ ] **Converter (TDD):** Write failing tests in `tests/test_render.py` for the success criteria on `render_html` (elements, links, tables, headings, escaping, title, no-external-references, empty/no-content errors), then implement `render/converter.py` with `RenderError`. Do not test markdown-it-py itself; assert only on this project's observable behavior (escaping config, error handling, template wiring). Must be green before the next task.
- [ ] **Template and CSS:** Create `render/template.html` with inline CSS, light/dark scheme, readable layout; add `markdown-it-py` and package-data inclusion to `pyproject.toml`. Verify by running, no CSS-restating tests; the only test touching it is the dark-scheme/no-external-reference assertions above.
- [ ] **Stage wrapper (TDD):** Write failing tests in `tests/test_render_stage.py` using a `tmp_path` run directory for the stage criteria (writes final file, empty input leaves nothing/does not clobber, missing input error, overwrite on re-run), then implement `stages/render.py` with atomic write, using the skeleton's filenames and stage signature.
- [ ] **Gate and eyeball:** Run pytest, mypy, ruff; render one realistic sample briefing (multi-league, tables, links) and open it manually to confirm appearance in both themes.

---

## Considerations
- Filenames and the stage signature are owned by the pipeline skeleton; reconcile before implementing rather than inventing new ones.
- Whether delivery and the idempotence check treat "file exists" as complete: the atomic write is what makes that safe. Do not write the final path until rendering has succeeded.
- LLM output may wrap the whole briefing in a fenced code block or add preamble; this stage does not repair that (synthesis owns content). Only empty or contentless input is an error.
- Relative `href`s or `javascript:` links in markdown: markdown-it-py's default link validation rejects `javascript:` URLs; rely on that, do not add tests for it.
- Per-league structure is carried by the markdown headings the prompt asks for; the renderer does not infer leagues.
