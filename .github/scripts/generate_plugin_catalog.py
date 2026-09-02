"""Generate deterministic plugin catalog data from the Hub registry."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
from typing import Literal

import yaml


class CatalogError(ValueError):
    """Raised when catalog data cannot be safely generated."""


REPOSITORY_SLUG = re.compile(
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/"
    r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9_-])?"
)
STABLE_TAG = re.compile(
    r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)


def require_repository_slug(value: object) -> str:
    if (
        not isinstance(value, str)
        or ".." in value
        or REPOSITORY_SLUG.fullmatch(value) is None
    ):
        raise CatalogError(f"repo must use exact owner/repo syntax: {value!r}")
    return value


def require_stable_tag(value: object) -> str:
    if not isinstance(value, str) or STABLE_TAG.fullmatch(value) is None:
        raise CatalogError(f"ref must be a canonical stable tag: {value!r}")
    return value


def require_safe_relative(value: str, field: str) -> str:
    path = PurePosixPath(value)
    is_windows_drive_path = len(value) >= 2 and value[0].isalpha() and value[1] == ":"
    if (
        not value
        or path.is_absolute()
        or is_windows_drive_path
        or ".." in path.parts
        or "\\" in value
    ):
        raise CatalogError(f"{field} must be a safe POSIX relative path: {value!r}")
    return value


def load_components(repo_root: Path) -> list[dict]:
    components: list[dict] = []
    for component_path in sorted((repo_root / "components.d").glob("*.yml")):
        with component_path.open(encoding="utf-8") as component_file:
            component = yaml.safe_load(component_file)
        if not isinstance(component, dict):
            raise CatalogError(f"component must be a mapping: {component_path}")
        component["ref"] = require_stable_tag(component.get("ref"))
        components.append(component)
    return components


def build_pack_registry(repo_root: Path, components: list[dict]) -> dict:
    del repo_root
    packs = []
    for component in components:
        if component.get("install_type") != "workspace":
            continue

        workspace_dir = component.get("workspace_dir")
        if not isinstance(workspace_dir, str):
            raise CatalogError("workspace_dir is required for workspace components")
        verify_paths = component.get("verify_paths")
        if not isinstance(verify_paths, list) or not verify_paths:
            raise CatalogError("verify_paths must be a non-empty list for workspace components")

        repo = require_repository_slug(component.get("repo"))
        ref = require_stable_tag(component.get("ref"))
        safe_workspace_dir = require_safe_relative(workspace_dir, "workspace_dir")
        safe_verify_paths = [require_safe_relative(path, "verify_paths") for path in verify_paths]

        # Workspace packs are mirrored into exactly one self-installable
        # catalog dir, so the registry must know where the Hub carries them.
        skills = component.get("skills")
        if not isinstance(skills, list) or len(skills) != 1:
            raise CatalogError(
                f"workspace component must declare exactly one skills entry: {component.get('name')!r}"
            )
        catalog_dir = skills[0].get("catalog_dir")
        if not isinstance(catalog_dir, str):
            raise CatalogError(f"catalog_dir is required for workspace component: {component.get('name')!r}")

        packs.append(
            {
                "name": component["name"],
                "repo": repo,
                "ref": ref,
                "install_type": "workspace",
                "install_script": component["install_script"],
                "catalog_dir": require_safe_relative(catalog_dir, "catalog_dir"),
                "workspace_dir": safe_workspace_dir,
                "verify_paths": safe_verify_paths,
            }
        )
    # Preserve the deterministic components.d order.  Repository/ref entries
    # are ordered data: keep duplicates and cardinality intact so the catalog
    # remains a faithful projection of the workspace registry.
    return {"schema_version": 1, "packs": packs}


def build_skill_index(repo_root: Path, components: list[dict], exceptions: list[dict]) -> dict:
    records = []
    seen_catalog_dirs = set()
    for component in components:
        install_type = component.get("install_type", "flat")
        skills = component.get("skills")
        if not isinstance(skills, list):
            raise CatalogError(f"skills must be a list for component: {component.get('name')!r}")
        for skill in skills:
            if not isinstance(skill, dict) or not isinstance(skill.get("catalog_dir"), str):
                raise CatalogError(f"catalog_dir is required for component: {component.get('name')!r}")
            catalog_dir = require_safe_relative(skill["catalog_dir"], "catalog_dir")
            if catalog_dir in seen_catalog_dirs:
                raise CatalogError(f"duplicate catalog path: skills/{catalog_dir}")
            seen_catalog_dirs.add(catalog_dir)

            catalog_root = repo_root / "skills" / catalog_dir
            skill_paths = (
                [catalog_root / "SKILL.md"]
                if install_type == "flat"
                else sorted(catalog_root.rglob("SKILL.md"), key=lambda path: path.as_posix())
            )
            for skill_path in skill_paths:
                records.append(
                    _skill_record(
                        repo_root,
                        skill_path,
                        component["name"],
                        install_type,
                        require_repository_slug(component.get("repo")),
                    )
                )

    for exception in exceptions:
        if not isinstance(exception, dict) or not isinstance(exception.get("dir"), str):
            raise CatalogError("exception dir is required")
        directory = require_safe_relative(exception["dir"], "exceptions.dir")
        records.append(
            _skill_record(
                repo_root,
                repo_root / "skills" / directory / "SKILL.md",
                exception.get("component", "D-Robotics Skills"),
                "flat",
                "D-Robotics/rdk-skills",
            )
        )

    seen_names = set()
    seen_paths = set()
    for record in records:
        name = record["name"]
        catalog_path = record["catalog_path"]
        if name in seen_names:
            raise CatalogError(f"duplicate skill name: {name}")
        if catalog_path in seen_paths:
            raise CatalogError(f"duplicate catalog path: {catalog_path}")
        seen_names.add(name)
        seen_paths.add(catalog_path)
    return {"schema_version": 1, "skills": sorted(records, key=lambda record: record["name"])}


def _skill_record(
    repo_root: Path,
    skill_path: Path,
    pack: str,
    install_type: str,
    repo: str,
) -> dict:
    relative_path = skill_path.relative_to(repo_root).as_posix()
    try:
        frontmatter = _read_frontmatter(skill_path)
    except (OSError, yaml.YAMLError, ValueError, TypeError) as error:
        raise CatalogError(f"invalid frontmatter: {relative_path}") from error
    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not name or not isinstance(description, str) or not description:
        raise CatalogError(f"invalid frontmatter: {relative_path}")
    return {
        "name": name,
        "description": description,
        "pack": pack,
        "catalog_path": skill_path.parent.relative_to(repo_root).as_posix(),
        "install_type": install_type,
        "repo": repo,
    }


def _read_frontmatter(skill_path: Path) -> dict:
    content = skill_path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError("frontmatter must start with a delimiter")
    closing_delimiter = content.find("\n---\n", 4)
    if closing_delimiter == -1:
        raise ValueError("frontmatter must end with a delimiter")
    frontmatter = yaml.safe_load(content[4:closing_delimiter])
    if not isinstance(frontmatter, dict):
        raise ValueError("frontmatter must be a mapping")
    return frontmatter


def render_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def validate_plugin_includes(repo_root: Path) -> None:
    for plugin_path in sorted((repo_root / "plugins.d").glob("*.yml")):
        if plugin_path.name.startswith("_"):
            continue
        try:
            with plugin_path.open(encoding="utf-8") as plugin_file:
                plugin = yaml.safe_load(plugin_file)
        except (OSError, yaml.YAMLError) as error:
            raise CatalogError(f"invalid plugin file: {plugin_path}") from error
        if not isinstance(plugin, dict):
            raise CatalogError(f"plugin must be a mapping: {plugin_path}")
        include_skills = plugin.get("include_skills", [])
        if not isinstance(include_skills, list):
            raise CatalogError(f"include_skills must be a list: {plugin_path}")
        for include_path in include_skills:
            if not isinstance(include_path, str) or not (repo_root / include_path).is_dir():
                raise CatalogError(f"missing include_skills path: {include_path}")


def generate(
    repo_root: Path, target: Literal["pack", "skills", "all"] = "all"
) -> list[Path]:
    if target not in {"pack", "skills", "all"}:
        raise CatalogError(f"unsupported target: {target}")
    components = load_components(repo_root)
    written = []
    if target in {"pack", "all"}:
        pack_path = repo_root / "skills/rdk-pack-installer/references/pack-registry.json"
        _write_json(pack_path, build_pack_registry(repo_root, components))
        written.append(pack_path)
    if target in {"skills", "all"}:
        exceptions = _load_exceptions(repo_root)
        skill_index_path = repo_root / "skills/rdk-skill-finder/references/skill-index.json"
        _write_json(skill_index_path, build_skill_index(repo_root, components, exceptions))
        written.append(skill_index_path)
    return written


def _load_exceptions(repo_root: Path) -> list[dict]:
    exceptions_path = repo_root / "catalog-exceptions.yml"
    try:
        with exceptions_path.open(encoding="utf-8") as exceptions_file:
            data = yaml.safe_load(exceptions_file)
    except (OSError, yaml.YAMLError) as error:
        raise CatalogError(f"invalid exceptions file: {exceptions_path}") from error
    if not isinstance(data, dict) or not isinstance(data.get("exceptions"), list):
        raise CatalogError(f"invalid exceptions file: {exceptions_path}")
    return data["exceptions"]


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output_file:
        output_file.write(render_json(data))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--target", choices=("pack", "skills", "all"), default="all")
    parser.add_argument("--check-plugin-includes", action="store_true")
    args = parser.parse_args()
    try:
        if args.check_plugin_includes:
            validate_plugin_includes(args.repo_root)
            return
        for path in generate(args.repo_root, args.target):
            print(path.relative_to(args.repo_root).as_posix())
    except CatalogError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
