#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-model-benchmark: wrap the official `hrt_model_exec perf` tool and emit a
# structured JSON summary. Parameter semantics follow:
#   rdk_x_doc 07_Advanced_development/04_toolchain_development/intermediate/ptq_process.md
#
# Usage:
#   benchmark.sh --model <path.bin> [--core N] [--threads N] [--frames N] [--profile]
#   benchmark.sh --baseline [--core N] [--threads N] [--frames N]
#
# --baseline picks the first preinstalled model from the official model dirs
# (/app/model/basic, /opt/hobot/model/<soc>/basic — see pydev_demo docs) so the
# user can answer "is my board performing normally?" without providing a model.

set -euo pipefail

MODEL=""
BASELINE=0
CORE=0
THREADS=1
FRAMES=200
PROFILE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --model)    MODEL="${2:-}"; shift 2 ;;
    --baseline) BASELINE=1; shift ;;
    --core)     CORE="${2:-0}"; shift 2 ;;
    --threads)  THREADS="${2:-1}"; shift 2 ;;
    --frames)   FRAMES="${2:-200}"; shift 2 ;;
    --profile)  PROFILE=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

MODEL_SOURCE="user"
if [ "$BASELINE" -eq 1 ] && [ -z "$MODEL" ]; then
  for d in /app/model/basic /opt/hobot/model/*/basic; do
    [ -d "$d" ] || continue
    candidate="$(ls "$d"/*.bin "$d"/*.hbm 2>/dev/null | head -n1 || true)"
    if [ -n "$candidate" ]; then
      MODEL="$candidate"
      MODEL_SOURCE="baseline:$d"
      break
    fi
  done
  if [ -z "$MODEL" ]; then
    echo "baseline-model-not-found: no preinstalled model under /app/model/basic or /opt/hobot/model/*/basic." >&2
    echo "Provide --model <path> instead, or install models per the official pydev_demo docs." >&2
    exit 1
  fi
fi

if [ -z "$MODEL" ]; then
  echo "usage: benchmark.sh --model <path.bin> | --baseline [--core N] [--threads N] [--frames N] [--profile]" >&2
  exit 1
fi
if [ ! -f "$MODEL" ]; then
  echo "model-not-found: $MODEL (official docs recommend placing .bin models under /userdata)" >&2
  exit 1
fi
if ! command -v hrt_model_exec >/dev/null 2>&1; then
  echo "hrt_model_exec-not-found: check your RDK OS version or install it from the official toolchain release." >&2
  exit 3
fi

PROFILE_ARG=""
PROFILE_PATH=null
if [ "$PROFILE" -eq 1 ]; then
  PROFILE_DIR="$(pwd)/hrt_profile_$(date +%s)"
  mkdir -p "$PROFILE_DIR"
  PROFILE_ARG="--profile_path=$PROFILE_DIR"
  PROFILE_PATH="\"$PROFILE_DIR\""
fi

# Print model info first so the agent can quote input/output shapes.
hrt_model_exec model_info --model_file="$MODEL" || true

# shellcheck disable=SC2086
OUT="$(hrt_model_exec perf \
  --model_file "$MODEL" \
  --core_id="$CORE" \
  --frame_count="$FRAMES" \
  --perf_time=0 \
  --thread_num="$THREADS" \
  $PROFILE_ARG 2>&1)" || {
  echo "hrt_model_exec-perf-failed:" >&2
  printf '%s\n' "$OUT" >&2
  exit 4
}

printf '%s\n' "$OUT"

LATENCY="$(printf '%s\n' "$OUT" | awk -F': ' '/Average +latency +is/ {gsub(/ ms.*/, "", $2); print $2}' | tail -n1)"
FPS="$(printf '%s\n' "$OUT" | awk -F': ' '/Frame +rate +is/ {gsub(/ FPS.*/, "", $2); print $2}' | tail -n1)"

cat <<EOF
{
  "model_file": "$MODEL",
  "model_source": "$MODEL_SOURCE",
  "running_condition": { "core_id": $CORE, "thread_num": $THREADS, "frame_count": $FRAMES },
  "perf_result": {
    "average_latency_ms": ${LATENCY:-null},
    "fps": ${FPS:-null}
  },
  "profile_path": $PROFILE_PATH
}
EOF
