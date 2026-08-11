#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-tros-setup: check TogetheROS.Bot installation and environment readiness.
# Env sourcing convention per official FAQ: source /opt/tros/setup.bash
#
# Usage:
#   tros_check.sh

set -euo pipefail

TROS_ROOT=/opt/tros

INSTALLED=false
DISTROS_JSON=""
if [ -d "$TROS_ROOT" ]; then
  INSTALLED=true
  # tros may install directly under /opt/tros or per-distro subdirs (e.g. humble)
  DISTROS_JSON="$(find "$TROS_ROOT" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | awk -F/ '{ printf "%s\"%s\"", (n++ ? ", " : ""), $NF }')"
fi

ROS2=false
command -v ros2 >/dev/null 2>&1 && ROS2=true

ENV_SOURCED=false
if [ -n "${AMENT_PREFIX_PATH:-}" ] && printf '%s' "${AMENT_PREFIX_PATH}" | grep -q "$TROS_ROOT"; then
  ENV_SOURCED=true
fi

HINT="ok"
if [ "$INSTALLED" = false ]; then
  HINT="tros not found under $TROS_ROOT; install per official docs for your board"
elif [ "$ENV_SOURCED" = false ]; then
  HINT="run: source $TROS_ROOT/setup.bash (or the distro-specific setup.bash)"
fi

cat <<EOF
{
  "tros_installed": $INSTALLED,
  "tros_root": "$TROS_ROOT",
  "distros": [ $DISTROS_JSON ],
  "ros2_available": $ROS2,
  "env_sourced": $ENV_SOURCED,
  "hint": "$HINT"
}
EOF
