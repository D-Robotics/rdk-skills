# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Render English, mixed-component notes for a manually approved Hub Release."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable


VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
MARKER = re.compile(r"(?:\{\{[^{}\n]+\}\}|<(?!\!)[^>\n]+>|X\.Y\.Z|\b(?:TODO|TBD|REPLACE_ME)\b)")
PRINTABLE_ASCII = re.compile(r"^[\x09\x0a\x0d\x20-\x7e]*$")

COMPONENTS = {
    "D-Robotics/bsp-skills": "BSP Skills",
    "D-Robotics/rdk-device-skills": "RDK Device Skills",
    "D-Robotics/oe-skills-x5": "OE Skills X5",
    "D-Robotics/oe-skills-s": "OE Skills S",
}
COMPONENT_NAME_ALIASES = {
    "BSP Skills": "BSP Skills",
    "RDK Device Skills": "RDK Device Skills",
    "OE Skills X5": "OE Skills X5",
    "OE Skills S": "OE Skills S",
    "OE Tool Chain (X5)": "OE Skills X5",
    "OE Tool Chain (S)": "OE Skills S",
}


@dataclass(frozen=True)
class ReleaseNotes:
    """The exact public title and body to submit to GitHub Releases."""

    title: str
    body: str


def contains_cjk(text: str) -> bool:
    """Return whether text contains Japanese, Chinese, or Korean ideographs."""
    return CJK.search(text) is not None


def _require_english(value: str, field: str) -> None:
    if not isinstance(value, str) or not PRINTABLE_ASCII.fullmatch(value) or contains_cjk(value):
        raise ValueError(f"{field} must contain English ASCII text only")
    if MARKER.search(value):
        raise ValueError(f"{field} contains an unresolved marker")


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _validate_components(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for row in rows:
        row = _require_mapping(row, "component")
        repo = row.get("repo")
        ref = row.get("ref")
        release_url = row.get("release_url")
        if repo not in COMPONENTS:
            raise ValueError("component is not a registered formal source")
        if repo in normalized:
            raise ValueError(f"duplicate component row: {repo}")
        if not isinstance(ref, str) or TAG.fullmatch(ref) is None:
            raise ValueError(f"invalid component tag for {repo}")
        expected_url = f"https://github.com/{repo}/releases/tag/{ref}"
        if release_url != expected_url or row.get("formal_release") is not True:
            raise ValueError(f"component lacks a formal source Release: {repo}")
        normalized[repo] = row
    if set(normalized) != set(COMPONENTS):
        raise ValueError("each registered component must have one formal source Release")
    return normalized


def _validate_upgrades(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    validated = []
    for row in rows:
        row = _require_mapping(row, "component-upgrade metadata")
        component = row.get("component")
        from_tag = row.get("from_tag")
        to_tag = row.get("to_tag")
        release_url = row.get("release_url")
        canonical_component = COMPONENT_NAME_ALIASES.get(component)
        if canonical_component is None:
            raise ValueError("component-upgrade metadata has an unknown component")
        if not isinstance(from_tag, str) or TAG.fullmatch(from_tag) is None:
            raise ValueError("component-upgrade metadata has an invalid previous tag")
        if not isinstance(to_tag, str) or TAG.fullmatch(to_tag) is None:
            raise ValueError("component-upgrade metadata has an invalid new tag")
        if not isinstance(release_url, str) or not release_url.startswith("https://github.com/"):
            raise ValueError("component-upgrade metadata has an invalid Release URL")
        if row.get("formal_release") is not True:
            raise ValueError("component-upgrade metadata lacks a formal source Release")
        number = row.get("number")
        if not isinstance(number, int) or number <= 0:
            raise ValueError("component-upgrade metadata has an invalid pull request number")
        validated.append({**row, "component": canonical_component})
    return validated


def _render_template(version: str, components: dict[str, dict[str, Any]]) -> str:
    template_path = Path(__file__).resolve().parents[1] / "RELEASE_TEMPLATE.md"
    body = template_path.read_text(encoding="utf-8")
    tag = f"v{version}"
    replacements = {
        "> One-sentence release summary.": "> This release assembles independently versioned, formally released RDK Skills components.",
        "Describe the release scope, the user-facing outcome, and the component-tag policy in two or three sentences.": (
            "This Hub release brings together the pinned component Releases listed below. "
            "Component versions remain independent from the Hub version and are sourced only from published formal Releases."
        ),
        "- **BSP Skills**: Describe BSP changes, if any.": "- **BSP Skills**: Delivered from its pinned formal source Release.",
        "- **RDK Device Skills**: Describe board-side changes, if any.": "- **RDK Device Skills**: Delivered from its pinned formal source Release.",
        "- **OE Tool Chain (X5 / S)**: Describe workspace-pack changes, if any.": "- **OE Tool Chain (X5 / S)**: Delivered from their pinned formal source Releases.",
        "- **Hub experience**: Describe finder, installer, registry, plugin, or catalog changes, if any.": "- **Hub experience**: Mirrors, catalogs, and plugin artifacts reflect the pinned component Releases.",
        "- **Compatibility and licenses**: State migration, compatibility, or licensing information when relevant.": "- **Compatibility and licenses**: No compatibility or licensing changes are introduced by the release assembly.",
        "- List the release-contract and full-suite commands that passed.": "- Hub release contracts and the full Hub test suite passed before publication.",
        "- Record clean-clone or installation smoke-test results.": "- Clean-clone and installation smoke checks passed before publication.",
        "- Record the source component tags and Hub tag that were cross-checked.": "- Every source component tag was cross-checked against its published formal Release.",
        "Document upgrade behavior, migrations, deprecations, or known limitations. Omit this section only when there are no compatibility considerations.": (
            "Component versions are intentionally independent. A correction is published as a new immutable patch tag."
        ),
    }
    for source, display_name in COMPONENTS.items():
        body = body.replace(f"| {display_name} | `vX.Y.Z` |", f"| {display_name} | `{components[source]['ref']}` |")
    body = body.replace("vX.Y.Z", tag)
    for old, new in replacements.items():
        body = body.replace(old, new)
    return body


def render_notes(
    version: str,
    components: Iterable[dict[str, Any]],
    upgrades: Iterable[dict[str, Any]],
    additions: str = "",
) -> ReleaseNotes:
    """Render validated public notes without assuming a common component version."""
    if not isinstance(version, str) or VERSION.fullmatch(version) is None:
        raise ValueError("invalid Hub version; use MAJOR.MINOR.PATCH without v")
    _require_english(additions, "approved additions")
    component_rows = _validate_components(components)
    upgrade_rows = _validate_upgrades(upgrades)
    body = _render_template(version, component_rows).rstrip()
    if upgrade_rows:
        body += "\n\n## Component upgrades since the previous Hub release\n"
        for row in sorted(upgrade_rows, key=lambda item: (item.get("merged_at", ""), item["number"])):
            body += (
                f"\n- {row['component']}: `{row['from_tag']}` to `{row['to_tag']}` "
                f"([source Release]({row['release_url']}), PR #{row['number']})."
            )
    if additions.strip():
        body += f"\n\n## Maintainer-approved additions\n\n{additions.strip()}"
    if contains_cjk(body):
        raise ValueError("rendered notes must not contain CJK text")
    if MARKER.search(body):
        raise ValueError("rendered notes contain an unresolved marker")
    return ReleaseNotes(title=f"RDK Skills v{version}", body=body + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--components-json", type=Path, required=True)
    parser.add_argument("--upgrades-json", type=Path, required=True)
    parser.add_argument("--additions-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        components = json.loads(args.components_json.read_text(encoding="utf-8"))
        upgrades = json.loads(args.upgrades_json.read_text(encoding="utf-8"))
        additions = args.additions_file.read_text(encoding="utf-8") if args.additions_file else ""
        if not isinstance(components, list) or not isinstance(upgrades, list):
            raise ValueError("components and upgrades JSON must be arrays")
        notes = render_notes(args.version, components, upgrades, additions)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"release notes rejected: {error}") from error
    args.output.write_text(notes.body, encoding="utf-8")
    print(notes.title)


if __name__ == "__main__":
    main()
