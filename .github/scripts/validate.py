#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
"""
Validate skill structure for all skills in the catalog.

Checks are split into two compliance levels:

  L1 (entry gate):
    - SKILL.md exists and has YAML frontmatter
    - frontmatter required fields: name, description, version, license
    - name is lowercase-with-hyphens, <= 64 chars, matches directory name
    - description <= 1024 chars
    - SKILL.md body <= 500 lines

  L2 (governance):
    - required sections: ## Purpose / ## When to use / ## Instructions / ## Safety
    - skill-card.md exists
    - evals/ directory exists with at least one task file (.json/.yaml/.yml)
    - every scripts/*.sh referenced in SKILL.md exists and passes bash -n
    - every references/*.md mentioned in SKILL.md exists

Modes:
  advisory  (default): report L1 + L2 violations, always exit 0. Used by the
      sync pipeline during the observation period (report, don't block).
  enforcing: exit 1 when L1 violations exist. L2 violations are reported but
      do not fail the run unless --strict-l2 is also given.

Usage:
    python3 .github/scripts/validate.py                      # advisory, all skills
    python3 .github/scripts/validate.py --mode enforcing     # gate on L1
    python3 .github/scripts/validate.py --strict-l2          # gate on L1 + L2
    python3 .github/scripts/validate.py --skill rdk-diagnostic
"""

import re
import shutil
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
    """Parse YAML frontmatter from markdown content.

    Deliberately minimal (no PyYAML dependency): handles the flat
    `key: value` scalars the L1 gate depends on, plus folded/literal
    multi-line blocks (description: > / |) by joining continuation
    lines. Returns (frontmatter_dict, body) or (None, content).
    """
    if not content.startswith("---"):
        return None, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content
    fm_raw = parts[1]
    body = parts[2]

    fm = {}
    lines = fm_raw.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in stripped:
            i += 1
            continue
        key, _, val = stripped.partition(":")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if val in ("", ">", "|"):
            # folded/literal block: collect indented continuation lines
            block = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() and not nxt.startswith((" ", "\t")):
                    break
                block.append(nxt.strip())
                j += 1
            val = " ".join(block).strip('"').strip("'")
            i = j
        else:
            i += 1
        fm[key] = val
    return fm, body


def validate_skill(skill_dir):
    """Validate a single skill directory. Returns (l1_errors, l2_errors)."""
    l1, l2 = [], []
    skill_name = skill_dir.name

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"], []

    content = skill_md.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)

    if fm is None:
        return ["SKILL.md has no YAML frontmatter"], []

    # ---- L1: frontmatter completeness + naming + length ----
    for field in REQUIRED_FRONTMATTER:
        if not fm.get(field):
            l1.append(f"frontmatter missing required field: {field}")
    name = fm.get("name", "")
    if not NAME_PATTERN.match(name):
        l1.append(f"name '{name}' must be lowercase-with-hyphens, <= {MAX_NAME_LEN} chars")
    if name != skill_name:
        l1.append(f"name '{name}' does not match directory '{skill_name}'")

    desc = fm.get("description", "")
    if len(desc) > MAX_DESC_LEN:
        l1.append(f"description exceeds {MAX_DESC_LEN} chars ({len(desc)})")

    body_lines = len([l for l in body.split("\n") if l.strip()])
    if body_lines > MAX_BODY_LINES:
        l1.append(f"SKILL.md body exceeds {MAX_BODY_LINES} lines ({body_lines})")

    # ---- L2: sections, governance card, evals, scripts, references ----
    for sec in REQUIRED_SECTIONS:
        if sec + "\n" not in content and not re.search(
            r"^" + re.escape(sec) + r"\s*$", content, re.M
        ):
            l2.append(f"missing section '{sec}'")

    if not (skill_dir / "skill-card.md").exists():
        l2.append("missing skill-card.md")

    evals_dir = skill_dir / "evals"
    if not evals_dir.exists():
        l2.append("missing evals/ directory")
    else:
        eval_files = (
            list(evals_dir.glob("*.json"))
            + list(evals_dir.glob("*.yaml"))
            + list(evals_dir.glob("*.yml"))
        )
        if not eval_files:
            l2.append("evals/ directory is empty (no .json/.yaml/.yml task files)")

    for ref in set(re.findall(r"scripts/([\w./-]+\.sh)", content)):
        p = skill_dir / "scripts" / ref
        if not p.exists():
            l2.append(f"SKILL.md references scripts/{ref} but file missing")

    scripts_dir = skill_dir / "scripts"
    # bash -n runs only on POSIX (CI ubuntu). On Windows, shutil.which("bash")
    # may find WSL bash, which mangles Windows paths and produces false errors.
    if scripts_dir.is_dir() and sys.platform != "win32" and shutil.which("bash"):
        for f in scripts_dir.iterdir():
            if not f.name.endswith(".sh"):
                continue
            r = subprocess.run(["bash", "-n", str(f)], capture_output=True)
            if r.returncode != 0:
                l2.append(f"bash -n failed for scripts/{f.name}: {r.stderr.decode().strip()}")
    elif scripts_dir.is_dir():
        # e.g. local Windows runs without a usable bash — skip syntax check, not a violation
        pass

    for ref in set(re.findall(r"references/([\w./-]+\.md)", content)):
        p = skill_dir / "references" / ref
        if not p.exists():
            l2.append(f"SKILL.md references references/{ref} but file missing")

    return l1, l2


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate skill structure")
    parser.add_argument("--skill", help="validate a single skill by name")
    parser.add_argument(
        "--mode",
        choices=["advisory", "enforcing"],
        default="advisory",
        help="advisory: report only, exit 0 (default). enforcing: exit 1 on L1 violations.",
    )
    parser.add_argument(
        "--strict-l2",
        action="store_true",
        help="with --mode enforcing, also exit 1 on L2 violations",
    )
    args = parser.parse_args()

    if args.skill:
        skill_dir = SKILLS_DIR / args.skill
        if not skill_dir.exists():
            print(f"Error: skill directory '{args.skill}' not found")
            sys.exit(1)
        skill_dirs = [skill_dir]
    else:
        # Discover skills recursively: both flat layout (skills/<name>/SKILL.md)
        # and bulk layout (skills/<catalog_dir>/<module>/<skill>/SKILL.md).
        # Every directory that contains a SKILL.md is a skill unit.
        skill_dirs = sorted(
            p.parent for p in SKILLS_DIR.rglob("SKILL.md") if p.is_file()
        )

    if not skill_dirs:
        print("No skills found to validate.")
        return

    total_l1 = 0
    total_l2 = 0
    for skill_dir in skill_dirs:
        l1, l2 = validate_skill(skill_dir)
        if l1 or l2:
            print(f"FAIL  {skill_dir.name}:")
            for e in l1:
                print(f"      [L1] - {e}")
            for e in l2:
                print(f"      [L2] - {e}")
            total_l1 += len(l1)
            total_l2 += len(l2)
        else:
            print(f"OK    {skill_dir.name}")

    print(f"\n{len(skill_dirs)} skills checked: {total_l1} L1 error(s), {total_l2} L2 error(s)")

    if args.mode == "enforcing":
        if total_l1 > 0:
            print("L1 gate: FAILED (entry requirements not met)")
            sys.exit(1)
        if args.strict_l2 and total_l2 > 0:
            print("L2 gate: FAILED (governance requirements not met)")
            sys.exit(1)
        print(f"Mode: enforcing — gate passed")
    else:
        print("Mode: advisory — reporting only, no gate applied")
    sys.exit(0)


if __name__ == "__main__":
    main()
