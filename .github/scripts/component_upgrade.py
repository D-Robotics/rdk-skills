# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Trusted helpers for the Hub component-upgrade workflow."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from release_contract import STABLE_TAG, semver_key  # noqa: E402


COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
GENERATED_EXACT_PATHS = {
    "README.md",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    ".cursor-plugin/marketplace.json",
    ".dsh-plugin/marketplace.json",
}
FAILURE_JOBS = ("validate", "build-proposal", "upsert-pr")
JOB_RESULTS = {"success", "failure", "cancelled", "skipped"}


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


def require_release_order(
    *, incoming_tag: str, main_tag: str, proposal_tag: str | None = None
) -> None:
    """Reject a formal event older than main or the current stable proposal."""
    incoming = semver_key(incoming_tag)
    if incoming < semver_key(main_tag):
        raise ValueError("incoming release is older than protected main")
    if proposal_tag and incoming < semver_key(proposal_tag):
        raise ValueError("incoming release is older than the existing proposal")


def require_dispatch_authority(
    *, dry_run: bool, actor: str, expected_actor: str
) -> None:
    """Permit manual dry-runs but bind every non-dry run to the dispatcher App."""
    if not isinstance(dry_run, bool):
        raise ValueError("dry_run must be boolean")
    if dry_run:
        return
    if not isinstance(expected_actor, str) or not expected_actor.endswith("[bot]"):
        raise ValueError("expected dispatcher bot is not configured")
    if actor != expected_actor:
        raise ValueError("non-dry workflow dispatch must use the expected dispatcher bot")


def render_failure_issue(
    *,
    component_id: str | None,
    source_repo: str | None,
    tag: str | None,
    job_results: dict[str, str],
    run_url: str,
) -> tuple[str, str]:
    """Render a bounded tracker from allowlisted fields, never raw logs or payloads."""
    safe_component = (
        component_id
        if isinstance(component_id, str)
        and len(component_id) <= 64
        and re.fullmatch(r"[a-z0-9][a-z0-9-]*", component_id)
        else "general"
    )
    safe_repo = (
        source_repo
        if isinstance(source_repo, str)
        and len(source_repo) <= 200
        and re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source_repo)
        else "unavailable"
    )
    safe_tag = (
        tag
        if isinstance(tag, str)
        and len(tag) <= 100
        and STABLE_TAG.fullmatch(tag) is not None
        else "unavailable"
    )
    if not isinstance(job_results, dict):
        raise ValueError("job results must be an object")
    if (
        not isinstance(run_url, str)
        or len(run_url) > 300
        or re.fullmatch(
            r"https://[A-Za-z0-9.-]+/[A-Za-z0-9_.-]+/"
            r"[A-Za-z0-9_.-]+/actions/runs/[0-9]+",
            run_url,
        )
        is None
    ):
        raise ValueError("invalid workflow run URL")
    result_lines = []
    for job in FAILURE_JOBS:
        result = job_results.get(job, "skipped")
        if result not in JOB_RESULTS:
            result = "unknown"
        result_lines.append(f"- {job}: {result}")
    title = f"Component upgrade failure tracker: {safe_component}"
    body = (
        "The component upgrade workflow failed without changing protected `main`.\n\n"
        f"**Most recent run:** {run_url}\n\n"
        f"**Component:** `{safe_component}`\n"
        f"**Source:** `{safe_repo}`\n"
        f"**Tag:** `{safe_tag}`\n\n"
        "**Job results:**\n"
        + "\n".join(result_lines)
        + "\n\nRaw payloads, command output, and credentials are intentionally omitted.\n"
    )
    if len(body) > 2000:
        raise ValueError("failure Issue body exceeded its bound")
    return title, body


def _git_paths(root: Path, *arguments: str) -> list[str]:
    result = subprocess.run(
        ["git", *arguments, "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        value.decode("utf-8", errors="surrogateescape")
        for value in result.stdout.split(b"\0")
        if value
    ]


def stage_and_validate_proposal(
    root: Path,
    *,
    component_file: str,
    catalog_dirs: list[str],
    repair: bool,
) -> list[str]:
    """Force-stage all drift, then reject every path outside the proposal policy."""
    root = root.resolve()
    if not component_file.startswith("components.d/") or not component_file.endswith(".yml"):
        raise ValueError("invalid component file")
    if not catalog_dirs or any(
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9_.-]+", value) is None
        or value in (".", "..")
        for value in catalog_dirs
    ):
        raise ValueError("invalid catalog directories")

    subprocess.run(
        ["git", "add", "-A", "-f", "--", "."],
        cwd=root,
        check=True,
        capture_output=True,
    )
    staged = _git_paths(root, "diff", "--cached", "--name-only")
    allowed_exact = set(GENERATED_EXACT_PATHS)
    if not repair:
        allowed_exact.add(component_file)
    allowed_prefixes = ["plugins/", *(f"skills/{value}/" for value in catalog_dirs)]
    for path in staged:
        if path in allowed_exact or any(path.startswith(prefix) for prefix in allowed_prefixes):
            continue
        raise ValueError(f"component upgrade contains an unexpected staged path: {path}")

    subprocess.run(
        ["git", "diff", "--cached", "--check"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return staged


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

    order = commands.add_parser("require-release-order")
    order.add_argument("--incoming-tag", required=True)
    order.add_argument("--main-tag", required=True)
    order.add_argument("--proposal-tag")

    authority = commands.add_parser("require-dispatch-authority")
    authority.add_argument("--dry-run", choices=("true", "false"), required=True)
    authority.add_argument("--actor", required=True)
    authority.add_argument("--expected-actor", required=True)

    stage = commands.add_parser("stage-proposal")
    stage.add_argument("--root", type=Path, default=Path.cwd())
    stage.add_argument("--component-file", required=True)
    stage.add_argument("--catalog-dirs-json", required=True)
    stage.add_argument("--repair", action="store_true")

    failure = commands.add_parser("render-failure-issue")
    failure.add_argument("--component")
    failure.add_argument("--source-repo")
    failure.add_argument("--tag")
    failure.add_argument("--job-results-json", required=True)
    failure.add_argument("--run-url", required=True)
    failure.add_argument("--title-file", type=Path, required=True)
    failure.add_argument("--body-file", type=Path, required=True)

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
    elif args.command == "render-pr-body":
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
    elif args.command == "require-release-order":
        require_release_order(
            incoming_tag=args.incoming_tag,
            main_tag=args.main_tag,
            proposal_tag=args.proposal_tag,
        )
    elif args.command == "require-dispatch-authority":
        require_dispatch_authority(
            dry_run=args.dry_run == "true",
            actor=args.actor,
            expected_actor=args.expected_actor,
        )
    elif args.command == "stage-proposal":
        print(
            json.dumps(
                stage_and_validate_proposal(
                    args.root,
                    component_file=args.component_file,
                    catalog_dirs=_json_list(args.catalog_dirs_json),
                    repair=args.repair,
                )
            )
        )
    else:
        results = json.loads(args.job_results_json)
        title, body = render_failure_issue(
            component_id=args.component,
            source_repo=args.source_repo,
            tag=args.tag,
            job_results=results,
            run_url=args.run_url,
        )
        args.title_file.write_text(title, encoding="utf-8")
        args.body_file.write_text(body, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
