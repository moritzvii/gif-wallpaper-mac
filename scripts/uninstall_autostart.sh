#!/usr/bin/env bash
set -euo pipefail

LABEL="${LABEL:-com.moritzvonburen.dynamicwallpaper}"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"

launchctl bootout "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
rm -f "${PLIST_PATH}"

echo "Removed LaunchAgent: ${LABEL}"
