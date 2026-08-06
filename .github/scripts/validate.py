#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
"""
Validate skill structure for all skills in the catalog.

Checks per skill:
  - SKILL.md exists and has YAML frontmatter
  - frontmatter has required fields: name, description, version, license
  - name is lowercase-with-hyphens, <= 64 chars, matches directory name
  - description <= 1024 chars
  - SKILL.md body <= 500 lines
  - required sections present: Purpose, When to use, Instructions, Safety
  - skill-card.md exists
  - evals/ directory exists (with at least one task file)
  - every scripts/*.sh referenced in SKILL.md exists and passes bash -n
  - every references/*.md mentioned in SKILL.md exists

Usage:
    python3 .github/scripts/validate.py            # validate all skills
    python3 .github/scripts/validate.py --skill rdk-diagnostic  # single skill
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

REQUIRED_FRONTMATTER = ["name", "description", "version", "license"]
REQUIRED_SECTIONS = [
    "## Purpose",
    "## When to use",
    "## Instructions",
    "## Safety",
]
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
MAX_NAME_LEN = 64
MAX_DESC_LEN = 1024
MAX_BODY_LINES = 500


def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    fm_raw = parts[1].strip()
    body = parts[2]
    fm = {}
    for line in fm_raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip().strip('"').strip("'")
    return fm, body


def validate_skill(skill_dir):
    """Validate a single skill directory. Returns list of errors."""
    errors = []
    skill_name = skill_dir.name

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("missing SKILL.md")
        return errors

    content = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    if fm is None:
        errors.append("SKILL.md has no YAML frontmatter")
        return errors

    # 1. frontmatter completeness + name/dir match
    for field in REQUIRED_FRONTMATTER:
        if not fm.get(field):
            errors.append(f"frontmatter missing required field: {field}")
    name = fm.get("name", "")
    if not NAME_PATTERN.match(name):
        errors.append(f"name '{name}' must be lowercase-with-hyphens, <= {MAX_NAME_LEN} chars")
    if name != skill_name:
        errors.append(f"name '{name}' does not match directory '{skill_name}'")

    # 2. description length
    desc = fm.get("description", "")
    if len(desc) > MAX_DESC_LEN:
        errors.append(f"description exceeds {MAX_DESC_LEN} chars ({len(desc)})")

    # 3. body length
    body_lines = len([l for l in body.split("\n") if l.strip()])
    if body_lines > MAX_BODY_LINES:
        errors.append(f"SKILL.md body exceeds {MAX_BODY_LINES} lines ({body_lines})")

    # 4. required sections
    for sec in REQUIRED_SECTIONS:
        if sec + "\n" not in content and not re.search(
            r"^" + re.escape(sec) + r"\s*$", content, re.M
        ):
            errors.append(f"missing section '{sec}'")

    # 5. skill-card.md
    if not (skill_dir / "skill-card.md").exists():
        errors.append("missing skill-card.md")

    # 6. evals/
    evals_dir = skill_dir / "evals"
    if not evals_dir.exists():
        errors.append("missing evals/ directory")
    else:
        eval_files = (
            list(evals_dir.glob("*.json"))
            + list(evals_dir.glob("*.yaml"))
            + list(evals_dir.glob("*.yml"))
        )
        if not eval_files:
            errors.append("evals/ directory is empty (no .json/.yaml/.yml task files)")

    # 7. scripts referenced in SKILL.md exist + bash -n
    for ref in set(re.findall(r"scripts/([\w./-]+\.sh)", content)):
        p = skill_dir / "scripts" / ref
        if not p.exists():
            errors.append(f"SKILL.md references scripts/{ref} but file missing")
    scripts_dir = skill_dir / "scripts"
    if scripts_dir.is_dir():
        for f in scripts_dir.iterdir():
            if not f.name.endswith(".sh"):
                continue
            r = subprocess.run(["bash", "-n", str(f)], capture_output=True)
            if r.returncode != 0:
                errors.append(
                    f"bash -n failed for scripts/{f.name}: {r.stderr.decode().strip()}"
                )

    # 8. references mentioned in SKILL.md exist
    for ref in set(re.findall(r"references/([\w./-]+\.md)", content)):
        p = skill_dir / "references" / ref
        if not p.exists():
            errors.append(f"SKILL.md references references/{ref} but file missing")

    return errors


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate skill structure")
    parser.add_argument("--skill", help="validate a single skill by name")
    args = parser.parse_args()

    if args.skill:
        skill_dir = SKILLS_DIR / args.skill
        if not skill_dir.exists():
            print(f"Error: skill directory '{args.skill}' not found")
            sys.exit(1)
        skill_dirs = [skill_dir]
    else:
        skill_dirs = sorted(
            d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
        )

    if not skill_dirs:
        print("No skills found to validate.")
        return

    total_errors = 0
    for skill_dir in skill_dirs:
        errors = validate_skill(skill_dir)
        if errors:
            print(f"FAIL  {skill_dir.name}:")
            for e in errors:
                print(f"      - {e}")
            total_errors += len(errors)
        else:
            print(f"OK    {skill_dir.name}")

    print(f"\n{len(skill_dirs)} skills checked, {total_errors} error(s) found")
    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
