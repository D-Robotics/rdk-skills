#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-memory-audit: baseline → reclaim → re-measure loop.
# Default is dry-run; pass --apply to actually drop caches (requires root).
#
# Usage:
#   reclaim_verify.sh [--apply]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

APPLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

mem_available() { awk '/^MemAvailable:/ {print $2}' /proc/meminfo; }

BEFORE="$(mem_available)"

if [ "$APPLY" -eq 0 ]; then
  cat <<EOF
{
  "mode": "dry-run",
  "before_available_kb": $BEFORE,
  "planned_actions": [ "sync", "echo 3 > /proc/sys/vm/drop_caches" ],
  "note": "re-run with --apply as root to execute and verify"
}
EOF
  exit 0
fi

if [ ! -w /proc/sys/vm/drop_caches ]; then
  echo "permission-denied: writing /proc/sys/vm/drop_caches requires root." >&2
  echo "Re-run as: sudo bash $SCRIPT_DIR/reclaim_verify.sh --apply" >&2
  exit 3
fi

sync
echo 3 > /proc/sys/vm/drop_caches
sleep 1

AFTER="$(mem_available)"

cat <<EOF
{
  "mode": "apply",
  "before_available_kb": $BEFORE,
  "after_available_kb": $AFTER,
  "reclaimed_kb": $(( AFTER - BEFORE ))
}
EOF
