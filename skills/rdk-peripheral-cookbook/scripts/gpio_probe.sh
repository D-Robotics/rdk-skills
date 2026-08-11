#!/bin/bash
# gpio_probe.sh — Read-only GPIO and CAN probe for RDK boards.
#
# Reads GPIO line count (via libgpiod gpioinfo) and CAN interface state
# — so the agent can verify "is the GPIO line visible / is CAN up" before
# advising wiring commands.
#
# Output: JSON {"ok":true,"off_platform":false,"reason":"","fields":{"gpio_lines":N,"can_interfaces":[...],"can0_state":"..."}}
# Non-board: {"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}
# Board but libgpiod missing: reason set to "libgpiod not found"
#
# Principles: read-only (no gpioset, no config writes); idempotent;
# no libgpiod → degrade with install hint; bash-only.
# Usage: bash gpio_probe.sh

set -euo pipefail

# --- Check if we're on an RDK board ---
if [ ! -d /sys/class/socinfo ]; then
    echo '{"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}'
    exit 0
fi

# --- GPIO lines via gpioinfo (libgpiod) ---
gpio_lines=-1
gpio_note=""
if command -v gpioinfo >/dev/null 2>&1; then
    # Count total GPIO lines across all chips
    count=$(gpioinfo 2>/dev/null | grep -c '^\s*line' || true)
    if [ -n "$count" ] && [ "$count" -gt 0 ] 2>/dev/null; then
        gpio_lines=$count
    else
        # Fallback: count non-header lines
        count=$(gpioinfo 2>/dev/null | tail -n +3 | wc -l || true)
        gpio_lines=${count:-0}
    fi
else
    gpio_note="libgpiod not installed: please install gpiod package"
fi

# --- CAN interfaces (scan /sys/class/net/ for can*) ---
can_interfaces=""
can0_state="none"
if [ -d /sys/class/net ]; then
    found_can=$(find /sys/class/net -maxdepth 1 -name 'can*' -printf '%f\n' 2>/dev/null | sort | tr '\n' ' ' | sed 's/ /", "/g; s/^/"/; s/", "$//')
    if [ -n "$found_can" ]; then
        can_interfaces="${found_can}"
        # Check can0 state if it exists
        if [ -f /sys/class/net/can0/operstate ]; then
            can0_state=$(cat /sys/class/net/can0/operstate 2>/dev/null | tr -d '\n')
        fi
    fi
fi
[ -z "$can_interfaces" ] && can_interfaces="\"none\""

# --- Emit JSON (contract: ok/off_platform/reason/fields) ---
echo '{"ok":true,"off_platform":false,"reason":"'"${gpio_note}"'","fields":{'
echo "  \"gpio_lines\": ${gpio_lines},"
echo "  \"can_interfaces\": [${can_interfaces}],"
echo "  \"can0_state\": \"${can0_state}\""
echo '}}'
