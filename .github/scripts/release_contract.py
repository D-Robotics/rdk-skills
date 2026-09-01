# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Canonical SemVer and GitHub Release-state validation helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


SEMVER_CORE = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
STABLE_TAG = re.compile(rf"^v{SEMVER_CORE}$")
HUB_VERSION = re.compile(rf"^{SEMVER_CORE}$")
COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
HTTP_STATUS = re.compile(r"(?mi)^HTTP/[0-9.]+[ \t]+([0-9]{3})(?:[ \t]|$)")
NOTES_DIGEST = re.compile(r"(?m)^Release-Notes-SHA256: ([0-9a-f]{64})\r?$")


def github_http_status(response: str) -> int:
    """Return the final numeric HTTP status emitted by ``gh api --include``."""
    if not isinstance(response, str):
        raise ValueError("GitHub response must be text")
    matches = HTTP_STATUS.findall(response)
    if not matches:
        raise ValueError("GitHub response did not contain an HTTP status")
    return int(matches[-1])


def release_notes_sha256(notes: bytes) -> str:
    """Return the digest embedded in a normal-publication annotated tag."""
    if not isinstance(notes, bytes):
        raise ValueError("Release notes must be bytes")
    return hashlib.sha256(notes).hexdigest()


def require_release_notes_digest(tag_object: str, notes: bytes) -> None:
    """Bind release-only recovery to the exact notes preserved by the tag."""
    if not isinstance(tag_object, str):
        raise ValueError("annotated tag object must be text")
    digests = NOTES_DIGEST.findall(tag_object)
    if len(digests) != 1:
        raise ValueError("annotated tag must contain exactly one Release notes digest")
    if digests[0] != release_notes_sha256(notes):
        raise ValueError("validated Release notes do not match the annotated tag")


def semver_key(value: str, *, leading_v: bool = True) -> tuple[int, int, int]:
    """Return the numeric key for a canonical stable tag or Hub version."""
    pattern = STABLE_TAG if leading_v else HUB_VERSION
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        kind = "tag" if leading_v else "version"
        raise ValueError(f"invalid canonical semantic {kind}")
    numeric = value[1:] if leading_v else value
    return tuple(int(part) for part in numeric.split("."))


def previous_release_tag(tags: Iterable[str], *, destination_tag: str) -> str:
    """Return the newest canonical ancestor tag other than the destination."""
    semver_key(destination_tag)
    candidates = {
        tag.strip()
        for tag in tags
        if isinstance(tag, str)
        and tag.strip() != destination_tag
        and STABLE_TAG.fullmatch(tag.strip()) is not None
    }
    return max(candidates, key=semver_key, default="")


def _remote_tag_map(tag_refs: str) -> dict[str, str]:
    refs: dict[str, str] = {}
    for raw_line in tag_refs.splitlines():
        if not raw_line:
            continue
        try:
            sha, ref = raw_line.split("\t", 1)
        except ValueError as error:
            raise ValueError("destination tag query returned malformed data") from error
        if COMMIT_SHA.fullmatch(sha) is None or ref in refs:
            raise ValueError("destination tag query returned malformed data")
        refs[ref] = sha.lower()
    return refs


def plan_release_destination(
    tag_refs: str,
    *,
    tag: str,
    candidate_sha: str,
    release_status: int,
    recover_existing_tag: bool,
) -> str:
    """Choose normal publication or exact-tag Release-only recovery."""
    if STABLE_TAG.fullmatch(tag) is None or COMMIT_SHA.fullmatch(candidate_sha) is None:
        raise ValueError("invalid release destination inputs")
    if release_status == 200:
        raise ValueError(f"destination GitHub Release already exists: {tag}")
    if release_status != 404:
        raise ValueError("could not prove the destination GitHub Release is absent")

    refs = _remote_tag_map(tag_refs)
    direct_ref = f"refs/tags/{tag}"
    peeled_ref = f"{direct_ref}^{{}}"
    unexpected = set(refs).difference({direct_ref, peeled_ref})
    if unexpected or (peeled_ref in refs and direct_ref not in refs):
        raise ValueError("destination tag query returned malformed data")

    if direct_ref not in refs:
        if recover_existing_tag:
            raise ValueError("recovery requires an existing exact annotated tag")
        return "create-tag"
    if not recover_existing_tag:
        raise ValueError(f"destination tag already exists: {tag}")
    if peeled_ref not in refs:
        raise ValueError("recovery requires an existing exact annotated tag")
    if refs[peeled_ref] != candidate_sha.lower():
        raise ValueError("existing destination tag does not resolve to the candidate")
    return "release-only"


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def normalize_release_facts(facts: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Return the security-relevant tuple for each published annotated Release."""
    normalized: dict[tuple[str, str], dict[str, str]] = {}
    for raw_fact in facts:
        fact = _mapping(raw_fact, "source Release fact")
        repo = fact.get("repo")
        tag = fact.get("tag")
        if (
            not isinstance(repo, str)
            or re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) is None
            or not isinstance(tag, str)
            or STABLE_TAG.fullmatch(tag) is None
        ):
            raise ValueError("source Release fact has an invalid repository or tag")
        key = (repo, tag)
        if key in normalized:
            raise ValueError(f"duplicate source Release fact: {repo} {tag}")

        release = _mapping(fact.get("release"), "source Release API response")
        canonical_url = f"https://github.com/{repo}/releases/tag/{tag}"
        published_at = release.get("published_at")
        if (
            release.get("tag_name") != tag
            or release.get("draft") is not False
            or release.get("prerelease") is not False
            or not isinstance(published_at, str)
            or not published_at
            or release.get("html_url") != canonical_url
        ):
            raise ValueError(f"record lacks a published formal source Release: {repo} {tag}")

        tag_ref = _mapping(fact.get("tag_ref"), "source tag API response")
        tag_ref_object = _mapping(tag_ref.get("object"), "source tag object")
        tag_object_sha = tag_ref_object.get("sha")
        if tag_ref_object.get("type") != "tag" or not isinstance(
            tag_object_sha, str
        ) or COMMIT_SHA.fullmatch(tag_object_sha) is None:
            raise ValueError(f"source tag is not annotated: {repo} {tag}")

        tag_object = _mapping(fact.get("tag_object"), "annotated tag API response")
        returned_tag_object_sha = tag_object.get("sha")
        if returned_tag_object_sha is not None and (
            not isinstance(returned_tag_object_sha, str)
            or returned_tag_object_sha.lower() != tag_object_sha.lower()
        ):
            raise ValueError(f"annotated source tag object changed: {repo} {tag}")
        target = _mapping(tag_object.get("object"), "annotated tag target")
        source_sha = target.get("sha")
        if target.get("type") != "commit" or not isinstance(
            source_sha, str
        ) or COMMIT_SHA.fullmatch(source_sha) is None:
            raise ValueError(f"annotated source tag does not resolve to a commit: {repo} {tag}")

        normalized[key] = {
            "repo": repo,
            "tag": tag,
            "release_url": canonical_url,
            "published_at": published_at,
            "tag_object_sha": tag_object_sha.lower(),
            "source_sha": source_sha.lower(),
        }
    return [normalized[key] for key in sorted(normalized)]


def require_release_facts_unchanged(
    expected: Iterable[dict[str, Any]], current: Iterable[dict[str, Any]]
) -> list[dict[str, str]]:
    """Reject source Release evidence that changed while approval was pending."""
    expected_normalized = normalize_release_facts(expected)
    current_normalized = normalize_release_facts(current)
    if current_normalized != expected_normalized:
        raise ValueError("source Release facts changed during Environment approval")
    return current_normalized


def _boolean(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError("boolean value must be true or false")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    tag = commands.add_parser("validate-tag")
    tag.add_argument("value")
    version = commands.add_parser("validate-version")
    version.add_argument("value")
    status = commands.add_parser("http-status")
    status.add_argument("--response-file", type=Path, required=True)
    notes_sha = commands.add_parser("notes-sha")
    notes_sha.add_argument("--notes-file", type=Path, required=True)
    notes_verify = commands.add_parser("verify-notes-hash")
    notes_verify.add_argument("--tag-object-file", type=Path, required=True)
    notes_verify.add_argument("--notes-file", type=Path, required=True)
    previous_tag = commands.add_parser("previous-tag")
    previous_tag.add_argument("--tags-file", type=Path, required=True)
    previous_tag.add_argument("--destination-tag", required=True)
    destination = commands.add_parser("destination-state")
    destination.add_argument("--tag-refs-file", type=Path, required=True)
    destination.add_argument("--tag", required=True)
    destination.add_argument("--candidate-sha", required=True)
    destination.add_argument("--release-status", type=int, required=True)
    destination.add_argument("--recover-existing-tag", required=True)
    validate_facts = commands.add_parser("validate-facts")
    validate_facts.add_argument("--facts-json", type=Path, required=True)
    compare_facts = commands.add_parser("compare-facts")
    compare_facts.add_argument("--expected-json", type=Path, required=True)
    compare_facts.add_argument("--current-json", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.command == "validate-tag":
            semver_key(args.value)
        elif args.command == "validate-version":
            semver_key(args.value, leading_v=False)
        elif args.command == "http-status":
            print(github_http_status(args.response_file.read_text(encoding="utf-8")))
        elif args.command == "notes-sha":
            print(release_notes_sha256(args.notes_file.read_bytes()))
        elif args.command == "verify-notes-hash":
            require_release_notes_digest(
                args.tag_object_file.read_text(encoding="utf-8"),
                args.notes_file.read_bytes(),
            )
        elif args.command == "previous-tag":
            print(
                previous_release_tag(
                    args.tags_file.read_text(encoding="utf-8").splitlines(),
                    destination_tag=args.destination_tag,
                )
            )
        elif args.command == "destination-state":
            print(
                plan_release_destination(
                    args.tag_refs_file.read_text(encoding="utf-8"),
                    tag=args.tag,
                    candidate_sha=args.candidate_sha,
                    release_status=args.release_status,
                    recover_existing_tag=_boolean(args.recover_existing_tag),
                )
            )
        elif args.command == "validate-facts":
            facts = json.loads(args.facts_json.read_text(encoding="utf-8"))
            if not isinstance(facts, list):
                raise ValueError("source Release facts must be an array")
            print(json.dumps(normalize_release_facts(facts), sort_keys=True))
        elif args.command == "compare-facts":
            expected = json.loads(args.expected_json.read_text(encoding="utf-8"))
            current = json.loads(args.current_json.read_text(encoding="utf-8"))
            if not isinstance(expected, list) or not isinstance(current, list):
                raise ValueError("source Release facts must be arrays")
            print(json.dumps(require_release_facts_unchanged(expected, current), sort_keys=True))
        else:
            raise ValueError("unknown release contract command")
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"release contract rejected: {error}") from error
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
