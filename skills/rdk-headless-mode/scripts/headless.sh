#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-headless-mode: list / stop+disable / restore desktop and non-essential
# services. Never touches ssh or network management services.
#
# Usage:
#   headless.sh                 # dry-run (default)
#   headless.sh --apply         # stop + disable candidates (root)
#   headless.sh --apply --now-only  # stop only, keep enabled across reboots
#   headless.sh --revert        # enable + start candidates back (root)

set -euo pipefail

# Candidate list mirrors rdk-diagnostic candidate_services. lightdm is the
# desktop manager on RDK OS Desktop editions (per official docs).
CANDIDATES="lightdm cups bluetooth ModemManager avahi-daemon"

MODE=dry-run
NOW_ONLY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --apply)    MODE=apply; shift ;;
    --revert)   MODE=revert; shift ;;
    --now-only) NOW_ONLY=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

command -v systemctl >/dev/null 2>&1 || {
  echo "systemctl-not-found: this skill requires a systemd-based RDK OS." >&2
  exit 3
}

svc_state() {
  local svc="$1"
  local active enabled
  active="$(systemctl is-active "$svc" 2>/dev/null || true)"
  enabled="$(systemctl is-enabled "$svc" 2>/dev/null || true)"
  printf '%s %s' "${active:-unknown}" "${enabled:-unknown}"
}

emit_json() {
  local mode_label="$1"
  local out=""
  for svc in $CANDIDATES; do
    read -r active enabled <<< "$(svc_state "$svc")"
    local planned="none"
    case "$MODE" in
      dry-run|apply)
        if [ "$active" = "active" ]; then
          planned="stop"
          [ "$NOW_ONLY" -eq 0 ] && planned="stop+disable"
        fi ;;
      revert)
        planned="enable+start" ;;
    esac
    [ -n "$out" ] && out+=",
"
    out+="    \"$svc\": { \"active\": \"$active\", \"enabled\": \"$enabled\", \"planned\": \"$planned\" }"
  done
  printf '{\n  "mode": "%s",\n  "services": {\n%s\n  }\n}\n' "$mode_label" "$out"
}

if [ "$MODE" = "dry-run" ]; then
  emit_json "dry-run"
  exit 0
fi

# apply / revert need root
if [ "$(id -u)" -ne 0 ]; then
  echo "permission-denied: --$MODE requires root. Re-run with sudo." >&2
  exit 3
fi

for svc in $CANDIDATES; do
  read -r active enabled <<< "$(svc_state "$svc")"
  case "$MODE" in
    apply)
      if [ "$active" = "active" ]; then
        systemctl stop "$svc" || echo "warn: failed to stop $svc" >&2
      fi
      if [ "$NOW_ONLY" -eq 0 ] && [ "$enabled" = "enabled" ]; then
        systemctl disable "$svc" >/dev/null 2>&1 || echo "warn: failed to disable $svc" >&2
      fi ;;
    revert)
      systemctl enable "$svc" >/dev/null 2>&1 || true
      systemctl start "$svc" 2>/dev/null || true ;;
  esac
done

emit_json "$MODE"
