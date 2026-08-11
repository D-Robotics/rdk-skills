#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-camera-setup: scan board-specific I2C buses for camera sensors and list
# V4L2 devices. Bus numbers follow official docs:
#   X3: rdk_x_doc 08_FAQ/01_hardware_and_system.md  (i2c-1 / i2c-2)
#   X5: rdk_x_doc 01_Quick_start/hardware_introduction/rdk_x5.md (i2c-6 / i2c-4,
#       with GPIO353/GPIO351 sensor-enable sequence)
#
# Usage:
#   detect_camera.sh [--json|--human]

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

# board → camera I2C buses (per official docs)
case "$RDK_BOARD" in
  rdk-x5*)            BUSES="6 4" ;;
  rdk-x3*)            BUSES="1 2" ;;
  rdk-s100*|rdk-s600*) BUSES="1 2" ;; # S series: vcon-managed sensors on i2c bus 1/2 (rdk_s_doc)
  *)                  BUSES="1 2 4 6" ;; # fallback: scan common buses, report as-is
esac

# X5 only: pull sensor-enable GPIOs before probing (official sequence)
enable_x5_sensor_gpio() {
  local gpio="$1"
  [ -w /sys/class/gpio/export ] || return 0
  if [ ! -d "/sys/class/gpio/gpio${gpio}" ]; then
    echo "$gpio" > /sys/class/gpio/export 2>/dev/null || return 0
  fi
  echo out > "/sys/class/gpio/gpio${gpio}/direction" 2>/dev/null || return 0
  echo 0 > "/sys/class/gpio/gpio${gpio}/value" 2>/dev/null || return 0
  sleep 0.1
  echo 1 > "/sys/class/gpio/gpio${gpio}/value" 2>/dev/null || return 0
}
case "$RDK_BOARD" in
  rdk-x5*)
    enable_x5_sensor_gpio 353  # mipi_host0 (near ethernet, bus 6)
    enable_x5_sensor_gpio 351  # mipi_host2 (bus 4)
    ;;
esac

I2C_READABLE=false
ADDRS_JSON=""
if command -v i2cdetect >/dev/null 2>&1; then
  for bus in $BUSES; do
    out="$(i2cdetect -y -r "$bus" 2>/dev/null || true)"
    [ -n "$out" ] || continue
    I2C_READABLE=true
    addrs="$(printf '%s\n' "$out" | awk 'NR > 1 {
      for (i = 2; i <= NF; i++) if ($i ~ /^[0-9a-f]{2}$/) printf "%s\"0x%s\"", (n++ ? ", " : ""), $i
    }')"
    [ -n "$ADDRS_JSON" ] && ADDRS_JSON+=", "
    ADDRS_JSON+="\"$bus\": [ ${addrs} ]"
  done
fi

BUSES_JSON="$(printf '%s' "$BUSES" | tr ' ' ',')"

V4L2_JSON="$(ls /dev/video* 2>/dev/null | awk '{
  printf "%s\"%s\"", (n++ ? ", " : ""), $1
}')"

PYDEV_PRESENT=false
[ -d /app/pydev_demo ] && PYDEV_PRESENT=true

if [ "$MODE" = "human" ]; then
  echo "board=$RDK_BOARD buses=$BUSES i2c_readable=$I2C_READABLE"
  echo "v4l2=${V4L2_JSON:-none} pydev_demo=$PYDEV_PRESENT"
  exit 0
fi

cat <<EOF
{
  "board": "$RDK_BOARD",
  "i2c": {
    "readable": $I2C_READABLE,
    "buses_scanned": [ $BUSES_JSON ],
    "detected_addrs": { $ADDRS_JSON }
  },
  "v4l2_devices": [ $V4L2_JSON ],
  "pydev_demo_present": $PYDEV_PRESENT
}
EOF
