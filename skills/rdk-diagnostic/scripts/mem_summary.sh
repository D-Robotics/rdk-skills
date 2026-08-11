#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-diagnostic: compact human-readable RAM / CMA / swap summary line.
#
# Usage:
#   mem_summary.sh [--short] [--watch] [--interval N]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=detect_rdk.sh
source "$SCRIPT_DIR/detect_rdk.sh" || true
if [ "${RDK_BOARD:-unknown}" = "unknown" ]; then
  echo "not-an-rdk-host: run this script on a D-Robotics RDK device." >&2
  exit 2
fi

SHORT=0
WATCH=0
INTERVAL=2
while [ $# -gt 0 ]; do
  case "$1" in
    --short)    SHORT=1; shift ;;
    --watch)    WATCH=1; shift ;;
    --interval) INTERVAL="${2:-2}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

mem_field() { awk -v k="$1" '$1 == k":" {print $2}' /proc/meminfo 2>/dev/null; }

print_line() {
  local total avail cma_total cma_free swap_total swap_free
  total="$(mem_field MemTotal)"
  avail="$(mem_field MemAvailable)"
  cma_total="$(mem_field CmaTotal)"
  cma_free="$(mem_field CmaFree)"
  swap_total="$(mem_field SwapTotal)"
  swap_free="$(mem_field SwapFree)"

  local used_mb avail_mb total_mb
  total_mb=$(( ${total:-0} / 1024 ))
  avail_mb=$(( ${avail:-0} / 1024 ))
  used_mb=$(( total_mb - avail_mb ))

  if [ "$SHORT" -eq 1 ]; then
    echo "RAM ${used_mb}/${total_mb}MB"
    return
  fi

  local cma_part="CMA n/a"
  if [ -n "${cma_total:-}" ]; then
    cma_part="CMA $(( (${cma_total} - ${cma_free:-0}) / 1024 ))/$(( ${cma_total} / 1024 ))MB"
  fi
  local swap_part="swap 0/0MB"
  if [ -n "${swap_total:-}" ] && [ "${swap_total}" -gt 0 ]; then
    swap_part="swap $(( (${swap_total} - ${swap_free:-0}) / 1024 ))/$(( ${swap_total} / 1024 ))MB"
  fi
  echo "[$RDK_BOARD] RAM ${used_mb}/${total_mb}MB | ${cma_part} | ${swap_part}"
}

if [ "$WATCH" -eq 1 ]; then
  while true; do
    print_line
    sleep "$INTERVAL"
  done
else
  print_line
fi
