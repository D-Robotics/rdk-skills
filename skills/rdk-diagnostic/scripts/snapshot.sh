#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-diagnostic: all-in-one read-only JSON health snapshot for RDK devices.
#
# Usage:
#   snapshot.sh [--human] [--top-procs N] [--record]
#
# --record appends a compact one-line JSON sample (timestamp, thermal, bpu,
# memory) to ${RDK_SNAPSHOT_LOG:-$HOME/.rdk-skill/snapshots.jsonl} so trend
# questions ("is it getting hotter?") can be answered from measured history.
#
# Output contract is documented in ../SKILL.md. Fields the host cannot provide
# are reported as null / false / empty — never fabricated.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=detect_rdk.sh
source "$SCRIPT_DIR/detect_rdk.sh" || true
if [ "${RDK_BOARD:-unknown}" = "unknown" ]; then
  echo "not-an-rdk-host: run this script on a D-Robotics RDK device." >&2
  exit 2
fi

HUMAN=0
TOP_PROCS=5
RECORD=0
while [ $# -gt 0 ]; do
  case "$1" in
    --human)     HUMAN=1; shift ;;
    --top-procs) TOP_PROCS="${2:-5}"; shift 2 ;;
    --record)    RECORD=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

json_or_null() { [ -n "${1:-}" ] && printf '%s' "$1" || printf 'null'; }

# ── memory ───────────────────────────────────────────────────────────────────
mem_field() { awk -v k="$1" '$1 == k":" {print $2}' /proc/meminfo 2>/dev/null; }
MEM_TOTAL="$(mem_field MemTotal)"
MEM_AVAIL="$(mem_field MemAvailable)"
MEM_CACHED="$(mem_field Cached)"
SWAP_TOTAL="$(mem_field SwapTotal)"
SWAP_FREE="$(mem_field SwapFree)"
CMA_TOTAL="$(mem_field CmaTotal)"
CMA_FREE="$(mem_field CmaFree)"

# ── BPU utilisation (sysfs, falls back to unreadable) ────────────────────────
BPU_READABLE=false
BPU_CORES_JSON=""
if [ -d /sys/devices/system/bpu ]; then
  idx=0
  for node in /sys/devices/system/bpu/bpu*/ratio; do
    [ -r "$node" ] || continue
    ratio="$(tr -dc '0-9' < "$node" 2>/dev/null || true)"
    [ -n "$ratio" ] || continue
    BPU_READABLE=true
    [ -n "$BPU_CORES_JSON" ] && BPU_CORES_JSON+=", "
    BPU_CORES_JSON+="{ \"core\": $idx, \"ratio_pct\": $ratio }"
    idx=$((idx + 1))
  done
fi

# ── thermal zones ────────────────────────────────────────────────────────────
THERMAL_JSON=""
for zone in /sys/class/thermal/thermal_zone*; do
  [ -r "$zone/temp" ] || continue
  ztype="$(cat "$zone/type" 2>/dev/null | tr -d '[:space:]')"
  raw="$(cat "$zone/temp" 2>/dev/null || true)"
  [ -n "$raw" ] || continue
  temp_c="$(awk -v t="$raw" 'BEGIN { printf "%.1f", t / 1000 }')"
  [ -n "$THERMAL_JSON" ] && THERMAL_JSON+=", "
  THERMAL_JSON+="\"${ztype:-zone}\": $temp_c"
done

# ── disk usage ───────────────────────────────────────────────────────────────
DISK_JSON="$(df -P -x tmpfs -x devtmpfs -x overlay 2>/dev/null | awk 'NR > 1 {
  gsub(/%/, "", $5)
  printf "%s{ \"mount\": \"%s\", \"used_pct\": %s }", (n++ ? ", " : ""), $6, $5
}')"

# ── top processes by RSS ─────────────────────────────────────────────────────
TOP_JSON="$(ps -eo pid=,rss=,comm= --sort=-rss 2>/dev/null | head -n "$TOP_PROCS" | awk '{
  printf "%s{ \"pid\": %s, \"cmd\": \"%s\", \"rss_kb\": %s }", (n++ ? ", " : ""), $1, $3, $2
}')"

# ── candidate services (safe-to-disable candidates, observed state only) ─────
SERVICES_JSON=""
for svc in lightdm gdm3 cups bluetooth ModemManager avahi-daemon; do
  if command -v systemctl >/dev/null 2>&1; then
    active="$(systemctl is-active "$svc" 2>/dev/null || true)"
    enabled="$(systemctl is-enabled "$svc" 2>/dev/null || true)"
    [ "$active" = "unknown" ] || [ -z "$active" ] && continue
    [ -n "$SERVICES_JSON" ] && SERVICES_JSON+=", "
    SERVICES_JSON+="\"$svc\": { \"active\": \"$active\", \"enabled\": \"${enabled:-unknown}\" }"
  fi
done

# ── kernel log error signal (read-only; degrades without privilege) ─────────
KERN_READABLE=false
KERN_ERR_COUNT=null
if command -v dmesg >/dev/null 2>&1; then
  if dmesg >/dev/null 2>&1; then
    KERN_READABLE=true
    KERN_ERR_COUNT="$(dmesg --level=err,crit,alert,emerg 2>/dev/null | grep -c . || true)"
    KERN_ERR_COUNT="${KERN_ERR_COUNT:-0}"
  fi
fi

# ── emit ─────────────────────────────────────────────────────────────────────
if [ "$RECORD" -eq 1 ]; then
  LOG_FILE="${RDK_SNAPSHOT_LOG:-$HOME/.rdk-skill/snapshots.jsonl}"
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '{"ts":%s,"board":"%s","mem_available_kb":%s,"cma_free_kb":%s,"thermal_c":{%s},"bpu_cores":[%s],"kernel_err_count":%s}\n' \
    "$(date +%s)" "$RDK_BOARD" "$(json_or_null "$MEM_AVAIL")" "$(json_or_null "$CMA_FREE")" \
    "$THERMAL_JSON" "$BPU_CORES_JSON" "$KERN_ERR_COUNT" >> "$LOG_FILE"
  echo "recorded: $LOG_FILE ($(grep -c . "$LOG_FILE" 2>/dev/null || echo 1) samples)" >&2
fi

if [ "$HUMAN" -eq 1 ]; then
  echo "board=$RDK_BOARD soc=$RDK_SOC bpu=$RDK_BPU_ARCH mem=${RDK_MEM_GB}GB os=$RDK_OS_VERSION"
  echo "mem_available_kb=${MEM_AVAIL:-n/a} cma_free_kb=${CMA_FREE:-n/a} bpu_readable=$BPU_READABLE"
  exit 0
fi

cat <<EOF
{
  "board": "$RDK_BOARD",
  "soc": "$RDK_SOC",
  "bpu_arch": "$RDK_BPU_ARCH",
  "mem_total_gb": $RDK_MEM_GB,
  "rdk_os_version": "$RDK_OS_VERSION",
  "product_model": "$RDK_PRODUCT_MODEL",
  "memory_kb": {
    "total": $(json_or_null "$MEM_TOTAL"),
    "available": $(json_or_null "$MEM_AVAIL"),
    "swap_total": $(json_or_null "$SWAP_TOTAL"),
    "swap_free": $(json_or_null "$SWAP_FREE"),
    "cached": $(json_or_null "$MEM_CACHED")
  },
  "cma": { "total_kb": $(json_or_null "$CMA_TOTAL"), "free_kb": $(json_or_null "$CMA_FREE") },
  "bpu": { "readable": $BPU_READABLE, "cores": [ $BPU_CORES_JSON ] },
  "thermal_c": { $THERMAL_JSON },
  "kernel_log": { "readable": $KERN_READABLE, "err_count": $KERN_ERR_COUNT },
  "disk": [ $DISK_JSON ],
  "top_processes": [ $TOP_JSON ],
  "candidate_services": { $SERVICES_JSON }
}
EOF
