# Scheduling the daily briefing with launchd

For an ESPN league using a scheduled Codex chat instead of this Python pipeline,
see [ESPN briefings with Codex](espn-codex.md).

A launchd user agent (`com.ff-daily-briefing`) runs `ff-briefing run` once a day at 07:00 local time.

## Prerequisites
- `config.toml` exists in the project directory (copy `config.example.toml`, fill in the Sleeper username and source URLs). The job runs with the project as its working directory and reads it from there.
- `uv` and `claude` are installed. The install script resolves both and bakes their directories into the job's `PATH`. If `uv` is a pyenv shim it resolves the real binary via `pyenv which uv`.
- Keep the checkout out of protected folders such as `~/Documents`, or macOS may prompt for access on the first unattended run.

## Install
From the repo root:

    scripts/install-launchd.sh

Rerunning replaces the loaded agent. Rerun it after moving the checkout or `claude`. The rendered plist is written to `~/Library/LaunchAgents/com.ff-daily-briefing.plist` and is not committed because it holds machine-specific paths.

## Uninstall

    scripts/uninstall-launchd.sh

Unloads the agent and deletes the plist. Safe to run when not installed.

## Change the time
Edit `StartCalendarInterval` in `launchd/com.ff-daily-briefing.plist.template`, then rerun the install script.

## Run it now

    launchctl kickstart gui/$(id -u)/com.ff-daily-briefing

Check it is loaded with `launchctl print gui/$(id -u)/com.ff-daily-briefing`.

## Logs
`~/Library/Logs/ff-daily-briefing/stdout.log` and `stderr.log`. They append forever; there is no rotation.

## Verify an unattended run
1. Install, then kickstart. The briefing HTML should be written and open in the default browser; both logs should show the run.
2. Kickstart again the same day: the pipeline's own idempotence makes it exit 0 without running stages or opening anything.
3. For the real check, leave the Mac asleep through 07:00, wake it while logged in, and confirm the briefing opens.

## Why these choices
- **User agent in `gui/<uid>`, not a daemon:** `claude -p` needs the login session.
- **`StartCalendarInterval`:** launchd coalesces and runs a missed calendar job on wake. `StartInterval` and cron do not give this. A run missed across a full shutdown or logout is not recovered.
- **No `RunAtLoad`:** otherwise every load, including the install script, would open a browser window.
- **No `KeepAlive`:** the job is a once-a-day run, not a service.
- **`ANTHROPIC_API_KEY` is not set** in the plist so `claude -p` uses the subscription.
