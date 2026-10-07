#!/usr/bin/env bash
# Render the launchd plist for this checkout and (re)load it into the GUI session.
# Optional: set OUT_PLIST and SKIP_LOAD=1 to render only (used for verification).
set -euo pipefail

LABEL="com.ff-daily-briefing"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$PROJECT_DIR/launchd/$LABEL.plist.template"
LOG_DIR="$HOME/Library/Logs/ff-daily-briefing"
PLIST="${OUT_PLIST:-$HOME/Library/LaunchAgents/$LABEL.plist}"

fail() { echo "error: $*" >&2; exit 1; }

UV_PATH="$(command -v uv || true)"
[[ -n "$UV_PATH" ]] || fail "uv not found on PATH"
# A pyenv shim only works with pyenv's shell setup, which launchd lacks.
if [[ "$UV_PATH" == *"/.pyenv/shims/"* ]]; then
    UV_PATH="$(pyenv which uv 2>/dev/null || true)"
    [[ -n "$UV_PATH" ]] || fail "uv is a pyenv shim and 'pyenv which uv' failed; install uv outside pyenv"
fi
UV_DIR="$(dirname "$UV_PATH")"

CLAUDE_PATH="$(command -v claude || true)"
[[ -n "$CLAUDE_PATH" ]] || fail "claude not found on PATH"
CLAUDE_DIR="$(dirname "$CLAUDE_PATH")"

mkdir -p "$LOG_DIR" "$(dirname "$PLIST")"

sed \
    -e "s|<UV_PATH>|$UV_PATH|g" \
    -e "s|<UV_DIR>|$UV_DIR|g" \
    -e "s|<CLAUDE_DIR>|$CLAUDE_DIR|g" \
    -e "s|<PROJECT_DIR>|$PROJECT_DIR|g" \
    -e "s|<LOG_DIR>|$LOG_DIR|g" \
    "$TEMPLATE" > "$PLIST"

plutil -lint "$PLIST" >/dev/null || fail "rendered plist failed plutil -lint: $PLIST"

if [[ "${SKIP_LOAD:-0}" == "1" ]]; then
    echo "rendered $PLIST (not loaded)"
    exit 0
fi

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed $LABEL (plist: $PLIST, logs: $LOG_DIR)"
