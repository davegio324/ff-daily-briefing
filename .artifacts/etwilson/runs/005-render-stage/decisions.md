# Decisions: 005-render-stage

- Stage entry point is `run(config, run_dir, today)` per the skeleton; spec's `run_render` name not used.
- The skeleton had no atomic-write helper; `_write_atomic` (temp file in same dir + `os.replace`) lives in `stages/render.py`.
- Template/CSS task folded into the converter commit: the converter loads the template, so its tests could not go green without it.
- "No renderable content" test uses a reference-definition-only document; with `html=False` a bare HTML comment becomes an escaped paragraph, so it is not contentless.
- Title and body substituted in a single regex pass so placeholder-like text in either is not re-expanded.
- Task 3 stage tests for missing input and re-run passed at RED (skeleton stub already behaved that way); kept as regression guards.
- PENDING (manual, user): open a generated briefing.html in a browser and confirm it looks clean in light and dark system themes.
