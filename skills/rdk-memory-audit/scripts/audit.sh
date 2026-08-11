#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-memory-audit: JSON memory audit for DRAM / CMA / swap / top RSS processes.
# Facts baseline: rdk_x_doc 09_Appendix/rdk-command-manual/cmd_rdkos_info.md
#
# Usage:
#   audit.sh [--label <name>]

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

LABEL="audit"
while [ $# -gt 0 ]; do
  case "$1" in
    --label) LABEL="${2:-audit}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

json_or_null() { [ -n "${1:-}" ] && printf '%s' "$1" || printf 'null'; }
mem_field() { awk -v k="$1" '$1 == k":" {print $2}' /proc/meminfo 2>/dev/null; }

TOP_JSON="$(ps -eo pid=,rss=,comm= --sort=-rss 2>/dev/null | head -n 5 | awk '{
  printf "%s{ \"pid\": %s, \"cmd\": \"%s\", \"rss_kb\": %s }", (n++ ? ", " : ""), $1, $3, $2
}')"

cat <<EOF
{
  "label": "$LABEL",
  "timestamp": "$(date +%Y-%m-%dT%H:%M:%S%z)",
  "board": "$RDK_BOARD",
  "memory_kb": {
    "total": $(json_or_null "$(mem_field MemTotal)"),
    "available": $(json_or_null "$(mem_field MemAvailable)"),
    "cached": $(json_or_null "$(mem_field Cached)"),
    "buffers": $(json_or_null "$(mem_field Buffers)")
  },
  "cma_kb": {
    "total": $(json_or_null "$(mem_field CmaTotal)"),
    "free": $(json_or_null "$(mem_field CmaFree)")
  },
  "swap_kb": {
    "total": $(json_or_null "$(mem_field SwapTotal)"),
    "free": $(json_or_null "$(mem_field SwapFree)")
  },
  "top_rss": [ $TOP_JSON ]
}
EOF
