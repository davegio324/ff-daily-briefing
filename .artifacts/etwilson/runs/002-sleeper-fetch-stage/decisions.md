# Decisions: 002-sleeper-fetch-stage

- Worked in the main checkout on the existing feature branch (no worktree), per lead instruction.
- `SleeperError` and the `SleeperClient` protocol live in `sleeper/client.py`; orchestration is in `sleeper/fetch.py` (`fetch_sleeper(username, client, now=None)`); `now` is injectable for deterministic tests.
- `_fetch_sleeper(config, run_dir, client=None)` builds `HttpSleeperClient` when no client is given, so `run()` is unchanged.
- Test fake and fixture loader live in `tests/sleeper/fakes.py` (shared by the stage test) since `tests/conftest.py` is outside spec scope.
- `HttpSleeperClient` is not unit-tested (thin GETs, per spec).
- Pending manual verification (user): run `uv run ff-briefing fetch` once with a real username to confirm live Sleeper responses match fixture shapes; `sleeper.json` is written.
