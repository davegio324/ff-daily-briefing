#!/usr/bin/env bash
# Unload the launchd agent and remove its plist. Safe to run when not installed.
set -euo pipefail

LABEL="com.ff-daily-briefing"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$PLIST"
echo "uninstalled $LABEL"
