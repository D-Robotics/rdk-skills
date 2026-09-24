#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Apply a conservative X5 Python API release-range screen; MCP and board checks remain required."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXCLUSIVE_VERSION_FLOORS = {
    "x5": (3, 5, 0),
}
VERSION_PATTERN = re.compile(r"(?<!\d)(\d+(?:\.\d+){1,3})(?!\d)")
LABELLED_VERSION_PATTERN = re.compile(
    r"(?im)(?:system|software|image|release|rdk|os)?\s*version\s*[:=]?\s*(\d+(?:\.\d+){1,3})"
)


def parse_version(value: str) -> tuple[int, ...]:
    return tuple(int(segment) for segment in value.split("."))


def format_version(version: tuple[int, ...]) -> str:
    return ".".join(str(segment) for segment in version)


def normalize_version(version: tuple[int, ...], width: int = 4) -> tuple[int, ...]:
    return version + (0,) * max(0, width - len(version))


def detect_version(content: str) -> tuple[int, ...] | None:
    labelled = list(dict.fromkeys(LABELLED_VERSION_PATTERN.findall(content)))
    if len(labelled) == 1:
        return parse_version(labelled[0])
    if len(labelled) > 1:
        return None

    candidates = list(dict.fromkeys(VERSION_PATTERN.findall(content)))
    if len(candidates) == 1:
        return parse_version(candidates[0])
    return None


def read_version_content(args: argparse.Namespace) -> tuple[str, str]:
    if args.version is not None:
        return args.version, "--version"

    version_file = args.version_file
    try:
        return version_file.read_text(encoding="utf-8", errors="replace"), str(version_file)
    except OSError as error:
        raise RuntimeError(f"Cannot read board version file {version_file}: {error}") from error


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Screen the X5 hbm_runtime documented version range; confirm MCP and actual board import separately."
    )
    parser.add_argument("--platform", choices=sorted(EXCLUSIVE_VERSION_FLOORS), required=True)
    parser.add_argument(
        "--version-file",
        type=Path,
        default=Path("/etc/version"),
        help="Board version file; defaults to /etc/version when run on the board.",
    )
    parser.add_argument(
        "--version",
        help="Explicit version string for CI/replay; do not use this to bypass a board preflight.",
    )
    args = parser.parse_args()

    try:
        content, source = read_version_content(args)
    except RuntimeError as error:
        print(f"BPU_PYTHON_API_VERSION_ERROR: {error}", file=sys.stderr)
        return 2

    detected = detect_version(content)
    version_floor = EXCLUSIVE_VERSION_FLOORS[args.platform]
    if detected is None:
        print(
            "BPU_PYTHON_API_VERSION_ERROR: cannot unambiguously parse a system version "
            f"from {source}. Run 'cat /etc/version' and provide the board version explicitly.",
            file=sys.stderr,
        )
        return 3

    if normalize_version(detected) < normalize_version(version_floor):
        print(
            "BPU_PYTHON_API_VERSION_UNSUPPORTED: "
            f"platform={args.platform} detected={format_version(detected)} "
            f"detected version is below the documented post-{format_version(version_floor)} range; "
            f"verify the latest official MCP documentation source={source}",
            file=sys.stderr,
        )
        return 1
    if normalize_version(detected) == normalize_version(version_floor):
        print(
            "BPU_PYTHON_API_VERSION_NEEDS_VERIFICATION: "
            f"platform={args.platform} detected={format_version(detected)}; official wording does not establish "
            "whether this exact release is supported. Recheck via MCP and verify an actual board import.",
            file=sys.stderr,
        )
        return 4

    print(
        "BPU_PYTHON_API_VERSION_RANGE_CANDIDATE: "
        f"platform={args.platform} detected={format_version(detected)} "
        f"after={format_version(version_floor)}. This is a static range screen only; confirm current MCP wording, "
        f"package source, and actual board import before use. source={source}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
