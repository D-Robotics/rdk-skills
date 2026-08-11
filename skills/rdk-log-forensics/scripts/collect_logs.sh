#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-log-forensics: read-only structured crash/log evidence collector.
# Sources: dmesg (err+), systemd failed units, coredumpctl / /var/crash,
# journalctl previous-boot availability.
#
# Usage:
#   collect_logs.sh [--json|--human] [--lines N]
#
# Read-only. Fields the host cannot provide are reported as null / false —
# never fabricated. Never reads credential or private user files.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Prefer the canonical detector from rdk-diagnostic; degrade gracefully when
# this skill is installed standalone (minimal RDK-marker fallback).
DETECT="$SCRIPT_DIR/../../rdk-diagnostic/scripts/detect_rdk.sh"
if [ -f "$DETECT" ]; then
  # shellcheck source=../../rdk-diagnostic/scripts/detect_rdk.sh
  source "$DETECT" || true
elif command -v hrut_somstatus >/dev/null 2>&1 || [ -d /sys/devices/system/bpu ]; then
  RDK_BOARD="rdk-unknown"
  echo "warn: rdk-diagnostic detector not found; board identity degraded to rdk-unknown" >&2
fi
if [ "${RDK_BOARD:-unknown}" = "unknown" ]; then
  echo "not-an-rdk-host: run this script on a D-Robotics RDK device." >&2
  exit 2
fi

MODE=json
LINES=5
while [ $# -gt 0 ]; do
  case "$1" in
    --json)  MODE=json; shift ;;
    --human) MODE=human; shift ;;
    --lines) LINES="${2:-5}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

json_escape() { sed 's/\\/\\\\/g; s/"/\\"/g' | tr -d '\r'; }

# ── kernel errors (dmesg err and above) ──────────────────────────────────────
KERN_READABLE=false
ERR_COUNT=null
ERRORS_JSON=""
if command -v dmesg >/dev/null 2>&1; then
  DMESG_OUT="$(dmesg --level=err,crit,alert,emerg 2>/dev/null || true)"
  if [ -n "$DMESG_OUT" ] || dmesg >/dev/null 2>&1; then
    KERN_READABLE=true
    ERR_COUNT="$(printf '%s' "$DMESG_OUT" | grep -c . || true)"
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      esc="$(printf '%s' "$line" | json_escape)"
      [ -n "$ERRORS_JSON" ] && ERRORS_JSON+=", "
      ERRORS_JSON+="\"$esc\""
    done < <(printf '%s\n' "$DMESG_OUT" | tail -n "$LINES")
  fi
fi

# ── failed systemd units ─────────────────────────────────────────────────────
FAILED_JSON=""
if command -v systemctl >/dev/null 2>&1; then
  while IFS= read -r unit; do
    [ -n "$unit" ] || continue
    [ -n "$FAILED_JSON" ] && FAILED_JSON+=", "
    FAILED_JSON+="{ \"unit\": \"$unit\", \"active\": \"failed\" }"
  done < <(systemctl --failed --no-legend --plain 2>/dev/null | awk '{print $1}')
fi

# ── coredumps ────────────────────────────────────────────────────────────────
COREDUMPCTL=null
if command -v coredumpctl >/dev/null 2>&1; then
  n="$(coredumpctl list --no-legend 2>/dev/null | grep -c . || true)"
  COREDUMPCTL="${n:-0}"
fi
VAR_CRASH=0
if [ -d /var/crash ]; then
  VAR_CRASH="$(ls -1 /var/crash 2>/dev/null | grep -c . || true)"
fi

# ── last boot cleanliness ────────────────────────────────────────────────────
PREV_BOOT=false
BOOT_CLEAN=null
if command -v journalctl >/dev/null 2>&1; then
  if journalctl -b -1 -n 1 >/dev/null 2>&1; then
    PREV_BOOT=true
    # A clean shutdown leaves a "Journal stopped" record at the end of -b -1.
    if journalctl -b -1 -n 20 --no-pager 2>/dev/null | grep -q "Journal stopped"; then
      BOOT_CLEAN=true
    else
      BOOT_CLEAN=false
    fi
  fi
fi

if [ "$MODE" = "human" ]; then
  echo "board=$RDK_BOARD kern_readable=$KERN_READABLE err_count=$ERR_COUNT failed_units=$(printf '%s' "$FAILED_JSON" | grep -c 'unit' || true)"
  echo "coredumpctl=$COREDUMPCTL var_crash_files=$VAR_CRASH prev_boot=$PREV_BOOT boot_clean=$BOOT_CLEAN"
  exit 0
fi

cat <<EOF
{
  "board": "$RDK_BOARD",
  "kernel": {
    "readable": $KERN_READABLE,
    "err_count": $ERR_COUNT,
    "recent_errors": [ $ERRORS_JSON ]
  },
  "failed_units": [ $FAILED_JSON ],
  "coredumps": { "coredumpctl": $COREDUMPCTL, "var_crash_files": $VAR_CRASH },
  "last_boot": { "clean": $BOOT_CLEAN, "previous_boot_available": $PREV_BOOT }
}
EOF
