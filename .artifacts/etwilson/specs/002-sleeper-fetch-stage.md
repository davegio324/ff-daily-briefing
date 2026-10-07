---
number: 002
story: STR-002
status: ready
base_branch: main
depends_on: [STR-001]
scope_files:
  - src/ff_briefing/stages/fetch.py
  - src/ff_briefing/sleeper/**
  - pyproject.toml
  - uv.lock
  - tests/sleeper/**
  - tests/test_sleeper_fetch_stage.py
  - tests/fixtures/sleeper/**
---

# Feature: Sleeper Fetch Stage

## Summary
Replaces the stub Sleeper fetch with a real, deterministic, read-only fetch over the raw Sleeper HTTP API. For the configured username it collects every NFL league the user is in for the current season, the user's roster and the league's scoring and waiver settings per league, and trending add/drop players annotated with whether each is available (unrostered) in each league. The result is persisted in the skeleton's stage output format so synthesis can consume it. Any Sleeper failure aborts the stage with a clear error and writes no output.

---

## Interface assumptions (STR-001 spec did not exist when this was written)
Reconcile against the STR-001 spec before implementation; adapt names, keep behavior.
- Config exposes `sleeper.username: str` (from `config.toml`), loaded via `tomllib` into a typed config object.
- A stage is a callable receiving the loaded config and a run context giving the output location for the day, and returning/persisting a JSON-serializable dict as that stage's output file (e.g. `sleeper.json`). The stub fetch for Sleeper is replaced in the pipeline's stage registry.
- A stage failure is signaled by raising an exception; the CLI turns it into a non-zero exit with a message. No output file is written on failure.
- Output file name for this stage: `sleeper.json` (rename if STR-001 dictates a convention).
If STR-001 defines a different mechanism for any of these, STR-001 wins.

---

## Reconciliation with the skeleton (authoritative; overrides conflicting text below)
The skeleton spec is now fixed and replaces the "Interface assumptions" section below.
- **Stage wiring:** there is no `stages/sleeper_fetch.py` stage and no registry change. The skeleton's `stages/fetch.py` is the single fetch stage writing both `sleeper.json` and `sources.json`. Replace only its `_fetch_sleeper` helper so it calls `fetch_sleeper(config.sleeper_username, client)` and writes the dict to `run_dir.sleeper_json` (`json`, `indent=2`, utf-8). Do not touch `_fetch_sources`. The stage signature stays `(config, run_dir, today)`.
- **Config:** use the skeleton's `Config.sleeper_username`; no config changes.
- **Failure:** `SleeperError` subclasses the skeleton's `BriefingError` so the CLI prints it cleanly. Call the Sleeper fetch before writing any file so a failure leaves no `sleeper.json`.
- **HTTP library:** use `httpx` with a timeout (this story adds it to `pyproject.toml`; the source fetch story reuses it).
- **Tests:** the stage test in `tests/test_sleeper_fetch_stage.py` calls the `fetch.py` helper with a fake client and a `tmp_path` run dir.

---

## Requirements
- For the configured username, output contains an entry for every NFL league that user is in for the current season (season taken from Sleeper's NFL state, not hardcoded).
- Each league entry includes the user's own roster (the roster whose `owner_id` equals the user's id), with player ids resolved to name, position, team and injury/status.
- Each league entry includes the league's scoring settings (`scoring_settings`) and `roster_positions`.
- Each league entry includes a waiver block read from Sleeper league settings: `waiver_type`, `waiver_day_of_week`, `waiver_clear_days`, `daily_waivers`, `daily_waivers_hour`, `waiver_budget`, plus the user's roster `waiver_position` and `waiver_budget_used`. Missing fields are emitted as null rather than invented.
- Each league entry includes the set of all rostered player ids in that league (all rosters), so free agents are identifiable.
- Output includes trending adds and trending drops (24h lookback), each resolved to name/position/team/status and annotated per league with `available: bool` (true when not rostered in that league).
- Players are resolved from one fetch of the full NFL player dump per run; only players referenced by the output (user rosters and trending) are kept in the persisted output, not the whole dump.
- Any HTTP error, timeout, non-JSON body, unknown username (null user), or zero leagues raises a clear error naming the failing request; no partial output is written.
- No request other than HTTP GET is ever made.

---

## Scope

### In Scope
- Read-only Sleeper client, response shaping, free-agent availability derivation, error handling, persistence via the stage format.
- Recorded fixtures and tests.

### Out of Scope
- Any write to Sleeper, MCP/LLM calls, interpreting or ranking data, multi-user support.
- Emitting the complete list of free agents (too large; availability is derived for trending players and is derivable for any player from the rostered ids).
- Caching the player dump across runs (one fetch per run; the run is already once-daily and idempotent).

---

## Technical Approach
- **Entry points / interfaces:** `fetch_sleeper(username: str, client: SleeperClient) -> dict` is the pure-ish core, called by a thin stage wrapper in `stages/sleeper_fetch.py` that builds the real client from config and persists the dict.
- **Key modules:**
  - `sleeper/client.py`: `SleeperClient` with one method per endpoint using `httpx` or `urllib` (pick whichever STR-001 already depends on; otherwise stdlib `urllib.request` with a timeout). Methods: `get_nfl_state()` -> `/v1/state/nfl`; `get_user(username)` -> `/v1/user/<username>`; `get_user_leagues(user_id, season)` -> `/v1/user/<user_id>/leagues/nfl/<season>`; `get_rosters(league_id)` -> `/v1/league/<id>/rosters`; `get_trending(kind)` -> `/v1/players/nfl/trending/<add|drop>?lookback_hours=24&limit=25`; `get_players()` -> `/v1/players/nfl`. Base URL `https://api.sleeper.app`. All failures raised as `SleeperError(message)`.
  - `sleeper/shape.py`: pure functions: `select_user_roster(rosters, user_id)`, `shape_waiver_settings(league, roster)`, `resolve_player(players, player_id)`, `build_league_entry(...)`, `build_trending(...)`.
  - `stages/sleeper_fetch.py`: orchestration and persistence.
  - The client is injected (a Protocol or the class with a fake substituted) so tests use fixture-backed fakes and never touch the network.
- **Data model (output JSON):**
  ```
  {
    "fetched_at": "<ISO8601>", "season": "2026", "username": str, "user_id": str,
    "leagues": [{
      "league_id": str, "name": str, "scoring_settings": {..}, "roster_positions": [..],
      "waiver": {"waiver_type": int|null, "waiver_day_of_week": int|null, "waiver_clear_days": int|null,
                 "daily_waivers": bool|null, "daily_waivers_hour": int|null, "waiver_budget": int|null,
                 "waiver_position": int|null, "waiver_budget_used": int|null},
      "roster": {"roster_id": int, "starters": [player_id], "players": [player_id], "reserve": [..]|null},
      "rostered_player_ids": [str]
    }],
    "trending": {"add": [{"player_id": str, "count": int, "available_in": {"<league_id>": bool}}],
                 "drop": [ same shape ]},
    "players": {"<player_id>": {"name": str, "position": str|null, "team": str|null, "status": str|null, "injury_status": str|null}}
  }
  ```
- **Exposed contract (consumed by synthesis):** the JSON shape above, written to `sleeper.json`; the Python entry `fetch_sleeper(username: str, client: SleeperClient) -> dict[str, Any]` and `class SleeperError(Exception)`.
- **Key design decisions:**
  - Free agents derived locally from rostered ids rather than an endpoint (Sleeper has none); the player dump is fetched once per run and filtered, to keep output small and the large call sparing.
  - Waiver timing is read from league `settings` (the documented fields above are the contract; exact semantics of `waiver_day_of_week` are passed through unmodified for synthesis to interpret).
  - Fail whole-stage on any error: partial data would mislead synthesis.
  - Unknown player ids (absent from the dump) are kept with name null rather than dropped.

---

## Success Criteria
- [ ] Given fixtures for a user in two leagues, output `leagues` has exactly two entries with the correct `league_id`s.
- [ ] Each league's `roster.players` equals the `players` of the roster whose `owner_id` is the user's id, not another team's.
- [ ] Each league's `scoring_settings` equals the fixture's `scoring_settings` verbatim, and `waiver` contains the eight keys listed with values copied from fixture settings/roster (e.g. `waiver_day_of_week`, `waiver_clear_days`); a league missing a field yields `null` for that key.
- [ ] `rostered_player_ids` for a league is the union of players across all rosters in that league.
- [ ] A trending player rostered in league A but not league B has `available_in` `{A: false, B: true}`.
- [ ] `players` contains entries for every player id in user rosters and trending lists, and only those; an id missing from the dump appears with `name: null`.
- [ ] The player dump is requested exactly once and league rosters once per league (asserted on the fake client call log).
- [ ] Unknown username (null user body), `SleeperError` from any client call, or zero leagues makes the stage raise with a message identifying the failing step, and no `sleeper.json` is written.
- [ ] The stage wrapper writes `sleeper.json` in the run output location on success (persistence through the skeleton's mechanism).
- [ ] No test makes a network call; `uv run pytest`, `mypy`, and `ruff` pass.

---

## Tasks
- [ ] **Capture fixtures:** Create `tests/fixtures/sleeper/` with trimmed, realistic recorded JSON for state, user, two leagues, rosters (multiple teams per league), league settings with waiver fields, trending add/drop, and a small players dump (include one unknown-id case). Hand-trim from real responses; no secrets.
- [ ] **Shaping logic (TDD):** `sleeper/shape.py` pure functions for roster selection, waiver settings (null on missing), player resolution, rostered-id union, trending availability. Fully tested against fixtures before the next task.
- [ ] **Client + orchestration (TDD):** `sleeper/client.py` (`SleeperClient`, `SleeperError`, thin GETs with timeout; not separately unit-tested) and `fetch_sleeper` tested with a fixture-backed fake client: call counts, error propagation, null user, zero leagues.
- [ ] **Stage wiring:** `stages/sleeper_fetch.py` replacing the stub in the pipeline registry; persist `sleeper.json`; test that failure writes no file. Verify manually (not TDD) with a real run once if a username is configured.

---

## Considerations
- `GET /v1/players/nfl` is ~5MB+; Sleeper asks it be called at most about once a day. One call per run is within that, and the daily idempotence guard keeps it so.
- `waiver_type`, `waiver_day_of_week`, etc. live in each league object's `settings`; `scoring_settings` and `roster_positions` are top-level on the league object. Rosters carry `waiver_position`/`waiver_budget_used` under roster `settings`.
- Offseason or between-season states: the `league_season` from `/state/nfl` is used; if it yields zero leagues, error out clearly rather than emitting empty output.
- Do not reference spec/story numbers in code comments or test names.
- Tests name behaviors (e.g. "selects roster by owner id"), not changes.
