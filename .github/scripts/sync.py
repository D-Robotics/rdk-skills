#!/usr/bin/env python3
"""
D-Robotics Skills 中央目录同步脚本

从 components.d/*.yml 读取各 Pack 源头仓库列表，
clone 并提取 skills 目录，校验 SKILL.md 格式，
合并 skill-index.json，镜像到 skills/ 下。

用法：
    python sync.py                    # 同步全部 Pack
    python sync.py --pack oe-skills   # 只同步指定 Pack
    python sync.py --dry-run          # 只校验不写入

触发方式：
    - GitHub Actions 定时（每日）
    - Pack 仓库 push 触发（workflow_dispatch）
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMPONENTS_DIR = REPO_ROOT / "components.d"
SKILLS_DIR = REPO_ROOT / "skills"
INDEX_FILE = REPO_ROOT / "skill-index.json"
CLAUDE_PLUGIN_FILE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
AGENTS_PLUGIN_FILE = REPO_ROOT / ".agents" / "marketplace.json"
TEMP_DIR = REPO_ROOT / ".tmp-sync"

REQUIRED_FRONTMATTER = ["name", "description", "version"]


def load_components():
    """读取 components.d/ 下所有 YAML，返回 Pack 列表。"""
    packs = []
    for yml_file in sorted(COMPONENTS_DIR.glob("*.yml")):
        with open(yml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                packs.append(data)
    return packs


def clone_pack(pack, dry_run=False):
    """clone Pack 源头仓库到临时目录，返回 skills 目录路径。"""
    source = pack["source"]
    source_path = pack.get("sourcePath", "drobotics/skills/")
    pack_name = pack["name"]

    clone_dir = TEMP_DIR / pack_name
    if clone_dir.exists():
        shutil.rmtree(clone_dir)

    if dry_run:
        print(f"  [DRY-RUN] would clone {source}")
        return None

    print(f"  Cloning {source}...")
    subprocess.run(
        ["git", "clone", "--depth", "1", f"https://github.com/{source}.git", str(clone_dir)],
        check=True,
        capture_output=True,
    )

    skills_path = clone_dir / source_path.rstrip("/")
    if not skills_path.exists():
        print(f"  [WARN] {pack_name}: sourcePath '{source_path}' not found in repo")
        return None

    return skills_path


def validate_skill(skill_dir):
    """校验单个 Skill 的 SKILL.md 格式。"""
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    content = skill_md.read_text(encoding="utf-8")

    # 检查 frontmatter
    if not content.startswith("---"):
        return False, "missing YAML frontmatter"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False, "malformed frontmatter"

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return False, f"YAML parse error: {e}"

    for field in REQUIRED_FRONTMATTER:
        if field not in frontmatter:
            return False, f"missing required field: {field}"

    return True, frontmatter


def mirror_pack(pack, skills_path, dry_run=False):
    """将 Pack 的 skills 目录镜像到中央仓库的 skills/<pack-name>/ 下。"""
    pack_name = pack["name"]
    dest_dir = SKILLS_DIR / pack_name

    if dry_run:
        print(f"  [DRY-RUN] would mirror to {dest_dir}")
        return {}

    # 清理旧镜像
    if dest_dir.exists():
        shutil.rmtree(dest_dir)

    # 复制
    shutil.copytree(skills_path, dest_dir)

    # 收集 skill 路径
    paths = {}
    for skill_md_path in sorted(dest_dir.rglob("SKILL.md")):
        skill_dir = skill_md_path.parent
        rel_path = skill_dir.relative_to(dest_dir)
        content = skill_md_path.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        frontmatter = yaml.safe_load(parts[1]) if len(parts) >= 3 else {}

        skill_name = frontmatter.get("name", str(rel_path).replace("/", "-"))
        paths[skill_name] = {
            "version": frontmatter.get("version", "0.0.0"),
            "pack": pack_name,
            "path": f"skills/{pack_name}/{rel_path.as_posix()}",
            "skillFile": f"skills/{pack_name}/{rel_path.as_posix()}/SKILL.md",
            "description": frontmatter.get("description", ""),
            "platform": frontmatter.get("platform", "universal"),
        }

    return paths


def merge_index(all_paths, packs_info):
    """合并所有 Pack 的 skill 路径到中央 skill-index.json。"""
    index = {
        "skillsRoot": "skills",
        "packs": packs_info,
        "paths": {},
        "platforms": {},
        "_note": "本文件由 .github/scripts/sync.py 自动生成，请勿手动编辑。",
    }

    for pack_name, paths in all_paths.items():
        index["paths"].update(paths)

    # 按 name 排序
    index["paths"] = dict(sorted(index["paths"].items()))

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Merged index: {len(index['paths'])} skills from {len(packs_info)} packs")


def update_marketplace(packs_info):
    """更新 Claude Code 和 agents marketplace.json。"""
    plugins = []
    for pack_name, info in sorted(packs_info.items()):
        plugins.append({
            "name": pack_name,
            "source": f"./skills/{pack_name}",
            "description": info.get("title", pack_name),
        })

    for plugin_file in [CLAUDE_PLUGIN_FILE, AGENTS_PLUGIN_FILE]:
        plugin_file.parent.mkdir(parents=True, exist_ok=True)
        marketplace = {
            "name": "d-robotics-skills",
            "owner": {"name": "D-Robotics"},
            "plugins": plugins,
        }
        plugin_file.write_text(
            json.dumps(marketplace, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print(f"  Updated marketplace: {len(plugins)} plugins")


def main():
    target_pack = None
    dry_run = "--dry-run" in sys.argv

    if "--pack" in sys.argv:
        idx = sys.argv.index("--pack")
        target_pack = sys.argv[idx + 1]

    print("=" * 60)
    print("D-Robotics Skills Sync")
    print(f"  dry-run: {dry_run}")
    print(f"  target:  {target_pack or 'ALL'}")
    print("=" * 60)

    packs = load_components()
    if target_pack:
        packs = [p for p in packs if p["name"] == target_pack]

    if not packs:
        print("No packs found. Add YAML files to components.d/.")
        sys.exit(1)

    all_paths = {}
    packs_info = {}

    for pack in packs:
        pack_name = pack["name"]
        print(f"\n[{pack_name}]")

        # 记录 Pack 元数据
        packs_info[pack_name] = {
            "title": pack.get("title", pack_name),
            "source": pack["source"],
            "sourcePath": pack.get("sourcePath", "drobotics/skills/"),
            "platforms": pack.get("platforms", []),
            "skillCount": pack.get("skillCount", 0),
        }

        # clone
        skills_path = clone_pack(pack, dry_run)
        if skills_path is None:
            continue

        # 校验
        valid_count = 0
        for skill_dir in sorted(skills_path.rglob("SKILL.md")):
            ok, result = validate_skill(skill_dir.parent)
            if ok:
                valid_count += 1
            else:
                print(f"  [VALIDATION FAIL] {skill_dir.relative_to(skills_path)}: {result}")
        print(f"  Validated: {valid_count} skills")

        # 镜像
        paths = mirror_pack(pack, skills_path, dry_run)
        all_paths[pack_name] = paths

    # 合并索引
    if not dry_run:
        merge_index(all_paths, packs_info)
        update_marketplace(packs_info)

    # 清理临时目录
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

    print("\nDone.")


if __name__ == "__main__":
    main()
