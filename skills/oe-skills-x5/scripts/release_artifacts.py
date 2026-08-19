#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Render fixed-release public download, Docker pull, and Docker load commands."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "release-artifacts.json"


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("releases"), dict):
        raise ValueError(f"Unexpected release artifact manifest: {path}")
    return data


def select_release(manifest: dict[str, Any], release_id: str) -> dict[str, Any]:
    release = manifest["releases"].get(release_id)
    if not isinstance(release, dict):
        raise ValueError(f"Unknown release: {release_id}")
    return release


def select_artifacts(release: dict[str, Any], requested_ids: list[str]) -> list[dict[str, Any]]:
    artifacts = release.get("public_artifacts")
    if not isinstance(artifacts, list):
        raise ValueError("Release has no public artifacts")
    if not requested_ids:
        return artifacts

    requested = set(requested_ids)
    selected = [artifact for artifact in artifacts if artifact.get("id") in requested]
    selected_ids = {str(artifact.get("id")) for artifact in selected}
    missing = sorted(requested - selected_ids)
    if missing:
        raise ValueError(f"Unknown public artifact IDs: {', '.join(missing)}")
    return selected


def render_list(release_id: str, release: dict[str, Any]) -> None:
    print(f"release={release_id} platform={release.get('platform')} version={release.get('release_version')}")
    print("public artifacts:")
    for artifact in release["public_artifacts"]:
        print(f"  {artifact['id']}: {artifact['filename']}")
    print("registry images:")
    for image in release["registry"]["images"]:
        print(f"  {image['id']}: {image['image']}")


def render_wget(release_id: str, artifacts: list[dict[str, Any]], output_dir: Path) -> None:
    directory = output_dir / release_id
    print(f"mkdir -p {shlex.quote(directory.as_posix())}")
    for artifact in artifacts:
        print(
            "wget --continue --https-only --show-progress "
            f"--directory-prefix {shlex.quote(directory.as_posix())} {shlex.quote(str(artifact['url']))}"
        )
    filenames = " ".join(shlex.quote(str(artifact["filename"])) for artifact in artifacts)
    print(f"(cd {shlex.quote(directory.as_posix())} && sha256sum {filenames} > SHA256SUMS.local)")


def render_docker_pull(manifest: dict[str, Any], release: dict[str, Any]) -> None:
    policy = manifest["credential_policy"]
    username_env = policy["registry_username_env"]
    password_env = policy["registry_password_env"]
    host = release["registry"]["host"]
    print(f"test -n \"${{{username_env}:-}}\"")
    print(f"test -n \"${{{password_env}:-}}\"")
    print(
        f"printf '%s' \"${{{password_env}}}\" | docker login {shlex.quote(str(host))} "
        f"--username \"${{{username_env}}}\" --password-stdin"
    )
    for image in release["registry"]["images"]:
        print(f"docker pull {shlex.quote(str(image['image']))}")


def render_docker_load(release_id: str, artifacts: list[dict[str, Any]], output_dir: Path) -> None:
    directory = output_dir / release_id
    docker_artifacts = [artifact for artifact in artifacts if artifact.get("type") == "docker-offline-image"]
    if not docker_artifacts:
        raise ValueError("Selected artifacts contain no offline Docker images")
    for artifact in docker_artifacts:
        print(f"docker load -i {shlex.quote((directory / str(artifact['filename'])).as_posix())}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render commands for fixed D-Robotics release artifacts without downloading or storing credentials."
    )
    parser.add_argument("--release", required=True, help="Release ID, such as x5-1.2.8 or s-3.7.0")
    parser.add_argument(
        "--mode",
        choices=("list", "wget", "docker-pull", "docker-load", "json"),
        default="list",
        help="Output-only mode; this tool never downloads artifacts or invokes Docker.",
    )
    parser.add_argument("--artifact", action="append", default=[], help="Public artifact ID to include; repeatable")
    parser.add_argument("--output-dir", type=Path, default=Path("release-artifacts"))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    release = select_release(manifest, args.release)
    artifacts = select_artifacts(release, args.artifact)

    if args.mode == "list":
        render_list(args.release, release)
    elif args.mode == "wget":
        render_wget(args.release, artifacts, args.output_dir)
    elif args.mode == "docker-pull":
        render_docker_pull(manifest, release)
    elif args.mode == "docker-load":
        render_docker_load(args.release, artifacts, args.output_dir)
    else:
        print(json.dumps({"release": args.release, "data": release}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)