# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Validate formal component Release events before creating Hub upgrades."""

from dataclasses import dataclass
from pathlib import Path
import re
import sys

import yaml


SCRIPT_DIR = str(Path(__file__).resolve().parent)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
from release_contract import STABLE_TAG, semver_key as canonical_semver_key  # noqa: E402

COMMIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


class ValidationError(ValueError):
    """Raised when a component Release event is not eligible for an upgrade."""


@dataclass(frozen=True)
class ComponentRef:
    """A component registration and its currently pinned source tag."""

    component_id: str
    repo: str
    ref: str
    path: Path


@dataclass(frozen=True)
class ComponentReleaseEvent:
    """Facts supplied by the source Release workflow."""

    source_repo: str
    tag: str
    target_sha: str
    release_url: str
    published_at: str
    is_draft: bool | None = None
    is_prerelease: bool | None = None


@dataclass(frozen=True)
class UpgradeDecision:
    """The idempotent result of evaluating one valid component Release."""

    action: str


def semver_key(tag: str) -> tuple[int, int, int]:
    """Return the numeric ordering key for one canonical stable tag."""
    try:
        return canonical_semver_key(tag)
    except ValueError as error:
        raise ValidationError("release tag must be a stable release tag") from error


def load_components(root: Path) -> list[ComponentRef]:
    """Load component registrations and require each source repository once."""
    components = []
    for path in sorted((root / "components.d").glob("*.yml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise ValidationError(f"invalid component YAML: {path}") from error
        if not isinstance(data, dict):
            raise ValidationError(f"component YAML must be a mapping: {path}")

        repo = data.get("repo")
        ref = data.get("ref")
        if not isinstance(repo, str) or not repo:
            raise ValidationError(f"component repo is required: {path}")
        try:
            canonical_semver_key(ref)
        except ValueError as error:
            raise ValidationError(
                f"component ref must be a canonical stable tag: {path}"
            ) from error
        components.append(ComponentRef(path.stem, repo, ref, path.relative_to(root)))

    repositories = [component.repo for component in components]
    if len(repositories) != len(set(repositories)):
        raise ValidationError("a source repository must map to exactly one component")
    return components


def validate_release_event(
    event: ComponentReleaseEvent,
    component: ComponentRef,
    verified_target_sha: str | None = None,
) -> None:
    """Reject events that are not a formal Release for the registered component."""
    if event.source_repo != component.repo:
        raise ValidationError("unregistered source repository")
    if STABLE_TAG.fullmatch(event.tag) is None:
        raise ValidationError("release tag must be a stable release tag")
    if COMMIT_SHA.fullmatch(event.target_sha) is None:
        raise ValidationError("target SHA must be a 40-character SHA")
    expected_url = f"https://github.com/{event.source_repo}/releases/tag/{event.tag}"
    if event.release_url != expected_url:
        raise ValidationError("release URL does not match the source repository and tag")
    if event.is_draft is not False or event.is_prerelease is not False:
        raise ValidationError("release must be published, non-draft, non-prerelease")
    if verified_target_sha is not None and event.target_sha.lower() != verified_target_sha.lower():
        raise ValidationError("target SHA mismatch")


def decide_upgrade(
    component: ComponentRef,
    event: ComponentReleaseEvent,
    verified_target_sha: str | None = None,
) -> UpgradeDecision:
    """Return ``noop`` only when the component already pins this exact tag."""
    validate_release_event(event, component, verified_target_sha)
    if semver_key(event.tag) < semver_key(component.ref):
        raise ValidationError("release tag is older than the current component ref")
    return UpgradeDecision("noop" if component.ref == event.tag else "upgrade")
