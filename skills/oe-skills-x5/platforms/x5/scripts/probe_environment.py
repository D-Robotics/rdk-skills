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
import sys
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


def torch_cuda_info() -> dict[str, Any]:
    """Report whether the current Python environment can see a CUDA device."""
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import torch; print(torch.version.cuda or ''); "
                "print('true' if torch.cuda.is_available() else 'false')",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {"available": False, "path": None, "version": None}
    lines = (completed.stdout or "").strip().splitlines()
    if completed.returncode != 0 or not lines or lines[-1].strip().lower() != "true":
        return {"available": False, "path": None, "version": None}
    cuda_version = lines[-2].strip() if len(lines) > 1 else ""
    return {
        "available": True,
        "path": None,
        "version": cuda_version or None,
    }


def probe_docker_toolchain(image: str | None, workflow: str) -> dict[str, Any]:
    """Verify a configured local X5 image without pulling it or mounting host paths."""
    result: dict[str, Any] = {
        "image": image,
        "image_available": False,
        "verified": False,
        "tools": [],
        "error": None,
    }
    if not image:
        result["error"] = "no Docker image configured"
        return result

    docker = shutil.which("docker")
    if not docker:
        result["error"] = "docker command is not available"
        return result

    try:
        inspected = subprocess.run(
            [docker, "image", "inspect", "--format", "{{.Id}}", image],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        result["error"] = f"docker image inspect failed: {error}"
        return result
    if inspected.returncode != 0 or not inspected.stdout.strip():
        result["error"] = "configured Docker image is not present locally; probe does not pull images"
        return result
    result["image_available"] = True

    if workflow == "qat":
        probe_command = (
            "python3 -c 'import torch, horizon_plugin_pytorch; "
            "from horizon_plugin_pytorch import March; assert hasattr(March, \"BAYES_E\"); "
            "assert torch.cuda.is_available(), \"CUDA is not visible to the container\"; "
            "print(\"CUDA_VISIBLE=True\")'"
        )
        expected_tools = ["torch", "horizon_plugin_pytorch", "cuda"]
    else:
        probe_command = (
            "set -e; command -v hb_mapper; command -v hb_model_info; "
            "hb_mapper --help"
        )
        expected_tools = ["hb_mapper", "hb_model_info"]

    try:
        completed = subprocess.run(
            [
                docker,
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp:rw,exec,nosuid,size=64m",
                *(["--gpus", "all"] if workflow == "qat" else []),
                "--entrypoint",
                "/bin/bash",
                image,
                "-lc",
                probe_command,
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        result["error"] = f"read-only Docker tool probe failed: {error}"
        return result

    output = "\n".join((completed.stdout or "", completed.stderr or ""))
    if workflow != "qat" and not all(token in output for token in ("checker", "makertbin")):
        result["error"] = "hb_mapper help did not confirm checker and makertbin"
        return result
    if completed.returncode != 0:
        details = (completed.stderr or "").strip().splitlines()
        reason = details[-1][:300] if details else f"exit status {completed.returncode}"
        result["error"] = f"container probe exited with status {completed.returncode}: {reason}"
        return result

    result["verified"] = True
    result["tools"] = expected_tools
    return result


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
    tools["cuda"] = torch_cuda_info() if tools["torch"]["available"] else {
        "available": False,
        "path": None,
        "version": None,
    }
    docker_image = args.docker_image or os.environ.get("OE_DROBOTICS_DOCKER_IMAGE")
    requested_execution = (
        getattr(args, "execution_mode", None)
        or os.environ.get("OE_DROBOTICS_EXECUTION_MODE")
        or "docker"
    )
    if requested_execution not in {"docker", "host"}:
        raise ValueError("execution mode must be 'docker' or 'host'")
    if requested_execution == "docker":
        docker_probe = probe_docker_toolchain(docker_image, args.workflow)
    else:
        docker_probe = {
            "image": docker_image,
            "image_available": False,
            "verified": False,
            "tools": [],
            "error": "host execution mode explicitly selected",
        }

    host_ptq_available = tools["hb_mapper"]["available"] and tools["hb_model_info"]["available"]
    host_qat_available = (
        tools["torch"]["available"]
        and tools["horizon_plugin_pytorch"]["available"]
        and tools["cuda"]["available"]
    )
    execution_mode: str | None = None
    if args.workflow in {"ptq", "qat", "environment"}:
        if requested_execution == "docker" and docker_probe["verified"]:
            execution_mode = "docker"
        elif requested_execution == "host" and (
            host_qat_available if args.workflow == "qat" else host_ptq_available
        ):
            execution_mode = "host"
    elif args.workflow in {"runtime", "python-api", "diagnose"}:
        execution_mode = "host"

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
        if requested_execution == "docker" and not docker_probe["verified"]:
            missing.append(
                "verified X5 PTQ Docker image" if docker_image else "configured X5 PTQ Docker image"
            )
        elif requested_execution == "host" and not host_ptq_available:
            missing.append("host hb_mapper and hb_model_info")
    if args.workflow == "qat":
        if requested_execution == "docker" and not docker_probe["verified"]:
            missing.append(
                "verified X5 Plugin QAT Docker image"
                if docker_image
                else "configured X5 Plugin QAT Docker image"
            )
        elif requested_execution == "host" and not host_qat_available:
            missing.append("host torch, CUDA, and horizon_plugin_pytorch")
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
        if requested_execution == "docker" and not docker_probe["verified"]:
            if docker_image:
                limitations.append("configured X5 OE Docker image could not be verified: " + str(docker_probe["error"]))
            else:
                limitations.append("configure and verify an X5 OE Docker image before running PTQ")
        elif requested_execution == "host" and not host_ptq_available:
            limitations.append("explicit host mode selected but hb_mapper and hb_model_info were not found")

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
        "execution": {
            "preferred_mode": "docker",
            "selected_mode": execution_mode,
            "docker_image": docker_probe,
            "host_fallback_available": (
                host_qat_available if args.workflow == "qat" else host_ptq_available
            ),
        },
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
    parser.add_argument(
        "--docker-image",
        help="A locally available X5 OE Docker image; never pulled by this read-only probe",
    )
    parser.add_argument(
        "--execution-mode",
        choices=("docker", "host"),
        help="Use Docker by default; select host only when the OE host toolchain is explicitly configured",
    )
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
