#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-gpio-40pin: check Hobot.GPIO availability and 40PIN-related device nodes.
#
# Usage:
#   pin_check.sh

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

HOBOT_GPIO=false
if command -v python3 >/dev/null 2>&1; then
  if python3 -c "import Hobot.GPIO" >/dev/null 2>&1; then
    HOBOT_GPIO=true
  fi
fi

list_json() {
  # shellcheck disable=SC2068
  ls $@ 2>/dev/null | awk '{ printf "%s\"%s\"", (n++ ? ", " : ""), $1 }'
}

I2C_JSON="$(list_json /dev/i2c-*)"
SPI_JSON="$(list_json /dev/spidev*)"
UART_JSON="$(list_json /dev/ttyS*)"
PWM_JSON="$(ls -d /sys/class/pwm/pwmchip* 2>/dev/null | awk '{ printf "%s\"%s\"", (n++ ? ", " : ""), $1 }')"

cat <<EOF
{
  "board": "$RDK_BOARD",
  "hobot_gpio": $HOBOT_GPIO,
  "devices": {
    "i2c": [ $I2C_JSON ],
    "spi": [ $SPI_JSON ],
    "uart": [ $UART_JSON ],
    "pwm": [ $PWM_JSON ]
  }
}
EOF
