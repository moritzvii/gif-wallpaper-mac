#!/usr/bin/env bash
set -euo pipefail

LABEL="${LABEL:-com.moritzvonburen.dynamicwallpaper}"
FPS="${FPS:-2}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3)}"
PLAY_SCRIPT="${PROJECT_ROOT}/scripts/play_wallpaper.py"
FRAMES_DIR="${FRAMES_DIR:-${PROJECT_ROOT}/video}"
LAUNCH_AGENTS_DIR="${HOME}/Library/LaunchAgents"
PLIST_PATH="${LAUNCH_AGENTS_DIR}/${LABEL}.plist"
LOG_DIR="${PROJECT_ROOT}/logs"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "python3 not found. Set PYTHON_BIN manually and retry."
  exit 1
fi

if [[ ! -f "${PLAY_SCRIPT}" ]]; then
  echo "Playback script not found: ${PLAY_SCRIPT}"
  exit 1
fi

mkdir -p "${LAUNCH_AGENTS_DIR}" "${LOG_DIR}"

cat > "${PLIST_PATH}" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${PYTHON_BIN}</string>
    <string>${PLAY_SCRIPT}</string>
    <string>--folder</string>
    <string>${FRAMES_DIR}</string>
    <string>--fps</string>
    <string>${FPS}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${PROJECT_ROOT}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/wallpaper.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/wallpaper.err.log</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "${PLIST_PATH}"
launchctl enable "gui/$(id -u)/${LABEL}"
launchctl kickstart -k "gui/$(id -u)/${LABEL}"

echo "Installed and started LaunchAgent: ${LABEL}"
echo "Plist: ${PLIST_PATH}"
echo "Logs: ${LOG_DIR}/wallpaper.out.log and ${LOG_DIR}/wallpaper.err.log"
