#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Parse one or more X5 hrut_somstatus snapshots into structured JSON."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any


MARKER = re.compile(r"^\s*=+\s*\d+\s*=+\s*$")
TEMP = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(-?[0-9]+(?:\.[0-9]+)?)\s*\(C\)")
ROW = re.compile(
    r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:\s*"
    r"([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)"
    r"(?:\s+([0-9]+(?:\.[0-9]+)?))?\s*$"
)


def new_snapshot() -> dict[str, Any]:
    return {"temperature_c": {}, "cpu_mhz": {}, "bpu_mhz": {}, "ddr_mhz": {}, "gpu_mhz": {}}


def parse_text(text: str) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    current = new_snapshot()
    section: str | None = None

    def finish() -> None:
        nonlocal current
        if any(current[key] for key in current):
            snapshots.append(current)
        current = new_snapshot()

    for line in text.splitlines():
        stripped = line.strip().lower()
        if MARKER.match(line):
            finish()
            section = None
            continue
        if "temperature" in stripped and "-->" in stripped:
            section = "temperature_c"
            continue
        if "cpu frequency" in stripped:
            section = "cpu_mhz"
            continue
        if "bpu status" in stripped:
            section = "bpu_mhz"
            continue
        if "ddr frequency" in stripped:
            section = "ddr_mhz"
            continue
        if "gpu" in stripped and "frequency" in stripped:
            section = "gpu_mhz"
            continue

        temperature = TEMP.match(line)
        if temperature and section == "temperature_c":
            current[section][temperature.group(1).lower()] = float(temperature.group(2))
            continue
        row = ROW.match(line)
        if row and section in {"cpu_mhz", "bpu_mhz", "ddr_mhz", "gpu_mhz"}:
            item: dict[str, float] = {
                "min": float(row.group(2)),
                "current": float(row.group(3)),
                "max": float(row.group(4)),
            }
            if row.group(5) is not None:
                item["ratio_percent"] = float(row.group(5))
            current[section][row.group(1).lower()] = item
    finish()
    return snapshots


def summarize(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    temperatures: dict[str, list[float]] = {}
    bpu_ratios: dict[str, list[float]] = {}
    for snapshot in snapshots:
        for name, value in snapshot["temperature_c"].items():
            temperatures.setdefault(name, []).append(value)
        for name, value in snapshot["bpu_mhz"].items():
            if "ratio_percent" in value:
                bpu_ratios.setdefault(name, []).append(value["ratio_percent"])
    return {
        "temperature_c": {
            name: {"average": statistics.fmean(values), "peak": max(values)}
            for name, values in sorted(temperatures.items())
        },
        "bpu_ratio_percent": {
            name: {"average": statistics.fmean(values), "peak": max(values)}
            for name, values in sorted(bpu_ratios.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="hrut_somstatus output file, or - for stdin")
    parser.add_argument("--output")
    args = parser.parse_args()

    text = sys.stdin.read() if args.input == "-" else Path(args.input).expanduser().read_text(encoding="utf-8", errors="replace")
    snapshots = parse_text(text)
    payload = {
        "schema_version": "1.0",
        "platform": "X5",
        "tool": "hrut_somstatus",
        "snapshot_count": len(snapshots),
        "snapshots": snapshots,
        "summary": summarize(snapshots),
    }
    if not snapshots:
        print("ERROR: no hrut_somstatus metrics found", file=sys.stderr)
        return 2
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
