#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-network-remote: layered on-board network self-check for RDK devices.
# Layers: interfaces/link -> ip -> default route -> gateway ping -> dns ->
# ssh service. Official defaults (static IP, baud rates) are documented in
# ../references/remote-access.md, sourced from rdk_x_doc remote_login.md.
#
# Usage:
#   net_diag.sh [--json|--human] [--no-ping]
#
# Read-only (ping is a single 2s-timeout probe). Fields the host cannot
# provide are reported as null — never fabricated.

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
DO_PING=1
while [ $# -gt 0 ]; do
  case "$1" in
    --json)    MODE=json; shift ;;
    --human)   MODE=human; shift ;;
    --no-ping) DO_PING=0; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── interfaces / link / ip ───────────────────────────────────────────────────
IFACES_JSON=""
ANY_CARRIER=false
ANY_ADDR=false
for d in /sys/class/net/*; do
  [ -d "$d" ] || continue
  ifname="$(basename "$d")"
  [ "$ifname" = "lo" ] && continue
  state="$(cat "$d/operstate" 2>/dev/null || echo unknown)"
  carrier=false
  if [ "$(cat "$d/carrier" 2>/dev/null || echo 0)" = "1" ]; then
    carrier=true
    ANY_CARRIER=true
  fi
  addrs="$(ip -o addr show dev "$ifname" 2>/dev/null | awk '$3 == "inet" {
    printf "%s\"%s\"", (n++ ? ", " : ""), $4
  }')"
  if [ -n "$addrs" ]; then ANY_ADDR=true; fi
  [ -n "$IFACES_JSON" ] && IFACES_JSON+=", "
  IFACES_JSON+="{ \"name\": \"$ifname\", \"state\": \"$state\", \"carrier\": $carrier, \"addrs\": [ $addrs ] }"
done

# ── default route ────────────────────────────────────────────────────────────
ROUTE_LINE="$(ip route show default 2>/dev/null | head -n1 || true)"
GW=""
GW_DEV=""
if [ -n "$ROUTE_LINE" ]; then
  GW="$(printf '%s' "$ROUTE_LINE" | awk '{for (i=1;i<NF;i++) if ($i=="via") print $(i+1)}')"
  GW_DEV="$(printf '%s' "$ROUTE_LINE" | awk '{for (i=1;i<NF;i++) if ($i=="dev") print $(i+1)}')"
fi
ROUTE_JSON=null
if [ -n "$ROUTE_LINE" ]; then
  ROUTE_JSON="{ \"via\": \"${GW:-null}\", \"dev\": \"${GW_DEV:-null}\" }"
fi

# ── gateway ping (single packet, 2s timeout) ─────────────────────────────────
GW_PING=null
if [ "$DO_PING" -eq 1 ] && [ -n "$GW" ] && command -v ping >/dev/null 2>&1; then
  if ping -c 1 -W 2 "$GW" >/dev/null 2>&1; then GW_PING=true; else GW_PING=false; fi
fi

# ── dns ──────────────────────────────────────────────────────────────────────
NS_JSON="$(awk '$1 == "nameserver" {
  printf "%s\"%s\"", (n++ ? ", " : ""), $2
}' /etc/resolv.conf 2>/dev/null || true)"
RESOLVE_OK=null
if [ "$DO_PING" -eq 1 ] && command -v getent >/dev/null 2>&1; then
  if timeout 3 getent hosts archive.d-robotics.cc >/dev/null 2>&1; then
    RESOLVE_OK=true
  else
    RESOLVE_OK=false
  fi
fi

# ── ssh service ──────────────────────────────────────────────────────────────
SSH_PRESENT=false
SSH_ACTIVE=null
if command -v sshd >/dev/null 2>&1 || [ -f /usr/sbin/sshd ]; then SSH_PRESENT=true; fi
if command -v systemctl >/dev/null 2>&1; then
  st="$(systemctl is-active ssh 2>/dev/null || systemctl is-active sshd 2>/dev/null || true)"
  [ -n "$st" ] && SSH_ACTIVE="\"$st\""
fi

# ── first failed layer ───────────────────────────────────────────────────────
FIRST_FAILED=null
if   [ "$ANY_CARRIER" != true ];  then FIRST_FAILED='"link"'
elif [ "$ANY_ADDR" != true ];     then FIRST_FAILED='"ip"'
elif [ "$ROUTE_JSON" = null ];    then FIRST_FAILED='"route"'
elif [ "$GW_PING" = false ];      then FIRST_FAILED='"gateway"'
elif [ "$RESOLVE_OK" = false ];   then FIRST_FAILED='"dns"'
elif [ "$SSH_ACTIVE" != null ] && [ "$SSH_ACTIVE" != '"active"' ]; then FIRST_FAILED='"ssh_service"'
fi

if [ "$MODE" = "human" ]; then
  echo "board=$RDK_BOARD carrier=$ANY_CARRIER addr=$ANY_ADDR gw=${GW:-none} gw_ping=$GW_PING dns=$RESOLVE_OK ssh=$SSH_ACTIVE"
  echo "first_failed_layer=$FIRST_FAILED"
  exit 0
fi

cat <<EOF
{
  "board": "$RDK_BOARD",
  "interfaces": [ $IFACES_JSON ],
  "default_route": $ROUTE_JSON,
  "gateway_ping": $GW_PING,
  "dns": { "nameservers": [ $NS_JSON ], "resolve_ok": $RESOLVE_OK },
  "ssh_service": { "present": $SSH_PRESENT, "active": $SSH_ACTIVE },
  "first_failed_layer": $FIRST_FAILED
}
EOF
