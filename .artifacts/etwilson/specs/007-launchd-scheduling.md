---
number: 007
story: STR-007
status: ready
base_branch: main
depends_on: [STR-001, STR-002, STR-003, STR-004, STR-005, STR-006]
scope_files:
  - launchd/com.ff-daily-briefing.plist.template
  - scripts/install-launchd.sh
  - scripts/uninstall-launchd.sh
  - docs/scheduling.md
  - README.md
  - CLAUDE.md
---

# Feature: launchd Scheduling

## Summary
A launchd user agent runs the full briefing pipeline once a day on the user's Mac with no one invoking it. It uses a calendar interval, so a run missed while the Mac was asleep fires on wake. Because launchd starts jobs with a minimal environment, the agent uses absolute paths for the project's Python environment and working directory and writes stdout and stderr to known log files. An install script and an uninstall script, documented in `docs/scheduling.md`, add and remove the agent. Same-day reruns do nothing because the pipeline is idempotent per day; the scheduler adds no idempotence logic of its own.

---

## Requirements
- Installing the agent registers a launchd user agent in the user's GUI session that runs the full pipeline once per day at a fixed local time.
- If the Mac was asleep at the scheduled time, the job runs on wake.
- The job runs with the project directory as its working directory, and invokes the project's Python environment by absolute path.
- The job's `PATH` includes the directories containing `uv` and `claude`, so the synthesis stage's `claude -p` call resolves.
- The agent's environment does not set `ANTHROPIC_API_KEY`.
- stdout and stderr go to files at a documented, stable location outside the repo.
- The install step is repeatable: running it again replaces the loaded agent instead of failing or duplicating it.
- The uninstall step unloads the agent and removes its plist, and tolerates the agent not being installed.
- The install script derives absolute paths from the checkout location, so no username or path is hardcoded in committed files.
- Running the job a second time on the same day exits successfully and does nothing, because of the pipeline's own idempotence.

---

## Scope

### In Scope
- A plist template with placeholders for absolute paths and the log directory
- Install and uninstall scripts that render the template into `~/Library/LaunchAgents/` and load or unload it
- Log files for stdout and stderr
- Instructions: install, uninstall, kick off a run manually (`launchctl kickstart`), where the logs are, how to verify an unattended run
- A short Commands entry in `CLAUDE.md` or README pointing to the instructions

### Out of Scope
- Battery, sleep, or lid-closed hardening beyond launchd's run-on-wake behavior
- `pmset` wake scheduling, retries, or failure alerts
- Any scheduler other than launchd
- Log rotation
- Any change to pipeline behavior, including idempotence logic (owned by the pipeline stories)

---

## Technical Approach
- **Entry points / interfaces:** `scripts/install-launchd.sh` and `scripts/uninstall-launchd.sh`, run by the user from the repo root. launchd executes the command defined in the rendered plist's `ProgramArguments`.
- **Key modules / components:**
  - `launchd/com.ff-daily-briefing.plist.template`: Label `com.ff-daily-briefing`; `ProgramArguments` = `<UV_PATH> run --project <PROJECT_DIR> <FULL_RUN_COMMAND>` (see Blockers for the command); `WorkingDirectory` = `<PROJECT_DIR>`; `StartCalendarInterval` = `{Hour: 7, Minute: 0}` (default time; the user edits the template to change it); `StandardOutPath` / `StandardErrorPath` = `<LOG_DIR>/stdout.log` and `stderr.log`; `EnvironmentVariables.PATH` set explicitly to include `<UV_DIR>`, `<CLAUDE_DIR>`, `/usr/bin:/bin:/usr/sbin:/sbin`. No `KeepAlive`. No `RunAtLoad`.
  - `scripts/install-launchd.sh`: resolves `PROJECT_DIR` from the script location, resolves `UV_PATH` and `CLAUDE_DIR` via `command -v` and fails with a clear message if either is missing, creates `~/Library/Logs/ff-daily-briefing/`, substitutes placeholders into `~/Library/LaunchAgents/com.ff-daily-briefing.plist`, runs `plutil -lint` on the result, then does `launchctl bootout` (ignore not-loaded) followed by `launchctl bootstrap gui/$(id -u)`.
  - `scripts/uninstall-launchd.sh`: `launchctl bootout gui/$(id -u)/com.ff-daily-briefing` (ignore not-loaded) then removes the plist file.
  - `docs/scheduling.md`: the instructions, plus the reasoning for the choices below.
- **Data model:** none. No Python is added. If a placeholder-substitution need grows beyond `sed`, move it to Python and TDD it; the base design does not require it.
- **Exposed contract:** none consumed by other code. Operational surface: launchd label `com.ff-daily-briefing`; plist at `~/Library/LaunchAgents/com.ff-daily-briefing.plist`; logs at `~/Library/Logs/ff-daily-briefing/{stdout,stderr}.log`.
- **Key design decisions:**
  - User agent bootstrapped into the `gui/<uid>` domain (not a daemon) so `claude -p` has the login session it needs.
  - `StartCalendarInterval` rather than `StartInterval` or cron, because launchd coalesces and runs a missed calendar job on wake.
  - No `RunAtLoad`: the story scopes triggering to the calendar interval, and it avoids a surprise browser window every time the agent is loaded (including by the install script).
  - Rendered plist is generated at install time, not committed, because it contains machine-specific absolute paths. Only the template is committed.
  - Verification is by installing and watching a real run, per the project testing approach; no tests restate the plist.

---

## Success Criteria
- [ ] After `scripts/install-launchd.sh`, `launchctl print gui/$(id -u)/com.ff-daily-briefing` shows the agent loaded and the rendered plist passes `plutil -lint`.
- [ ] The rendered plist contains `StartCalendarInterval` with `Hour` 7 and `Minute` 0, and contains no `RunAtLoad` or `KeepAlive` key.
- [ ] Every path in the rendered plist (`ProgramArguments[0]`, `WorkingDirectory`, log paths, PATH entries) is absolute and contains no unsubstituted placeholder.
- [ ] `launchctl kickstart gui/$(id -u)/com.ff-daily-briefing` runs the full pipeline unattended, writes that day's briefing HTML, and opens it in the default browser.
- [ ] stdout and stderr of that run appear in `~/Library/Logs/ff-daily-briefing/stdout.log` and `stderr.log`.
- [ ] Kickstarting again the same day exits without creating a second briefing or reopening one beyond whatever the pipeline's own idempotence defines.
- [ ] Running the install script twice leaves exactly one loaded agent and exits 0.
- [ ] `scripts/uninstall-launchd.sh` removes the agent and the plist; `launchctl print` for the label then fails; running it again exits 0.
- [ ] The install script exits non-zero with a clear message when `uv` or `claude` cannot be found.
- [ ] Final acceptance (epic done condition): one genuine scheduled run, with the Mac asleep through the scheduled time and woken afterward, executes unattended and the styled briefing opens in the browser.

---

## Tasks
- [ ] **Plist template:** Create `launchd/com.ff-daily-briefing.plist.template` with the keys listed under Key modules. Verify by rendering by hand and running `plutil -lint`. Depends on the pinned run command (Blockers).
- [ ] **Install and uninstall scripts:** Create `scripts/install-launchd.sh` and `scripts/uninstall-launchd.sh` (`set -euo pipefail`, idempotent, clear failure messages). Verify by running install twice, then uninstall twice, checking `launchctl print` after each.
- [ ] **Instructions:** Write `docs/scheduling.md` (install, uninstall, change the time, manual kickstart, log locations, how to verify an unattended run, why launchd and why no RunAtLoad). Add a Commands pointer in `CLAUDE.md` or README.
- [ ] **Unattended-run verification:** Install the agent, kickstart it, confirm the browser opens and logs fill; then confirm the asleep-through-schedule case. Record the result in the run's `decisions.md`. If any Python is later introduced for rendering the plist or computing paths, TDD it first.

---

## Considerations
- launchd's environment lacks the shell profile, so `.env` must be loaded by the application itself from the project directory (relying on `WorkingDirectory`), not by the shell. Confirm the skeleton's config loading resolves `.env` relative to the project or working directory, not `$HOME`.
- `ANTHROPIC_API_KEY` must stay unset. Do not export it in the plist. If it is present in the user's `.env`, that is a pipeline-level concern; the plist should not add to it.
- `command -v claude` at install time may resolve to an nvm or similar shim path; the PATH entry should use the resolved directory. If `claude` later moves, the user reruns install.
- launchd runs a missed calendar job on wake only while the user is logged in. A run missed across a full shutdown or logout is not recovered; this is accepted (out of scope hardening).
- Opening the browser at wake time may happen before the display is fully awake; observe while dogfooding and treat as follow-up, not part of this story.
- macOS may prompt for permission on first access to some directories (for example under `~/Documents`); the project path should avoid protected folders, or the doc should note it.
- Logs append indefinitely; rotation is out of scope.

---

## Resolved from the skeleton
- **Full-run command:** the console script is `ff-briefing` with subcommand `run` and no required arguments. `<FULL_RUN_COMMAND>` is `ff-briefing run`, so `ProgramArguments` is `<UV_PATH> run --project <PROJECT_DIR> ff-briefing run`. It exits 0 on success and on the already-done-today skip, and exits 1 with `error: <msg>` on stderr for any expected failure.
- **Skip suppresses `open`:** a skipped run executes no stages, so nothing opens.
- **`uv` may be a pyenv shim:** on this Mac, `command -v uv` resolves to `~/.pyenv/shims/uv`, which only works with pyenv's shell setup and will fail under launchd. The install script must resolve to the real binary: if the resolved path is under `.pyenv/shims`, use `pyenv which uv` (here `/opt/homebrew/bin/uv`), and fail clearly if that fails too.
- **Executor boundary:** the autonomous run does not install the agent into `~/Library/LaunchAgents`, kickstart it, or do the sleep test. It verifies the scripts with `bash -n` and by rendering the template into a temp file and running `plutil -lint` on that file. Installing, kickstarting, and the asleep-through-schedule acceptance are done by the user after the run; record them as pending in `decisions.md`.
- **No `.env`:** the pipeline has no secrets and no `.env`, so ignore the `.env` consideration above. The skeleton reads `config.toml` from the working directory, which `WorkingDirectory` sets. Before the first unattended run, `config.toml` must exist in the project directory (copy `config.example.toml` and fill in the Sleeper username and source URLs).
