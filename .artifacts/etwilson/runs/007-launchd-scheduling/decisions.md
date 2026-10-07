# Decisions: 007-launchd-scheduling

- No RED tests or reviewer round: the spec adds no Python, and the project testing approach says not to force RED-first onto wiring (plist, shell scripts). Verified with `bash -n`, rendering to a temp file with `plutil -lint`, and a missing-`uv`/`claude` failure check. Skipped the reviewer gate for the same reason.
- Added `OUT_PLIST` and `SKIP_LOAD=1` env overrides to install-launchd.sh so rendering can be verified without touching `~/Library/LaunchAgents` or launchctl.
- Rendering also creates `~/Library/Logs/ff-daily-briefing/` (harmless).
- Commands pointer went in CLAUDE.md (replaced the "not yet defined" line); no README exists.

## Pending (manual, user)
- Run `scripts/install-launchd.sh` twice; confirm `launchctl print gui/$(id -u)/com.ff-daily-briefing`.
- `launchctl kickstart` and confirm briefing opens and logs fill; kickstart again to confirm skip.
- Run `scripts/uninstall-launchd.sh` twice; confirm `launchctl print` fails afterwards.
- Ensure `config.toml` exists in the project dir.
- Asleep-through-schedule acceptance test.
