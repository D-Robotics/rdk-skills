#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-vision-pipeline: stage-by-stage readiness check for the end-to-end
# camera -> BPU inference -> HDMI/Web display pipeline. Sample and model paths
# follow official docs:
#   rdk_x_doc 03_Basic_Application/03_pydev_demo_sample (web_display, /app/model/basic)
#   rdk_x_doc 03_Basic_Application/06_multi_media_sp_dev_api (/opt/hobot/model)
#
# Usage:
#   pipeline_check.sh [--json|--human]
#
# Read-only. Fields the host cannot provide are reported as null / false —
# never fabricated.

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

# ── stage: camera (V4L2 nodes present) ──────────────────────────────────────
V4L2_JSON="$(ls /dev/video* 2>/dev/null | awk '{
  printf "%s\"%s\"", (n++ ? ", " : ""), $1
}')"
CAMERA_PASS=false
if [ -n "$V4L2_JSON" ]; then CAMERA_PASS=true; fi

# ── stage: samples (official pydev_demo + web_display sample) ───────────────
PYDEV_PRESENT=false
if [ -d /app/pydev_demo ]; then PYDEV_PRESENT=true; fi
WEB_SAMPLE="$(ls -d /app/pydev_demo/*web_display* 2>/dev/null | head -n1 || true)"
SAMPLES_PASS=$PYDEV_PRESENT
WEB_SAMPLE_JSON=null
if [ -n "$WEB_SAMPLE" ]; then WEB_SAMPLE_JSON="\"$WEB_SAMPLE\""; fi

# ── stage: model (preinstalled model dirs + hrt_model_exec) ─────────────────
MODEL_DIRS_JSON=""
for d in /app/model/basic /opt/hobot/model/*/basic; do
  [ -d "$d" ] || continue
  [ -n "$MODEL_DIRS_JSON" ] && MODEL_DIRS_JSON+=", "
  MODEL_DIRS_JSON+="\"$d\""
done
HRT_PRESENT=false
if command -v hrt_model_exec >/dev/null 2>&1; then HRT_PRESENT=true; fi
MODEL_PASS=false
if [ -n "$MODEL_DIRS_JSON" ]; then MODEL_PASS=true; fi

# ── stage: bpu (sysfs readable) ──────────────────────────────────────────────
BPU_READABLE=false
for node in /sys/devices/system/bpu/bpu*/ratio; do
  [ -r "$node" ] || continue
  BPU_READABLE=true
  break
done
BPU_PASS=$BPU_READABLE

# ── stage: display (any DRM connector reports connected) ────────────────────
HDMI_CONNECTED=false
for st in /sys/class/drm/*/status; do
  [ -r "$st" ] || continue
  if grep -q '^connected$' "$st" 2>/dev/null; then
    HDMI_CONNECTED=true
    break
  fi
done
DISPLAY_PASS=$HDMI_CONNECTED

# ── stage: web (nginx binary + port 80 listener) ─────────────────────────────
NGINX_PRESENT=false
if command -v nginx >/dev/null 2>&1; then NGINX_PRESENT=true; fi
PORT80=null
if command -v ss >/dev/null 2>&1; then
  if ss -ltn 2>/dev/null | awk '{print $4}' | grep -Eq '(^|:)80$'; then
    PORT80=true
  else
    PORT80=false
  fi
fi
WEB_PASS=$NGINX_PRESENT

# ── CMA/ION headroom signal ──────────────────────────────────────────────────
CMA_FREE="$(awk '$1 == "CmaFree:" {print $2}' /proc/meminfo 2>/dev/null || true)"
CMA_FREE_JSON="${CMA_FREE:-null}"

# ── first broken stage (camera -> samples -> model -> bpu -> output) ────────
FIRST_BROKEN=null
if   [ "$CAMERA_PASS" != true ];  then FIRST_BROKEN='"camera"'
elif [ "$SAMPLES_PASS" != true ]; then FIRST_BROKEN='"samples"'
elif [ "$MODEL_PASS" != true ];   then FIRST_BROKEN='"model"'
elif [ "$BPU_PASS" != true ];     then FIRST_BROKEN='"bpu"'
elif [ "$DISPLAY_PASS" != true ] && [ "$WEB_PASS" != true ]; then FIRST_BROKEN='"output"'
fi

if [ "$MODE" = "human" ]; then
  echo "board=$RDK_BOARD camera=$CAMERA_PASS samples=$SAMPLES_PASS model=$MODEL_PASS bpu=$BPU_PASS display=$DISPLAY_PASS web=$WEB_PASS"
  echo "first_broken_stage=$FIRST_BROKEN cma_free_kb=${CMA_FREE:-n/a}"
  exit 0
fi

cat <<EOF
{
  "board": "$RDK_BOARD",
  "stages": {
    "camera":  { "pass": $CAMERA_PASS, "v4l2_devices": [ $V4L2_JSON ] },
    "samples": { "pass": $SAMPLES_PASS, "pydev_demo": $PYDEV_PRESENT, "web_display_sample": $WEB_SAMPLE_JSON },
    "model":   { "pass": $MODEL_PASS, "model_dirs": [ $MODEL_DIRS_JSON ], "hrt_model_exec": $HRT_PRESENT },
    "bpu":     { "pass": $BPU_PASS, "readable": $BPU_READABLE },
    "display": { "pass": $DISPLAY_PASS, "hdmi_connected": $HDMI_CONNECTED },
    "web":     { "pass": $WEB_PASS, "nginx_present": $NGINX_PRESENT, "port80_listening": $PORT80 }
  },
  "cma_free_kb": $CMA_FREE_JSON,
  "first_broken_stage": $FIRST_BROKEN
}
EOF
