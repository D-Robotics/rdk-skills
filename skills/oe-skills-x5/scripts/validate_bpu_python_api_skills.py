#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Validate the X5 board-side hbm_runtime Python API Skill."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from search_local_docs import load_platform_index, resolve_doc_root, resolve_python_api_doc, score, terms

SKILL_SPECS = {
    "x5-bpu-python-api": {
        "version": "2.0.0",
        "module": "x5",
        "platform": "x5",
        "chip": "X5",
        "path": ".drobotics/skills/x5-bpu-python-api",
        "manual_platform": "x5",
        "reference_path": Path("skills/x5-bpu-python-api/references/x5_bpu_pyapi.md"),
        "route": "/local-python-api/x5-bpu",
        "query": "X5 hbm_runtime Python API",
        "minimum": "3.5.0",
        "model_suffix": ".bin",
        "required_headings": (
            "## 目标与边界",
            "## 输入合同",
            "## 前置检查",
            "## 执行步骤",
            "## 产物与完成标准",
            "## 风险与确认",
            "## 失败与交接",
            "## 按需参考",
        ),
        "required_terms": (
            "cat /etc/version",
            "3.5.0",
            "HB_HBMRuntime",
            "libdnn",
            "pip install hbm_runtime",
            "x5-runtime-deploy",
        ),
    },
}
FENCED_CODE_BLOCK = re.compile(r"(?ms)^(?:```|~~~)(?:bash|sh|shell|console)?\s*\n(.*?)^(?:```|~~~)")
BARE_X5_PIP_INSTALL = re.compile(
    r"(?m)^\s*(?:python(?:3)?\s+-m\s+)?pip(?:3)?\s+install\s+hbm_runtime\s*$"
)


def installed_root() -> Path:
    return Path(__file__).resolve().parents[1]


def assert_true(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def ranked_routes(entries: list[dict[str, Any]], query: str) -> list[str]:
    query_terms = terms(query)
    ranked = sorted(
        (
            (score(entry, query_terms), str(entry.get("routePath", "")))
            for entry in entries
            if score(entry, query_terms) > 0
        ),
        key=lambda item: (-item[0], item[1]),
    )
    return [route for _, route in ranked]


def check_index_and_skills(root: Path, index: dict[str, Any], failures: list[str]) -> None:
    for skill_id, spec in SKILL_SPECS.items():
        module_skills = index.get("modules", {}).get(spec["module"], {}).get("skills", [])
        assert_true(skill_id in module_skills, f"{skill_id} is absent from its module list", failures)

        expected_path = spec["path"]
        expected_file = f"{expected_path}/SKILL.md"
        skill_file = root / expected_file.removeprefix(".drobotics/")
        assert_true(skill_file.is_file(), f"Missing Skill file: {skill_id}", failures)
        reference_file = root / spec["reference_path"]
        assert_true(reference_file.is_file(), f"Missing packaged API reference: {reference_file}", failures)
        if not skill_file.is_file():
            continue

        skill_text = skill_file.read_text(encoding="utf-8")
        frontmatter = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", skill_text, re.S)
        assert_true(frontmatter is not None, f"Missing frontmatter: {skill_id}", failures)
        if frontmatter:
            assert_true(
                re.search(rf"^name: {re.escape(skill_id)}$", frontmatter.group(1), re.M) is not None,
                f"Wrong Skill name: {skill_id}",
                failures,
            )
            assert_true(
                re.search(r"^description: .+", frontmatter.group(1), re.M) is not None,
                f"Missing Skill description: {skill_id}",
                failures,
            )

        for heading in spec["required_headings"]:
            assert_true(heading in skill_text, f"{skill_id} missing required section: {heading}", failures)
        for term in spec["required_terms"]:
            assert_true(term in skill_text, f"{skill_id} missing required contract term: {term}", failures)
        assert_true(spec["model_suffix"] in skill_text, f"{skill_id} lacks model suffix boundary", failures)

        if skill_id == "x5-bpu-python-api":
            for code_block in FENCED_CODE_BLOCK.findall(skill_text):
                assert_true(
                    BARE_X5_PIP_INSTALL.search(code_block) is None,
                    "X5 Skill contains an executable bare pip install hbm_runtime command",
                    failures,
                )


def check_routing_and_packs(root: Path, failures: list[str]) -> None:
    router_path = root / "skills/x5-router/SKILL.md"
    assert_true(router_path.is_file(), f"Missing x5-router: {router_path}", failures)
    if router_path.is_file():
        router_text = router_path.read_text(encoding="utf-8")
        for term in (
            "x5-bpu-python-api",
            "HB_HBMRuntime",
        ):
            assert_true(term in router_text, f"x5-router missing Python API route or boundary: {term}", failures)

    x5_pack_path = root / "platforms/x5/PACK.md"
    assert_true(x5_pack_path.is_file(), f"Missing X5 Pack: {x5_pack_path}", failures)
    if x5_pack_path.is_file():
        pack_text = x5_pack_path.read_text(encoding="utf-8")
        assert_true("x5-bpu-python-api" in pack_text, "X5 Pack does not list x5-bpu-python-api", failures)
        assert_true("3.5.0" in pack_text, "X5 Pack lacks Python API version gate 3.5.0", failures)


def check_manuals_and_retrieval(
    x5_docs_root: Path,
    s_docs_root: Path | None,
    x5_manual: Path,
    s_manual: Path | None,
    failures: list[str],
) -> None:
    doc_roots = {"x5": x5_docs_root}
    manuals = {"x5": x5_manual}
    for skill_id, spec in SKILL_SPECS.items():
        platform = spec["manual_platform"]
        doc_root = doc_roots[platform]
        manual_path = manuals[platform]
        assert_true(doc_root.is_dir(), f"Missing {platform} docs root: {doc_root}", failures)
        assert_true(manual_path.is_file(), f"Missing {platform} Python API manual: {manual_path}", failures)
        if not doc_root.is_dir() or not manual_path.is_file():
            continue

        entries = load_platform_index(doc_root, "zh", manual_path)
        routes = ranked_routes(entries, spec["query"])
        assert_true(
            spec["route"] in routes[:12],
            f"Local {platform} retrieval did not surface {spec['route']} for '{spec['query']}'",
            failures,
        )


def run_version_gate(script_path: Path, platform: str, value: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temporary_directory:
        version_file = Path(temporary_directory) / "version"
        version_file.write_text(f"Version: {value}\n", encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script_path), "--platform", platform, "--version-file", str(version_file)],
            text=True,
            capture_output=True,
            check=False,
        )


def check_version_gate(root: Path, failures: list[str]) -> None:
    script_path = root / "scripts/check_bpu_python_api_version.py"
    assert_true(script_path.is_file(), f"Missing version gate: {script_path}", failures)
    if not script_path.is_file():
        return

    checks = (
        ("x5", "3.4.9", 1),
        ("x5", "3.5.0", 0),
        ("s", "4.0.4", 1),
        ("s", "4.0.5", 0),
    )
    for platform, value, expected_code in checks:
        result = run_version_gate(script_path, platform, value)
        assert_true(
            result.returncode == expected_code,
            f"Version gate {platform} {value} returned {result.returncode}; stderr={result.stderr.strip()}",
            failures,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate separated S/X5 hbm_runtime Python API Skills")
    parser.add_argument("--x5-docs-root", help="Override X5 documentation root")
    parser.add_argument("--s-docs-root", help="Override S-series documentation root")
    parser.add_argument("--x5-manual", help="Override X5 Python API Markdown")
    parser.add_argument("--s-manual", help="Override S-series Python API Markdown")
    args = parser.parse_args()

    root = installed_root()
    index_path = root / "skill-index.json"
    failures: list[str] = []
    assert_true(index_path.is_file(), f"Missing skill index: {index_path}", failures)
    if not index_path.is_file():
        print("\n".join(f"FAIL: {failure}" for failure in failures), file=sys.stderr)
        return 1

    index = json.loads(index_path.read_text(encoding="utf-8"))
    check_index_and_skills(root, index, failures)
    check_routing_and_packs(root, failures)
    check_version_gate(root, failures)

    try:
        x5_docs_root = resolve_doc_root(args.x5_docs_root)
        x5_manual = resolve_python_api_doc(args.x5_manual)
    except FileNotFoundError as error:
        failures.append(str(error))
    else:
        check_manuals_and_retrieval(x5_docs_root, None, x5_manual, None, failures)

    if failures:
        print("\n".join(f"FAIL: {failure}" for failure in failures), file=sys.stderr)
        return 1

    print("BPU_PYTHON_API_SKILL_VALIDATION_OK: X5 skill, version gate, routes, local manual, and retrieval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
