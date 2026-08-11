#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Canonical D-Robotics RDK platform detector for rdk-device-skills.
#
# Exports (when sourced) or prints (when executed):
#   RDK_BOARD          rdk-x3 | rdk-x3-module | rdk-x5 | rdk-x5-module | rdk-ultra | rdk-s100 | rdk-s600 | unknown
#   RDK_SOC            sunrise-x3 | sunrise-5 | journey-5 | s100 | s600 | unknown
#   RDK_BPU_ARCH       bernoulli | bayes-e | bayes | nash-e | nash-p | unknown
#   RDK_MEM_GB         integer, rounded total DRAM in GiB
#   RDK_OS_VERSION     contents of /etc/version (RDK OS release), or "unknown"
#   RDK_PRODUCT_MODEL  raw /proc/device-tree/model string, lowercased
#
# Exit codes (when executed): 0 = RDK detected, 2 = not an RDK host.
# Other skills should source this file instead of duplicating detection logic.

_rdk_detect() {
  local model=""
  if [ -r /proc/device-tree/model ]; then
    model="$(tr -d '\0' < /proc/device-tree/model 2>/dev/null | tr '[:upper:]' '[:lower:]')"
  fi
  RDK_PRODUCT_MODEL="${model:-unknown}"

  # total memory in GiB, rounded to the nearest common size
  local mem_kb=0
  mem_kb="$(awk '/^MemTotal:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
  RDK_MEM_GB=$(( (mem_kb + 524288) / 1048576 ))

  RDK_OS_VERSION="unknown"
  if [ -r /etc/version ]; then
    RDK_OS_VERSION="$(head -n1 /etc/version | tr -d '[:space:]')"
  fi

  RDK_BOARD="unknown"; RDK_SOC="unknown"; RDK_BPU_ARCH="unknown"

  case "$model" in
    *rdk*x5*module*|*x5*md*)
      RDK_BOARD="rdk-x5-module"; RDK_SOC="sunrise-5";  RDK_BPU_ARCH="bayes-e" ;;
    *rdk*x5*|*sunrise*5*)
      RDK_BOARD="rdk-x5";        RDK_SOC="sunrise-5";  RDK_BPU_ARCH="bayes-e" ;;
    *x3*module*|*som*x3*)
      RDK_BOARD="rdk-x3-module"; RDK_SOC="sunrise-x3"; RDK_BPU_ARCH="bernoulli" ;;
    *x3*pi*|*rdk*x3*|*hobot*x3*)
      RDK_BOARD="rdk-x3";        RDK_SOC="sunrise-x3"; RDK_BPU_ARCH="bernoulli" ;;
    *rdk*ultra*|*journey*5*|*j5*)
      RDK_BOARD="rdk-ultra";     RDK_SOC="journey-5";  RDK_BPU_ARCH="bayes" ;;
    *rdk*s600*|*s600*)
      RDK_BOARD="rdk-s600";      RDK_SOC="s600";       RDK_BPU_ARCH="nash-p" ;;
    *rdk*s100*|*s100*)
      RDK_BOARD="rdk-s100";      RDK_SOC="s100";       RDK_BPU_ARCH="nash-e" ;;
  esac

  # Fallback heuristic: RDK OS markers without a recognisable model string.
  if [ "$RDK_BOARD" = "unknown" ]; then
    if command -v hrut_somstatus >/dev/null 2>&1 || [ -d /sys/devices/system/bpu ]; then
      RDK_BOARD="rdk-unknown"
    fi
  fi

  export RDK_BOARD RDK_SOC RDK_BPU_ARCH RDK_MEM_GB RDK_OS_VERSION RDK_PRODUCT_MODEL

  case "$RDK_BOARD" in
    unknown) return 2 ;;
    *)       return 0 ;;
  esac
}

_rdk_detect
_rdk_status=$?

# When executed (not sourced): print fields and exit with detection status.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ "$_rdk_status" -ne 0 ]; then
    echo "not-an-rdk-host: /proc/device-tree/model, hrut_somstatus and BPU sysfs are all missing." >&2
    echo "Run this skill on a D-Robotics RDK device, or relaunch with a host-visible sandbox profile." >&2
    exit 2
  fi
  printf 'RDK_BOARD=%s\n'         "$RDK_BOARD"
  printf 'RDK_SOC=%s\n'           "$RDK_SOC"
  printf 'RDK_BPU_ARCH=%s\n'      "$RDK_BPU_ARCH"
  printf 'RDK_MEM_GB=%s\n'        "$RDK_MEM_GB"
  printf 'RDK_OS_VERSION=%s\n'    "$RDK_OS_VERSION"
  printf 'RDK_PRODUCT_MODEL=%s\n' "$RDK_PRODUCT_MODEL"
fi
