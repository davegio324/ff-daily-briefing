# QA Review — 001-project-skeleton-and-stage-pipeline (2026-10-07)

## Duplicate coverage
- `test_stage_with_missing_input_raises_naming_file_and_producing_stage` (tests/test_pipeline.py) vs
  `test_require_on_a_missing_file_names_the_file_and_producing_stage` (tests/test_rundir.py).
  Same behavior: `MissingInputError` message names the missing file ("briefing.md") and producing stage ("synthesize").
  In the pipeline test the error is raised by `Recorder.render` (test-local fake) calling `run_dir.require`, so it only
  re-proves `RunDir.require`. The real stage behavior is already covered by `test_missing_markdown_raises_error_naming_expected_file`
  (tests/test_render_stage.py) and `test_missing_sleeper_output_fails_naming_the_file_without_calling_the_llm`
  (tests/test_synthesize_stage.py). Candidate to drop.

## Pointless / incorrect tests
- Same test as above, secondary angle: `test_stage_with_missing_input_raises_naming_file_and_producing_stage`
  (tests/test_pipeline.py) asserts behavior produced by the test's own fake stage, not by `run_stage`/`pipeline.py`.
  `run_stage` contributes nothing to the outcome.

Everything else reviewed (sleeper, sources, claude_cli, config, deliver, render, rundir, cli, stage tests) is distinct
seam coverage or unit-vs-composition and was left unflagged.
