#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Validate fixed release artifact sources without contacting external services."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "release-artifacts.json"
SCRIPT_PATH = ROOT / "scripts/release_artifacts.py"
DOC_PATH = ROOT / "docs/offline-artifact-delivery.md"
EXPECTED_RELEASES = {
    "x5-1.2.8": {
        "platform": "x5",
        "version": "1.2.8",
        "public_ids": {"sdk", "docs-zh", "docs-en", "docker-cpu-offline", "docker-gpu-offline", "release-note-zh"},
        "images": {
            "registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_cpu:v1.2.8",
            "registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_gpu:v1.2.8",
        },
    },
    "s-3.7.0": {
        "platform": "s-series",
        "version": "3.7.0",
        "public_ids": {"sdk", "docs-zh", "docker-cpu-offline", "docker-gpu-offline", "s100-dsp-ucp-tutorial"},
        "images": {
            "registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_cpu:v3.7.0",
            "registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_gpu:v3.7.0",
        },
    },
}


def assert_true(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_manifest(manifest: dict[str, Any], failures: list[str]) -> None:
    assert_true(manifest.get("schema_version") == 1, "Unsupported artifact manifest schema", failures)
    policy = manifest.get("credential_policy", {})
    assert_true(policy.get("registry_username_env") == "DROBOTICS_REGISTRY_USERNAME", "Missing registry username environment contract", failures)
    assert_true(policy.get("registry_password_env") == "DROBOTICS_REGISTRY_PASSWORD", "Missing registry password environment contract", failures)

    releases = manifest.get("releases", {})
    for release_id, expected in EXPECTED_RELEASES.items():
        release = releases.get(release_id)
        assert_true(isinstance(release, dict), f"Missing fixed release: {release_id}", failures)
        if not isinstance(release, dict):
            continue
        assert_true(release.get("platform") == expected["platform"], f"Wrong platform for {release_id}", failures)
        assert_true(release.get("release_version") == expected["version"], f"Wrong version for {release_id}", failures)

        artifacts = release.get("public_artifacts", [])
        identifiers = {artifact.get("id") for artifact in artifacts if isinstance(artifact, dict)}
        assert_true(identifiers == expected["public_ids"], f"Unexpected public artifacts for {release_id}", failures)
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                failures.append(f"Malformed artifact in {release_id}")
                continue
            url = str(artifact.get("url", ""))
            filename = str(artifact.get("filename", ""))
            parsed = urlparse(url)
            assert_true(parsed.scheme == "https", f"Artifact URL must use HTTPS: {artifact.get('id')}", failures)
            assert_true(parsed.netloc == "d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com", f"Unexpected artifact host: {artifact.get('id')}", failures)
            assert_true(parsed.path.endswith(f"/{filename}"), f"Filename does not match URL: {artifact.get('id')}", failures)
            assert_true(not parsed.query and not parsed.fragment, f"Artifact URL must be immutable without query/fragment: {artifact.get('id')}", failures)

        registry = release.get("registry", {})
        assert_true(registry.get("host") == "registry.d-robotics.cc", f"Wrong Registry host for {release_id}", failures)
        images = {image.get("image") for image in registry.get("images", []) if isinstance(image, dict)}
        assert_true(images == expected["images"], f"Unexpected Registry images for {release_id}", failures)


def check_security_contract(failures: list[str]) -> None:
    content = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (MANIFEST_PATH, SCRIPT_PATH, DOC_PATH)
    )
    assert_true(not re.search(r"docker\s+login\b[^\n]*\s-p(?:\s|=)", content, re.I), "Unsafe docker login -p command found", failures)
    assert_true("--password-stdin" in content, "Password-stdin guidance is missing", failures)
    assert_true('"password"' not in MANIFEST_PATH.read_text(encoding="utf-8"), "Manifest must not contain a password value field", failures)


def check_integrations(failures: list[str]) -> None:
    for path in (
        DOC_PATH,
        ROOT / "platforms/x5/PACK.md",
        ROOT / "platforms/s-series/PACK.md",
        ROOT / "skills/x5-environment-setup/SKILL.md",
    ):
        assert_true(path.is_file(), f"Missing integration file: {path}", failures)
        if path.is_file() and path != DOC_PATH:
            assert_true("offline-artifact-delivery.md" in path.read_text(encoding="utf-8"), f"Offline artifact guide is not linked from {path}", failures)


def check_renderer(failures: list[str]) -> None:
    for release_id in EXPECTED_RELEASES:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT_PATH), "--release", release_id, "--mode", "wget"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(result.returncode == 0, f"Release command renderer failed for {release_id}: {result.stderr.strip()}", failures)
        assert_true("wget --continue --https-only" in result.stdout, f"Missing wget output for {release_id}", failures)

        registry_result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT_PATH), "--release", release_id, "--mode", "docker-pull"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(registry_result.returncode == 0, f"Registry command renderer failed for {release_id}: {registry_result.stderr.strip()}", failures)
        assert_true("--password-stdin" in registry_result.stdout, f"Safe Registry login missing for {release_id}", failures)
        assert_true(not re.search(r"\s-p(?:\s|=)", registry_result.stdout), f"Unsafe Registry login output for {release_id}", failures)


def main() -> int:
    failures: list[str] = []
    assert_true(MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}", failures)
    assert_true(SCRIPT_PATH.is_file(), f"Missing renderer: {SCRIPT_PATH}", failures)
    assert_true(DOC_PATH.is_file(), f"Missing guide: {DOC_PATH}", failures)
    if not failures:
        try:
            manifest = load_manifest()
        except (OSError, json.JSONDecodeError) as error:
            failures.append(f"Cannot load manifest: {error}")
        else:
            check_manifest(manifest, failures)
            check_security_contract(failures)
            check_integrations(failures)
            check_renderer(failures)

    if failures:
        print("\n".join(f"FAIL: {failure}" for failure in failures), file=sys.stderr)
        return 1
    print("RELEASE_ARTIFACT_VALIDATION_OK: fixed X5 1.2.8 and S 3.7.0 sources; no embedded Registry credentials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())