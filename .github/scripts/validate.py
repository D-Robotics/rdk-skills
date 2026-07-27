#!/usr/bin/env python3
"""
D-Robotics Skills 格式校验脚本

校验单个 Skill 或整个 Pack 的 SKILL.md 格式是否符合规范。
CI 中在 PR 阶段调用，拦截格式不合规的 Skill。

用法：
    python validate.py skills/oe-skills/           # 校验整个 Pack
    python validate.py skills/oe-skills/hbdk/        # 校验某个模块
    python validate.py skills/oe-skills/hbdk/s-hbdk-compile/SKILL.md  # 校验单个
"""

import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = ["name", "description", "version"]
RECOMMENDED_FIELDS = ["platform", "kind", "riskLevel"]


def validate_skill_md(skill_md_path):
    """校验单个 SKILL.md，返回 (通过, 错误列表, 警告列表)。"""
    errors = []
    warnings = []

    content = Path(skill_md_path).read_text(encoding="utf-8")

    # frontmatter 存在性
    if not content.startswith("---"):
        return False, ["missing YAML frontmatter (must start with ---)"], []

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False, ["malformed frontmatter (need opening and closing ---)"], []

    # YAML 解析
    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"], []

    if not isinstance(frontmatter, dict):
        return False, ["frontmatter is not a dict"], []

    # 必填字段
    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            errors.append(f"missing required field: {field}")
        elif not frontmatter[field].strip():
            errors.append(f"empty required field: {field}")

    # name 格式
    name = frontmatter.get("name", "")
    if name and not name.replace("-", "").replace("_", "").isalnum():
        errors.append(f"name '{name}' should be lowercase with hyphens/underscores only")
    if name and name != name.lower():
        errors.append(f"name '{name}' should be lowercase")

    # description 不能太短
    desc = frontmatter.get("description", "")
    if desc and len(desc) < 20:
        warnings.append(f"description is very short ({len(desc)} chars), Agent may not match it well")

    # 推荐字段
    for field in RECOMMENDED_FIELDS:
        if field not in frontmatter:
            warnings.append(f"missing recommended field: {field}")

    # 正文不能为空
    body = parts[2].strip()
    if not body:
        warnings.append("SKILL.md body is empty")

    return len(errors) == 0, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate.py <path-to-skill-or-file>")
        sys.exit(1)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"Path not found: {target}")
        sys.exit(1)

    # 收集所有 SKILL.md
    if target.is_file() and target.name == "SKILL.md":
        skill_files = [target]
    elif target.is_dir():
        skill_files = sorted(target.rglob("SKILL.md"))
    else:
        print(f"Not a SKILL.md or directory: {target}")
        sys.exit(1)

    if not skill_files:
        print("No SKILL.md files found.")
        sys.exit(1)

    total = len(skill_files)
    passed = 0
    failed = 0
    warned = 0

    print(f"Validating {total} skill(s)...\n")

    for sf in skill_files:
        ok, errors, warnings = validate_skill_md(sf)
        rel = sf.relative_to(target.parent if target.is_dir() else target)
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {rel}")

        for e in errors:
            print(f"         ERROR: {e}")
        for w in warnings:
            print(f"         WARN:  {w}")

        if ok:
            passed += 1
            if warnings:
                warned += 1
        else:
            failed += 1

    print(f"\n{'='*40}")
    print(f"Total: {total}  Pass: {passed}  Fail: {failed}  Warn: {warned}")
    print(f"{'='*40}")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
