#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-system-maintain: read-only maintenance health check for RDK OS.
# apt source facts follow official FAQ Q10:
#   rdk_x_doc 08_FAQ/01_hardware_and_system.md
#   (sunrise.list, archive.d-robotics.cc, /usr/share/keyrings/sunrise.gpg)
#
# Usage:
#   maintain_check.sh [--json|--human]
#
# Read-only. Fields the host cannot provide are reported as null / false —
# never fabricated. This script never modifies sources, locks, or files.

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
case "${1:-}" in
  ""|--json) MODE=json ;;
  --human)   MODE=human ;;
  *) echo "Unknown argument: $1" >&2; exit 1 ;;
esac

# ── apt sources (official FAQ Q10: sunrise.list + known stale domains) ───────
SRC_FILE="/etc/apt/sources.list.d/sunrise.list"
SRC_PRESENT=false
STALE_JSON=""
if [ -r "$SRC_FILE" ]; then
  SRC_PRESENT=true
  for dom in archive.sunrisepi.tech sunrise.horizon.cc ubuntu-rdk-s100-beta; do
    if grep -q "$dom" "$SRC_FILE" 2>/dev/null; then
      [ -n "$STALE_JSON" ] && STALE_JSON+=", "
      STALE_JSON+="\"$dom\""
    fi
  done
fi
GPG_PRESENT=false
[ -f /usr/share/keyrings/sunrise.gpg ] && GPG_PRESENT=true

# ── apt/dpkg lock ────────────────────────────────────────────────────────────
LOCK_HELD=false
LOCK_PID=null
if command -v fuser >/dev/null 2>&1; then
  pid="$(fuser /var/lib/dpkg/lock-frontend 2>/dev/null | tr -dc '0-9' || true)"
  if [ -n "$pid" ]; then
    LOCK_HELD=true
    LOCK_PID="$pid"
  fi
elif pgrep -x apt >/dev/null 2>&1 || pgrep -x apt-get >/dev/null 2>&1 || pgrep -x dpkg >/dev/null 2>&1; then
  LOCK_HELD=true
fi

# ── disk usage per mount ─────────────────────────────────────────────────────
DISK_JSON="$(df -P -x tmpfs -x devtmpfs -x overlay 2>/dev/null | awk 'NR > 1 {
  gsub(/%/, "", $5)
  printf "%s{ \"mount\": \"%s\", \"used_pct\": %s, \"avail_kb\": %s }", (n++ ? ", " : ""), $6, $5, $4
}')"

# ── large cleanable dirs (bounded scan, no full-disk du) ─────────────────────
LARGE_JSON=""
for d in /var/cache/apt /var/log /var/crash /tmp; do
  [ -d "$d" ] || continue
  kb="$(du -sk "$d" 2>/dev/null | awk '{print $1}' || true)"
  [ -n "$kb" ] || continue
  [ -n "$LARGE_JSON" ] && LARGE_JSON+=", "
  LARGE_JSON+="{ \"path\": \"$d\", \"size_kb\": $kb }"
done

# ── last successful apt metadata refresh ─────────────────────────────────────
LAST_UPDATE=null
if [ -d /var/lib/apt/lists ]; then
  ts="$(stat -c %Y /var/lib/apt/lists 2>/dev/null || stat -f %m /var/lib/apt/lists 2>/dev/null || true)"
  [ -n "$ts" ] && LAST_UPDATE="$ts"
fi

if [ "$MODE" = "human" ]; then
  echo "board=$RDK_BOARD sources_present=$SRC_PRESENT stale=[${STALE_JSON}] gpg=$GPG_PRESENT lock_held=$LOCK_HELD"
  echo "last_apt_update_epoch=$LAST_UPDATE"
  exit 0
fi

cat <<EOF
{
  "board": "$RDK_BOARD",
  "apt_sources": {
    "file": "$SRC_FILE",
    "present": $SRC_PRESENT,
    "stale_domains": [ $STALE_JSON ],
    "gpg_key_present": $GPG_PRESENT
  },
  "apt_lock": { "held": $LOCK_HELD, "holder_pid": $LOCK_PID },
  "disk": [ $DISK_JSON ],
  "large_dirs": [ $LARGE_JSON ],
  "last_apt_update_epoch": $LAST_UPDATE
}
EOF
