#!/bin/bash
# hw_probe.sh — Read-only hardware interface and thermal probe for RDK boards.
#
# Scans /dev and /sys for available hardware interfaces (I2C, SPI, UART, CAN,
# GPIO chips) and reads thermal data — so the agent can verify "which buses
# are actually present / what's the temperature" without guessing from the
# board spec table alone.
#
# Output: JSON {"ok":true,"off_platform":false,"reason":"","fields":{"board_id":"...","i2c_buses":[...],"spi_devices":[...],"uart_devices":[...],"can_interfaces":[...],"gpio_chips":[...],"soc_temp":"...","board_temp":"..."}}
# Non-board: {"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}
# Board but hrut_somstatus missing: reason set to "hrut_somstatus not found" (temp fields still probed via /sys)
#
# Principles: read-only (no i2cset, no gpioset); idempotent; bash-only.
# Complements board_probe.sh (identity) and bpu_status.sh (BPU/memory).
# Usage: bash hw_probe.sh

set -euo pipefail

# --- Check if we're on an RDK board ---
if [ ! -d /sys/class/socinfo ]; then
    echo '{"ok":false,"off_platform":true,"reason":"not_on_rdk_board: /sys/class/socinfo not found","fields":null}'
    exit 0
fi

# --- Helper: read a sysfs file safely ---
read_sysfs() {
    local path="$1"
    if [ -r "$path" ]; then
        cat "$path" 2>/dev/null | tr -d '\0' | tr -d '\n'
    else
        echo ""
    fi
}

# --- Board identity (for context, not the primary purpose) ---
board_id=$(read_sysfs /sys/class/socinfo/board_id)

# --- I2C buses (/dev/i2c-*) ---
i2c_buses=""
if ls /dev/i2c-* >/dev/null 2>&1; then
    i2c_buses=$(ls -1 /dev/i2c-* 2>/dev/null | sed 's|/dev/||' | sort | tr '\n' ' ' | sed 's/ /", "/g; s/^/"/; s/", "$//')
fi
[ -z "$i2c_buses" ] && i2c_buses="\"none\""

# --- SPI devices (/dev/spidev*) ---
spi_devices=""
if ls /dev/spidev* >/dev/null 2>&1; then
    spi_devices=$(ls -1 /dev/spidev* 2>/dev/null | sed 's|/dev/||' | sort | tr '\n' ' ' | sed 's/ /", "/g; s/^/"/; s/", "$//')
fi
[ -z "$spi_devices" ] && spi_devices="\"none\""

# --- UART devices (/dev/ttyS*, /dev/ttyTHS*) ---
uart_devices=""
if ls /dev/ttyS* /dev/ttyTHS* >/dev/null 2>&1; then
    uart_devices=$(ls -1 /dev/ttyS* /dev/ttyTHS* 2>/dev/null | sed 's|/dev/||' | sort -u | tr '\n' ' ' | sed 's/ /", "/g; s/^/"/; s/", "$//')
fi
[ -z "$uart_devices" ] && uart_devices="\"none\""

# --- CAN interfaces (/sys/class/net/can*) ---
can_interfaces=""
if [ -d /sys/class/net ]; then
    found_can=$(find /sys/class/net -maxdepth 1 -name 'can*' -printf '%f\n' 2>/dev/null | sort | tr '\n' ' ' | sed 's/ /", "/g; s/^/"/; s/", "$//')
    if [ -n "$found_can" ]; then
        can_interfaces="${found_can}"
    fi
fi
[ -z "$can_interfaces" ] && can_interfaces="\"none\""

# --- GPIO chips (/dev/gpiochip*) ---
gpio_chips=""
if ls /dev/gpiochip* >/dev/null 2>&1; then
    gpio_chips=$(ls -1 /dev/gpiochip* 2>/dev/null | sed 's|/dev/||' | sort | tr '\n' ' ' | sed 's/ /", "/g; s/^/"/; s/", "$//')
fi
[ -z "$gpio_chips" ] && gpio_chips="\"none\""

# --- Temperature (try /sys/class/hwmon first, then hrut_somstatus) ---
soc_temp=""
board_temp=""
temp_note=""

# Try sysfs thermal zones
if [ -d /sys/class/thermal ]; then
    for tz in /sys/class/thermal/thermal_zone*/temp; do
        if [ -r "$tz" ]; then
            temp_raw=$(cat "$tz" 2>/dev/null | tr -d '\n')
            if [ -n "$temp_raw" ]; then
                # Convert millidegrees to degrees
                temp_c=$(awk "BEGIN{printf \"%.1f\", ${temp_raw}/1000}" 2>/dev/null || echo "${temp_raw}")
                if [ -z "$soc_temp" ]; then
                    soc_temp="${temp_c}"
                else
                    board_temp="${temp_c}"
                fi
            fi
        fi
    done
fi

# Try hrut_somstatus for additional thermal/power info
if command -v hrut_somstatus >/dev/null 2>&1; then
    som_status=$(timeout 3 hrut_somstatus 2>/dev/null | tr -d '\n' | sed 's/"/\\"/g')
    # Don't override sysfs temps; som_status is supplementary
    [ -z "$soc_temp" ] && soc_temp="see hrut_somstatus output"
else
    temp_note="hrut_somstatus not found"
fi

[ -z "$soc_temp" ] && soc_temp="unknown"

# --- Emit JSON (contract: ok/off_platform/reason/fields) ---
echo '{"ok":true,"off_platform":false,"reason":"'"${temp_note}"'","fields":{'
echo "  \"board_id\": \"${board_id}\","
echo "  \"i2c_buses\": [${i2c_buses}],"
echo "  \"spi_devices\": [${spi_devices}],"
echo "  \"uart_devices\": [${uart_devices}],"
echo "  \"can_interfaces\": [${can_interfaces}],"
echo "  \"gpio_chips\": [${gpio_chips}],"
echo "  \"soc_temp\": \"${soc_temp}\","
echo "  \"board_temp\": \"${board_temp}\""
echo '}}'
