#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Probe X5 host, toolchain, documentation, and optional board facts."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, newline="\n"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temporary = Path(handle.name)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def command_info(name: str) -> dict[str, Any]:
    executable = shutil.which(name)
    if not executable:
        return {"available": False, "path": None, "version": None}
    version: str | None = None
    try:
        completed = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
        if combined:
            version = combined.splitlines()[0][:500]
    except (OSError, subprocess.TimeoutExpired):
        version = None
    return {"available": True, "path": str(Path(executable).resolve()), "version": version}


def package_info(name: str) -> dict[str, Any]:
    try:
        version = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return {"available": False, "version": None}
    return {"available": True, "version": version}


def doc_candidates(explicit: str | None) -> list[Path]:
    values: list[Path] = []
    for value in (
        explicit,
        os.environ.get("OE_DROBOTICS_DOC_ROOT"),
        os.environ.get("OE_X_SERIES_DOC_ROOT"),
    ):
        if value:
            values.append(Path(value).expanduser())
    values.append(Path.cwd() / "x5_doc-v1.2.8-py310-cn")
    script_path = Path(__file__).resolve()
    for parent in script_path.parents:
        values.append(parent / "x5_doc-v1.2.8-py310-cn")
        values.append(parent.parent / "x5_doc-v1.2.8-py310-cn")
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in values:
        resolved = candidate.resolve()
        key = str(resolved).lower()
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def resolve_docs(explicit: str | None) -> tuple[Path | None, list[str]]:
    checked: list[str] = []
    for candidate in doc_candidates(explicit):
        checked.append(str(candidate))
        if (candidate / "index.html").is_file() and (candidate / "_sources").is_dir():
            return candidate, checked
    return None, checked


def version_tuple(value: str | None) -> tuple[int, ...] | None:
    if not value:
        return None
    parts: list[int] = []
    for token in value.strip().split("."):
        digits = "".join(character for character in token if character.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts) if parts else None


def build_snapshot(args: argparse.Namespace) -> dict[str, Any]:
    docs_root, checked_docs = resolve_docs(args.docs_root)
    tools = {
        name: command_info(name)
        for name in (
            "hb_mapper",
            "hb_model_info",
            "hb_perf",
            "hrt_model_exec",
            "hrut_somstatus",
            "cmake",
            "aarch64-none-linux-gnu-gcc",
            "aarch64-none-linux-gnu-g++",
            "docker",
        )
    }
    tools["torch"] = package_info("torch")
    tools["horizon_plugin_pytorch"] = package_info("horizon-plugin-pytorch")

    board: dict[str, Any] | None = None
    if any((args.board_chip, args.board_version, args.board_architecture, args.board_reachable)):
        board = {
            "chip": args.board_chip,
            "version": args.board_version,
            "architecture": args.board_architecture,
            "reachable": bool(args.board_reachable),
        }

    missing: list[str] = []
    limitations: list[str] = []
    if docs_root is None:
        missing.append("X5 local manual")
    if board and board.get("chip") and str(board["chip"]).upper() != "X5":
        missing.append("board chip must be X5")
    if args.workflow == "ptq":
        for name in ("hb_mapper", "hb_model_info"):
            if not tools[name]["available"]:
                missing.append(name)
    if args.workflow == "qat":
        if not tools["torch"]["available"]:
            missing.append("torch")
        if not tools["horizon_plugin_pytorch"]["available"]:
            missing.append("horizon_plugin_pytorch")
    if args.workflow in {"runtime", "python-api"} and args.require_board:
        if not board or not board["reachable"]:
            missing.append("reachable X5 board")
    if args.workflow == "runtime" and board and board.get("architecture"):
        if str(board["architecture"]).lower() not in {"aarch64", "arm64"}:
            missing.append("X5 board architecture must be aarch64/arm64")
    if args.workflow == "runtime":
        optional = [name for name in ("cmake", "aarch64-none-linux-gnu-g++") if not tools[name]["available"]]
        if optional:
            limitations.append("host C++ build tools not found: " + ", ".join(optional))
    if args.workflow == "python-api":
        current = version_tuple(args.board_version)
        if current is None:
            missing.append("board /etc/version")
        elif current < (3, 5, 0):
            missing.append("board version >= 3.5.0")
    if args.workflow == "environment":
        optional = [name for name in ("hb_mapper", "hb_model_info", "hb_perf") if not tools[name]["available"]]
        if optional:
            limitations.append("toolchain commands not found: " + ", ".join(optional))

    status = "blocked" if missing else "degraded" if limitations else "ready"
    return {
        "schema_version": "1.0",
        "platform": "X5",
        "status": status,
        "captured_at": utc_now(),
        "workflow": args.workflow,
        "host": {
            "os": platform.platform(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
        },
        "toolchain": tools,
        "documentation": {
            "root": str(docs_root) if docs_root else None,
            "available": docs_root is not None,
            "hat_in_scope": False,
            "manual_baseline": "OE Mapper v1.2.8 / Python 3.10",
            "checked_candidates": checked_docs,
        },
        "board": board,
        "missing": missing,
        "limitations": limitations,
    }


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError:
        return
    schema_path = Path(__file__).resolve().parents[1] / "schemas/environment.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(snapshot, schema, format_checker=jsonschema.FormatChecker())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow",
        choices=("environment", "ptq", "qat", "runtime", "python-api", "diagnose"),
        default="environment",
    )
    parser.add_argument("--output", default="environment.json")
    parser.add_argument("--docs-root")
    parser.add_argument("--board-chip")
    parser.add_argument("--board-version")
    parser.add_argument("--board-architecture")
    parser.add_argument("--board-reachable", action="store_true")
    parser.add_argument("--require-board", action="store_true")
    args = parser.parse_args()

    snapshot = build_snapshot(args)
    validate_snapshot(snapshot)
    output = Path(args.output).expanduser().resolve()
    write_json(output, snapshot)
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
    return 0 if snapshot["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
