#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-system-config: view/set CPU governor and view thermal trip points.
# Commands follow rdk_x_doc 02_System_configuration/04_frequency_management.md.
#
# Usage:
#   perf_mode.sh [status]      # read-only (default)
#   perf_mode.sh performance   # set all policies to performance (root)
#   perf_mode.sh ondemand      # restore default governor (root)

set -euo pipefail

CMD="${1:-status}"
case "$CMD" in
  status|performance|ondemand) ;;
  *) echo "usage: perf_mode.sh [status|performance|ondemand]" >&2; exit 1 ;;
esac

CPUFREQ=/sys/devices/system/cpu/cpufreq
THERMAL=/sys/devices/virtual/thermal/thermal_zone0

if [ ! -d "$CPUFREQ" ]; then
  echo "cpufreq-not-found: $CPUFREQ missing; is this an RDK/Linux host?" >&2
  exit 2
fi

set_governor() {
  local gov="$1" changed=0
  for pol in "$CPUFREQ"/policy*; do
    [ -w "$pol/scaling_governor" ] || {
      echo "permission-denied: writing $pol/scaling_governor requires root." >&2
      echo "Re-run as: sudo bash $0 $gov" >&2
      exit 3
    }
    echo "$gov" > "$pol/scaling_governor"
    changed=$((changed + 1))
  done
  echo "governor set to '$gov' on $changed policy(ies); note: resets after reboot." >&2
}

case "$CMD" in
  performance) set_governor performance ;;
  ondemand)    set_governor ondemand ;;
esac

# ── status (always printed, proves the change took effect) ──────────────────
POL_JSON=""
for pol in "$CPUFREQ"/policy*; do
  [ -d "$pol" ] || continue
  name="$(basename "$pol")"
  gov="$(cat "$pol/scaling_governor" 2>/dev/null || echo unknown)"
  cur="$(cat "$pol/scaling_cur_freq" 2>/dev/null || echo null)"
  max="$(cat "$pol/scaling_max_freq" 2>/dev/null || echo null)"
  [ -n "$POL_JSON" ] && POL_JSON+=", "
  POL_JSON+="{ \"policy\": \"$name\", \"governor\": \"$gov\", \"cur_khz\": $cur, \"max_khz\": $max }"
done

trip_c() {
  local f="$THERMAL/trip_point_${1}_temp"
  if [ -r "$f" ]; then
    awk -v t="$(cat "$f")" 'BEGIN { printf "%.1f", t / 1000 }'
  else
    printf 'null'
  fi
}

cat <<EOF
{
  "policies": [ $POL_JSON ],
  "thermal": { "boot_c": $(trip_c 0), "throttle_c": $(trip_c 1), "shutdown_c": $(trip_c 2) }
}
EOF
