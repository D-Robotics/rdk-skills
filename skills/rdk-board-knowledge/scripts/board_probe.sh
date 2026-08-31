#!/bin/bash
# board_probe.sh — Read-only identity probe for RDK boards.
#
# Reads live /sys + /proc device-tree facts to answer "which board am I on?"
# deterministically, so the agent doesn't guess from memory.
#
# Output: JSON {"ok":true,"off_platform":false,"reason":"","fields":{"board_id":"...","som_name":"...","model":"...","os_version":"..."}}
# Non-board: {"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}
#
# Principles: read-only (no writes to /sys or /proc); idempotent; bash-only (no jq dep).
# Usage: bash board_probe.sh

set -euo pipefail

# --- Check if we're on an RDK board ---
if [ ! -d /sys/class/socinfo ]; then
    echo '{"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}'
    exit 0
fi

# --- Helper: read a sysfs/proc file safely, strip trailing null/newline ---
read_file() {
    local path="$1"
    if [ -r "$path" ]; then
        # device-tree files have trailing \0; strip it along with whitespace
        cat "$path" 2>/dev/null | tr -d '\0' | tr -d '\n' | sed 's/\\/\\\\/g; s/"/\\"/g'
    else
        echo ""
    fi
}

# --- Read board identity ---
board_id=$(read_file /sys/class/socinfo/board_id)
som_name=$(read_file /sys/class/socinfo/som_name)
model=$(read_file /proc/device-tree/model)

# OS version: /etc/version is the canonical, stable RDK OS release file on
# every supported image. rdkos_info (2.1.0+) prints a banner plus a
# "[RDK OS Version]:" section — take the version line only when present, and
# never pipe a long-running command through head (SIGPIPE on short reads).
os_version=""
if [ -r /etc/version ]; then
    os_version=$(cat /etc/version 2>/dev/null | tr -d '\r\n' | sed 's/\\/\\\\/g; s/"/\\"/g')
fi
if [ -z "$os_version" ] && command -v rdkos_info >/dev/null 2>&1; then
    os_version=$(rdkos_info 2>/dev/null | sed -n 's/^\[RDK OS Version\]:[[:space:]]*//p' | tr -d '\r\n' | sed 's/\\/\\\\/g; s/"/\\"/g')
fi

# --- Emit JSON (contract: ok/off_platform/reason/fields) ---
echo '{"ok":true,"off_platform":false,"reason":"","fields":{'
echo "  \"board_id\": \"${board_id}\","
echo "  \"som_name\": \"${som_name}\","
echo "  \"model\": \"${model}\","
echo "  \"os_version\": \"${os_version}\""
echo '}}'
