# SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Regenerate README tables from parsed YAML and filesystem data."""

from __future__ import annotations

import argparse
import html
from pathlib import Path, PurePosixPath
import re
from urllib.parse import quote

import yaml


REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SKILLS_START = "<!-- skills-table-start -->"
SKILLS_END = "<!-- skills-table-end -->"
HELP_START = "<!-- help-table-start -->"
HELP_END = "<!-- help-table-end -->"


def _text(data: dict, field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"component {field} is required")
    return value


def _table_text(value: str) -> str:
    return (
        html.escape(value, quote=True)
        .replace("|", "&#124;")
        .replace("`", "&#96;")
        .replace("[", "&#91;")
        .replace("]", "&#93;")
        .replace("\r", "&#13;")
        .replace("\n", "&#10;")
    )


def _component_text(value: str) -> str:
    return (
        value.replace("|", "&#124;")
        .replace("`", "&#96;")
        .replace("\r", "&#13;")
        .replace("\n", "&#10;")
    )


def _safe_relative_url(value: str, field: str) -> str:
    parsed = PurePosixPath(value)
    if value.startswith("/") or "\\" in value or ".." in parsed.parts or str(parsed) in ("", "."):
        raise ValueError(f"component {field} is unsafe")
    return quote(str(parsed), safe="/-._~")


def _component_rows(root: Path) -> tuple[str, str]:
    components = []
    for path in sorted((root / "components.d").glob("*.yml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as error:
            raise ValueError(f"invalid component YAML: {path}") from error
        if not isinstance(data, dict):
            raise ValueError(f"component YAML must be a mapping: {path}")
        components.append(data)

    skills_rows = [
        "| Product | Description | Skills |",
        "|---------|-------------|--------|",
    ]
    help_rows = [
        "| Product | Issues | Discussions | Contributing |",
        "|---------|--------|-------------|--------------|",
    ]
    for data in sorted(components, key=lambda item: _text(item, "name").casefold()):
        name = _text(data, "name")
        description = _text(data, "description")
        repo = _text(data, "repo")
        if REPOSITORY.fullmatch(repo) is None:
            raise ValueError(f"unsafe component repository: {repo}")
        skills = data.get("skills")
        if not isinstance(skills, list) or not skills:
            raise ValueError("component skills must be a non-empty list")

        links = []
        for skill in skills:
            if not isinstance(skill, dict):
                raise ValueError("component skill entry must be a mapping")
            catalog_dir = skill.get("catalog_dir")
            if (
                not isinstance(catalog_dir, str)
                or not catalog_dir
                or "/" in catalog_dir
                or "\\" in catalog_dir
                or catalog_dir in (".", "..")
            ):
                raise ValueError(f"unsafe catalog directory: {catalog_dir}")
            catalog_root = root / "skills" / catalog_dir
            skill_files = []
            if (catalog_root / "SKILL.md").is_file():
                skill_files = [catalog_root / "SKILL.md"]
            elif catalog_root.is_dir():
                skill_files = sorted(
                    catalog_root.rglob("SKILL.md"), key=lambda path: path.as_posix()
                )
            for skill_file in skill_files:
                skill_dir = skill_file.parent.relative_to(root).as_posix()
                skill_name = skill_file.parent.name
                links.append(
                    f"[ `{_table_text(skill_name)}`]({quote(skill_dir, safe='/-._~')})"
                )

        if not links:
            continue
        skills_rows.append(
            f"| **{_component_text(name)}** | {_component_text(description)} | {', '.join(links)} |"
        )

        raw_links = data.get("links")
        if raw_links is None:
            raw_links = {}
        if not isinstance(raw_links, dict):
            raise ValueError("component links must be a mapping")
        contributing = raw_links.get("contributing", "CONTRIBUTING.md")
        discussions = raw_links.get("discussions", True)
        if contributing is None or contributing == "":
            contributing = "CONTRIBUTING.md"
        if discussions is None or discussions == "":
            discussions = True
        if contributing is not False and not isinstance(contributing, str):
            raise ValueError("component contributing link must be a path or false")
        if not isinstance(discussions, bool):
            raise ValueError("component discussions link must be boolean")

        contributing_link = "—"
        if contributing is not False:
            contributing_link = (
                f"[Contributing](https://github.com/{repo}/blob/main/"
                f"{_safe_relative_url(contributing, 'contributing link')})"
            )
        discussions_link = (
            f"[Discussions](https://github.com/{repo}/discussions)"
            if discussions
            else "—"
        )
        help_rows.append(
            f"| **{_component_text(name)}** | [Issues](https://github.com/{repo}/issues) | "
            f"{discussions_link} | {contributing_link} |"
        )

    return "\n".join(skills_rows) + "\n", "\n".join(help_rows) + "\n"


def _replace_section(content: str, start: str, end: str, rows: str) -> str:
    pattern = re.compile(rf"({re.escape(start)}\r?\n).*?({re.escape(end)})", re.DOTALL)
    updated, count = pattern.subn(lambda match: match.group(1) + rows + match.group(2), content)
    if count != 1:
        raise ValueError(f"README must contain exactly one {start}/{end} marker pair")
    return updated


def regenerate(root: Path) -> None:
    """Regenerate both README tables without constructing executable source."""
    root = root.resolve()
    readme_path = root / "README.md"
    content = readme_path.read_text(encoding="utf-8")
    skills_rows, help_rows = _component_rows(root)
    content = _replace_section(content, SKILLS_START, SKILLS_END, skills_rows)
    content = _replace_section(content, HELP_START, HELP_END, help_rows)
    temporary = readme_path.with_name(f".{readme_path.name}.tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(readme_path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        regenerate(args.root)
    except (OSError, ValueError) as error:
        raise SystemExit(f"README regeneration failed: {error}") from error
    print("README.md regenerated successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
