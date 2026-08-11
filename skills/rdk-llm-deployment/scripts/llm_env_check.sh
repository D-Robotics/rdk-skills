#!/bin/bash
# llm_env_check.sh — Read-only LLM environment probe for RDK boards.
#
# Reads board identity, memory, and installed LLM packages to verify whether
# the board can run an on-device LLM and which stack matches — so the agent
# doesn't recommend the wrong stack (e.g. hobot_llamacpp on S600).
#
# Output: JSON {"ok":true,"off_platform":false,"reason":"","fields":{"board_id":"...","mem_total":"...","llm_packages":[...],"recommended_stack":"..."}}
# Non-board: {"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}
#
# Principles: read-only; idempotent; non-board graceful degradation; bash-only.
# Usage: bash llm_env_check.sh

set -euo pipefail

# --- Check if we're on an RDK board ---
if [ ! -d /sys/class/socinfo ]; then
    echo '{"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}'
    exit 0
fi

# --- Board identity ---
board_id=""
if [ -r /sys/class/socinfo/board_id ]; then
    board_id=$(cat /sys/class/socinfo/board_id 2>/dev/null | tr -d '\0' | tr -d '\n')
fi

# --- Memory (total, from /proc/meminfo) ---
mem_total=""
if [ -r /proc/meminfo ]; then
    mem_total=$(awk '/^MemTotal:/{print $2" "$3}' /proc/meminfo 2>/dev/null | tr -d '\n')
fi
[ -z "$mem_total" ] && mem_total="unknown"

# --- Installed LLM packages (scan /opt/tros/*/lib/) ---
llm_packages=""
if [ -d /opt/tros ]; then
    # Find directories matching hobot_llm, hobot_llamacpp, oellm in any TROS lib
    found=$(find /opt/tros -maxdepth 3 -type d 2>/dev/null \
            | grep -E 'hobot_llm|hobot_llamacpp|oellm' \
            | sed 's/.*\///' \
            | sort -u \
            | tr '\n' ' ' \
            | sed 's/ /", "/g; s/^/"/; s/", "$//')
    if [ -n "$found" ]; then
        llm_packages="${found}"
    fi
fi
[ -z "$llm_packages" ] && llm_packages="\"none\""

# --- Recommended stack based on board_id ---
recommended_stack="none"
case "$board_id" in
    *X5*|*x5*)   recommended_stack="hobot_llamacpp" ;;
    *S100*|*s100*) recommended_stack="hobot_llamacpp or oellm_runtime" ;;
    *S600*|*s600*) recommended_stack="oellm_runtime (NOT hobot_llamacpp)" ;;
    *X3*|*x3*)   recommended_stack="hobot_llm (legacy, 4GB only)" ;;
    *Ultra*|*ultra*) recommended_stack="not supported (no first-party LLM path)" ;;
    *)           recommended_stack="unknown_board" ;;
esac

# --- Emit JSON (contract: ok/off_platform/reason/fields) ---
echo '{"ok":true,"off_platform":false,"reason":"","fields":{'
echo "  \"board_id\": \"${board_id}\","
echo "  \"mem_total\": \"${mem_total}\","
echo "  \"llm_packages\": [${llm_packages}],"
echo "  \"recommended_stack\": \"${recommended_stack}\""
echo '}}'
