#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Probe a D-Robotics S OE environment without pulling images or exposing secrets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


IMAGE_PATTERN = re.compile(
    r"\Aregistry\.d-robotics\.cc/deliver/"
    r"ai_toolchain_ubuntu_22_s100_s600_(cpu|gpu):"
    r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z"
)
VERSION_PATTERN = re.compile(r"\Av?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
CONFIG_KEYS = {"OE_DIR", "OE_VERSION", "EXECUTION_MODE", "DOCKER_IMAGE"}
IMAGE_PREFIX = "registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_"


def check(ok: bool | None, evidence: str) -> dict[str, Any]:
    return {"ok": ok, "evidence": evidence}


def read_package_config(project_root: Path) -> dict[str, str]:
    """Read only non-secret keys from the workspace's simple KEY=value file."""
    path = project_root / ".drobotics-s" / ".env.oe-package"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return {}
    values: dict[str, str] = {}
    for line in lines:
        key, separator, value = line.partition("=")
        if separator and key in CONFIG_KEYS:
            values[key] = value.strip().strip("\"'")
    return values


def normalize_version(value: str | None) -> str | None:
    if value is None:
        return None
    match = VERSION_PATTERN.fullmatch(value.strip())
    if match is None:
        return None
    return ".".join(match.groups())


def image_facts(value: str) -> tuple[str, str] | None:
    match = IMAGE_PATTERN.fullmatch(value.strip())
    if match is None:
        return None
    return match.group(1), ".".join(match.groups()[1:])


def run_captured(
    command: list[str], *, timeout: int = 20, cwd: str | None = None
) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
    except (OSError, UnicodeError, subprocess.SubprocessError):
        return None


def local_image_list(docker: str) -> tuple[list[str], bool]:
    result = run_captured([docker, "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"])
    if result is None or result.returncode != 0:
        return [], False
    images = [line.strip() for line in result.stdout.splitlines() if image_facts(line.strip())]
    return sorted(set(images)), True


def select_image(
    workflow: str,
    explicit_image: str | None,
    env_image: str | None,
    config: dict[str, str],
    local_images: list[str],
) -> tuple[str | None, str]:
    configured_image = explicit_image
    if configured_image is None:
        configured_image = env_image
    if configured_image is None:
        configured_image = config.get("DOCKER_IMAGE") or None
    if configured_image is not None:
        facts = image_facts(configured_image)
        if facts is None:
            return None, "configured image is not a supported S100/S600 image"
        return configured_image.strip(), "explicitly configured S100/S600 image"

    version_hint_raw = os.environ.get("OE_VERSION") or config.get("OE_VERSION")
    version_hint = normalize_version(version_hint_raw) if version_hint_raw else None
    if version_hint_raw and version_hint is None:
        return None, "configured OE version is invalid"

    candidates = local_images
    if version_hint is not None:
        candidates = [
            image
            for image in candidates
            if image_facts(image) and image_facts(image)[1] == version_hint
        ]
        if not candidates:
            return None, "no matching S100/S600 image is present in the local cache"

    versions = {image_facts(image)[1] for image in candidates if image_facts(image)}
    if not candidates:
        return None, "no supported S100/S600 image is present in the local cache"
    if len(versions) != 1:
        return None, "multiple cached S100/S600 image versions require an explicit version or image"

    preferred_kind = "gpu" if workflow == "qat" else "cpu"
    preferred = [image for image in candidates if image_facts(image)[0] == preferred_kind]
    if preferred:
        return preferred[0], "selected the workflow-preferred image from the local cache"
    return candidates[0], "selected the only compatible image type from the local cache"


def docker_probe_command(workflow: str, image_kind: str) -> str:
    lines = [
        "set +e",
        "command -v hb_compile >/dev/null 2>&1 && hb_compile --help >/dev/null 2>&1",
        "compile_rc=$?",
        "command -v hb_config_generator >/dev/null 2>&1 && hb_config_generator --help >/dev/null 2>&1",
        "config_rc=$?",
        "qat_rc=not_checked",
        "qat_device=not_checked",
    ]
    if workflow == "qat":
        lines.extend(
            [
                "python3 -c 'import torch, horizon_plugin_pytorch; "
                "print(\"S_QAT_DEVICE:\" + (\"gpu\" if torch.cuda.is_available() else \"cpu\"))'",
                "qat_rc=$?",
                "qat_device=$(python3 -c 'import torch; print(\"gpu\" if torch.cuda.is_available() else \"cpu\")' 2>/dev/null)",
                "qat_device_rc=$?",
                "if [ \"$qat_device_rc\" -ne 0 ]; then qat_device=unknown; fi",
            ]
        )
    lines.append(
        "printf 'S_OE_PROBE:compile=%s:config=%s:qat=%s:device=%s\\n' "
        '"$compile_rc" "$config_rc" "$qat_rc" "$qat_device"'
    )
    return "; ".join(lines)


def verify_docker_image(docker: str, image: str) -> tuple[bool, str]:
    result = run_captured([docker, "image", "inspect", "--format", "{{.Id}}", image])
    if result is None or result.returncode != 0 or not result.stdout.strip():
        return False, "configured image is not available in the local Docker cache"
    return True, "configured image is available in the local Docker cache"


def verify_docker_tools(
    docker: str, image: str, workflow: str, image_kind: str
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    gpu_args = ["--gpus", "all"] if workflow == "qat" and image_kind == "gpu" else []
    command = [
        docker,
        "run",
        "--rm",
        "--pull=never",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=128m",
        *gpu_args,
        "--entrypoint",
        "/bin/bash",
        image,
        "-lc",
        docker_probe_command(workflow, image_kind),
    ]
    result = run_captured(command, timeout=45)
    checks = {
        "hb_compile": check(False, "container help check was not completed"),
        "hb_config_generator": check(False, "container help check was not completed"),
        "qat_packages": check(None, "not checked for PTQ"),
        "qat_cuda": check(None, "not checked for PTQ"),
    }
    missing: list[str] = []
    if result is None or result.returncode != 0:
        checks["hb_compile"] = check(False, "read-only container tool probe did not complete")
        checks["hb_config_generator"] = check(False, "read-only container tool probe did not complete")
        missing.extend(("hb_compile --help", "hb_config_generator --help"))
        if workflow == "qat":
            checks["qat_packages"] = check(False, "QAT package probe did not complete")
            missing.append("QAT Python packages")
            if image_kind == "gpu":
                checks["qat_cuda"] = check(False, "QAT GPU visibility probe did not complete")
                missing.append("QAT GPU visibility")
        return checks, missing

    match = re.search(
        r"S_OE_PROBE:compile=(\d+):config=(\d+):qat=([\w-]+):device=([\w-]+)",
        result.stdout,
    )
    if match is None:
        missing.extend(("hb_compile --help", "hb_config_generator --help"))
        checks["hb_compile"] = check(False, "container did not return the probe evidence")
        checks["hb_config_generator"] = check(False, "container did not return the probe evidence")
        if workflow == "qat":
            checks["qat_packages"] = check(False, "container did not return the QAT probe evidence")
            missing.append("QAT Python packages")
            if image_kind == "gpu":
                checks["qat_cuda"] = check(False, "container did not return the QAT GPU evidence")
                missing.append("QAT GPU visibility")
        return checks, missing

    compile_ok, config_ok = match.group(1) == "0", match.group(2) == "0"
    checks["hb_compile"] = check(compile_ok, "hb_compile --help exited successfully")
    checks["hb_config_generator"] = check(
        config_ok, "hb_config_generator --help exited successfully"
    )
    if not compile_ok:
        missing.append("hb_compile --help")
    if not config_ok:
        missing.append("hb_config_generator --help")

    if workflow == "qat":
        qat_ok = match.group(3) == "0"
        device = match.group(4)
        checks["qat_packages"] = check(
            qat_ok,
            "QAT Python packages import successfully" if qat_ok else "QAT Python packages could not be imported",
        )
        if not qat_ok:
            missing.append("QAT Python packages")
        if image_kind == "gpu":
            cuda_ok = device == "gpu"
            checks["qat_cuda"] = check(
                cuda_ok,
                "CUDA is visible in the selected GPU image"
                if cuda_ok
                else "CUDA is not visible in the selected GPU image",
            )
            if not cuda_ok:
                missing.append("QAT GPU visibility")
        else:
            checks["qat_cuda"] = check(
                False,
                "CPU QAT selected; CUDA is not required and training may be slower",
            )
    return checks, missing


def package_facts(project_root: Path, values: dict[str, str]) -> tuple[bool, str | None]:
    oe_dir_text = os.environ.get("OE_DIR") or values.get("OE_DIR")
    version_text = os.environ.get("OE_VERSION") or values.get("OE_VERSION")
    version = normalize_version(version_text)
    if not oe_dir_text or version is None:
        return False, None
    oe_dir = Path(oe_dir_text).expanduser()
    if not oe_dir.is_absolute():
        oe_dir = project_root / oe_dir
    try:
        oe_dir = oe_dir.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return False, None
    if not oe_dir.is_dir():
        return False, None
    markers = (
        (oe_dir / "run_docker.sh").is_file(),
        (oe_dir / "package").is_dir(),
        (oe_dir / "samples").is_dir(),
        (oe_dir / "docs").is_dir(),
        (oe_dir / "toolchain").is_dir(),
    )
    return sum(markers) >= 2, version


def verify_local_help(command_name: str) -> bool:
    executable = shutil.which(command_name)
    if not executable:
        return False
    try:
        with tempfile.TemporaryDirectory(prefix="s-oe-probe-") as temporary:
            result = run_captured([executable, "--help"], timeout=30, cwd=temporary)
    except OSError:
        return False
    return result is not None and result.returncode == 0


def verify_local_qat() -> tuple[bool, bool]:
    python = shutil.which("python3")
    if not python:
        return False, False
    command = [
        python,
        "-c",
        "import torch, horizon_plugin_pytorch; "
        "print('S_QAT_DEVICE:' + ('gpu' if torch.cuda.is_available() else 'cpu'))",
    ]
    result = run_captured(command, timeout=30)
    if result is None or result.returncode != 0:
        return False, False
    match = re.search(r"S_QAT_DEVICE:(gpu|cpu)", result.stdout)
    return True, bool(match and match.group(1) == "gpu")


def base_snapshot(workflow: str, mode: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "execution_mode": mode,
        "workflow": workflow,
        "image": None,
        "checks": {
            "docker_cli": check(None, "not used for local execution" if mode == "local" else "not checked"),
            "image_cache": check(None, "not used for local execution" if mode == "local" else "not checked"),
            "image_inspect": check(None, "not used for local execution" if mode == "local" else "not checked"),
            "oe_package": check(None, "not required for Docker execution" if mode == "docker" else "not checked"),
            "hb_compile": check(False, "not checked"),
            "hb_config_generator": check(False, "not checked"),
            "qat_packages": check(None, "not checked for PTQ" if workflow == "ptq" else "not checked"),
            "qat_cuda": check(None, "not checked for PTQ" if workflow == "ptq" else "not checked"),
        },
        "missing": [],
    }


def build_snapshot(args: argparse.Namespace, project_root: Path) -> dict[str, Any]:
    values = read_package_config(project_root)
    env_mode = os.environ.get("OE_DROBOTICS_EXECUTION_MODE")
    configured_mode = args.execution_mode or env_mode or values.get("EXECUTION_MODE")
    mode = configured_mode or "docker"
    snapshot = base_snapshot(args.workflow, mode)
    if mode not in {"docker", "local"}:
        snapshot["execution_mode"] = None
        snapshot["checks"]["execution_mode"] = check(False, "configured execution mode is invalid")
        snapshot["missing"].append("valid execution mode")
        return snapshot

    if mode == "local":
        _valid_package, version = package_facts(project_root, values)
        if _valid_package:
            snapshot["checks"]["oe_package"] = check(
                True, "OE package directory and version are configured"
            )
        else:
            snapshot["checks"]["oe_package"] = check(
                False, "OE_DIR must identify an extracted OE package and OE_VERSION must be valid"
            )
            snapshot["missing"].append("OE package path and version")

        compile_ok = verify_local_help("hb_compile") if _valid_package else False
        config_ok = verify_local_help("hb_config_generator") if _valid_package else False
        snapshot["checks"]["hb_compile"] = check(
            compile_ok, "host hb_compile --help exited successfully" if compile_ok else "host hb_compile is unavailable"
        )
        snapshot["checks"]["hb_config_generator"] = check(
            config_ok,
            "host hb_config_generator --help exited successfully"
            if config_ok
            else "host hb_config_generator is unavailable",
        )
        if not compile_ok:
            snapshot["missing"].append("host hb_compile --help")
        if not config_ok:
            snapshot["missing"].append("host hb_config_generator --help")

        if args.workflow == "qat":
            qat_ok, cuda_ok = verify_local_qat() if _valid_package else (False, False)
            snapshot["checks"]["qat_packages"] = check(
                qat_ok,
                "host QAT Python packages import successfully"
                if qat_ok
                else "host QAT Python packages are unavailable",
            )
            snapshot["checks"]["qat_cuda"] = check(
                cuda_ok,
                "host CUDA is visible"
                if cuda_ok
                else "CPU QAT selected or CUDA is not visible; training may be slower",
            )
            if not qat_ok:
                snapshot["missing"].append("host QAT Python packages")
        snapshot["status"] = "ready" if not snapshot["missing"] else "blocked"
        return snapshot

    docker = shutil.which("docker")
    if not docker:
        snapshot["checks"]["docker_cli"] = check(False, "Docker CLI is unavailable")
        snapshot["missing"].append("Docker CLI")
        return snapshot
    snapshot["checks"]["docker_cli"] = check(True, "Docker CLI is available")

    explicit_env_image = os.environ.get("OE_DROBOTICS_DOCKER_IMAGE")
    explicit_image = args.image if args.image is not None else None
    configured_image = explicit_image
    if configured_image is None:
        configured_image = explicit_env_image or values.get("DOCKER_IMAGE") or None
    if configured_image is None:
        images, listed = local_image_list(docker)
        if not listed:
            snapshot["checks"]["image_cache"] = check(False, "local Docker image cache could not be inspected")
            snapshot["missing"].append("local S100/S600 Docker image")
            return snapshot
    else:
        images, listed = [], True
    snapshot["checks"]["image_cache"] = check(
        listed,
        "checking only local S100/S600 images; no image pull is performed",
    )
    image, selection_evidence = select_image(
        args.workflow,
        explicit_image,
        explicit_env_image,
        values,
        images,
    )
    if image is None:
        snapshot["checks"]["image_inspect"] = check(False, selection_evidence)
        snapshot["missing"].append("supported local S100/S600 Docker image selection")
        return snapshot

    facts = image_facts(image)
    if facts is None:
        snapshot["checks"]["image_inspect"] = check(False, "selected image reference is unsupported")
        snapshot["missing"].append("supported S100/S600 Docker image")
        return snapshot
    image_kind, _image_version = facts
    snapshot["image"] = image
    snapshot["checks"]["image_cache"] = check(True, selection_evidence)
    image_ok, image_evidence = verify_docker_image(docker, image)
    snapshot["checks"]["image_inspect"] = check(image_ok, image_evidence)
    if not image_ok:
        snapshot["missing"].append("selected image in local Docker cache")
        return snapshot

    docker_checks, docker_missing = verify_docker_tools(
        docker, image, args.workflow, image_kind
    )
    snapshot["checks"].update(docker_checks)
    snapshot["missing"].extend(docker_missing)
    snapshot["status"] = "ready" if not snapshot["missing"] else "blocked"
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", choices=("ptq", "qat"), default="ptq")
    parser.add_argument("--image", help="Explicit supported local S100/S600 Docker image")
    parser.add_argument(
        "--execution-mode",
        choices=("docker", "local"),
        help="Docker is the default; local must be explicitly selected",
    )
    args = parser.parse_args()
    result = build_snapshot(args, Path.cwd())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
