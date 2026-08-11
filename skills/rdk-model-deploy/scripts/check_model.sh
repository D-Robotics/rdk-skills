#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-model-deploy: pre-deployment sanity check for a .bin model.
#
# Usage:
#   check_model.sh --model <path.bin>

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
  RDK_BPU_ARCH="unknown"
  echo "warn: rdk-diagnostic detector not found; board identity degraded to rdk-unknown" >&2
fi
if [ "${RDK_BOARD:-unknown}" = "unknown" ]; then
  echo "not-an-rdk-host: run this script on a D-Robotics RDK device." >&2
  exit 2
fi

MODEL=""
while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="${2:-}"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$MODEL" ]; then
  echo "usage: check_model.sh --model <path.bin>" >&2
  exit 1
fi

EXISTS=false
[ -f "$MODEL" ] && EXISTS=true

MODEL_INFO_OK=false
if [ "$EXISTS" = true ] && command -v hrt_model_exec >/dev/null 2>&1; then
  if hrt_model_exec model_info --model_file="$MODEL"; then
    MODEL_INFO_OK=true
  fi
fi

cat <<EOF
{
  "model_file": "$MODEL",
  "exists": $EXISTS,
  "board": "$RDK_BOARD",
  "bpu_arch": "$RDK_BPU_ARCH",
  "model_info_ok": $MODEL_INFO_OK,
  "notes": [ "verify the .bin was compiled for $RDK_BPU_ARCH before deploying" ]
}
EOF
