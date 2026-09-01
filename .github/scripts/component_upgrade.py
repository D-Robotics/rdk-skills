# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Trusted helpers for the Hub component-upgrade workflow."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


STABLE_TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def _require_stable_tag(value: str, field: str) -> None:
    if STABLE_TAG.fullmatch(value) is None:
        raise ValueError(f"{field} must be a stable tag")


def _require_sha(value: str) -> None:
    if COMMIT_SHA.fullmatch(value) is None:
        raise ValueError("source SHA must be a 40-character SHA")


def render_pr_body(
    *,
    component_name: str,
    component_id: str,
    previous_tag: str,
    new_tag: str,
    release_url: str,
    source_sha: str,
    catalog_dirs: list[str],
    generated_artifacts: list[str],
    test_result: str,
) -> str:
    """Render the review body without evaluating any component-owned text."""
    _require_stable_tag(previous_tag, "previous tag")
    _require_stable_tag(new_tag, "new tag")
    _require_sha(source_sha)
    if not component_name or not component_id or not release_url or not test_result:
        raise ValueError("PR body fields must be non-empty")
    if any(not isinstance(item, str) or not item for item in catalog_dirs):
        raise ValueError("catalog directories must be non-empty strings")
    if any(not isinstance(item, str) or not item for item in generated_artifacts):
        raise ValueError("generated artifacts must be non-empty strings")

    mirrors = "\n".join(f"- skills/{directory}" for directory in catalog_dirs) or "- None"
    artifacts = "\n".join(f"- {path}" for path in generated_artifacts) or "- None"
    return f"""## Automated component upgrade

| Field | Value |
| --- | --- |
| Component | {component_name} (`{component_id}`) |
| Previous tag | `{previous_tag}` |
| New tag | `{new_tag}` |
| Source Release | {release_url} |
| Source SHA | `{source_sha}` |

### Mirrored directories

{mirrors}

### Generated artifacts

{artifacts}

### Tests

{test_result}

A maintainer must review this PR and choose the eventual Hub version after merge.
"""


def validate_sync_summary(summary: Any, expected_source_sha: str) -> list[str]:
    """Return synchronized catalog dirs only when their checkout matches the API SHA."""
    _require_sha(expected_source_sha)
    if not isinstance(summary, dict) or not isinstance(summary.get("components"), list):
        raise ValueError("invalid synchronization summary")
    components = summary["components"]
    if len(components) != 1 or not isinstance(components[0], dict):
        raise ValueError("synchronization summary must contain exactly one component")
    actual_sha = components[0].get("source_sha")
    catalog_dirs = components[0].get("catalog_dirs")
    if not isinstance(actual_sha, str) or actual_sha.lower() != expected_source_sha.lower():
        raise ValueError("synchronized source SHA does not match the verified Release SHA")
    if not isinstance(catalog_dirs, list) or any(
        not isinstance(directory, str) or not directory for directory in catalog_dirs
    ):
        raise ValueError("synchronization summary has invalid catalog directories")
    return catalog_dirs


def require_labels(available_labels: list[str], component_id: str) -> None:
    """Fail before mutation unless maintainer-provisioned PR labels exist."""
    required = {"component-upgrade", f"source:{component_id}"}
    missing = sorted(required.difference(available_labels))
    if missing:
        raise ValueError(f"required labels are not provisioned: {', '.join(missing)}")


def resolve_action(candidate_action: str, *, has_drift: bool) -> str:
    """Turn a tag-only noop into a repair upgrade when artifacts drift."""
    if candidate_action not in {"noop", "upgrade"}:
        raise ValueError("unknown component upgrade action")
    return "upgrade" if candidate_action == "noop" and has_drift else candidate_action


def _json_list(value: str) -> list[str]:
    decoded = json.loads(value)
    if not isinstance(decoded, list):
        raise ValueError("expected a JSON list")
    return decoded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    sync = commands.add_parser("validate-sync-summary")
    sync.add_argument("--summary-file", type=Path, required=True)
    sync.add_argument("--source-sha", required=True)

    labels = commands.add_parser("require-labels")
    labels.add_argument("--labels-json", required=True)
    labels.add_argument("--component", required=True)

    render = commands.add_parser("render-pr-body")
    render.add_argument("--component-name", required=True)
    render.add_argument("--component", required=True)
    render.add_argument("--previous-tag", required=True)
    render.add_argument("--new-tag", required=True)
    render.add_argument("--release-url", required=True)
    render.add_argument("--source-sha", required=True)
    render.add_argument("--catalog-dirs-json", required=True)
    render.add_argument("--artifacts-json", required=True)
    render.add_argument("--test-result", required=True)

    args = parser.parse_args()
    if args.command == "validate-sync-summary":
        summary = json.loads(args.summary_file.read_text(encoding="utf-8"))
        print(json.dumps(validate_sync_summary(summary, args.source_sha)))
    elif args.command == "require-labels":
        labels_data = json.loads(args.labels_json)
        if not isinstance(labels_data, list) or any(
            not isinstance(item, dict) or not isinstance(item.get("name"), str)
            for item in labels_data
        ):
            raise ValueError("label API response is invalid")
        require_labels([item["name"] for item in labels_data], args.component)
    else:
        print(
            render_pr_body(
                component_name=args.component_name,
                component_id=args.component,
                previous_tag=args.previous_tag,
                new_tag=args.new_tag,
                release_url=args.release_url,
                source_sha=args.source_sha,
                catalog_dirs=_json_list(args.catalog_dirs_json),
                generated_artifacts=_json_list(args.artifacts_json),
                test_result=args.test_result,
            ),
            end="",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
