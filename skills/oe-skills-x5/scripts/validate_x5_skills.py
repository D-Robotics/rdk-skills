#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Validate the X5 V2 Skill Pack, local manual coverage, and executable contracts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
from collections import deque
from pathlib import Path
from typing import Any

from search_local_docs import (
    load_platform_index,
    resolve_doc_root,
    resolve_python_api_doc,
    score,
    terms,
)


PACK_VERSION = "2.0.0"
EXPECTED_SKILLS = (
    "x5-router",
    "x5-environment-setup",
    "x5-environment-probe",
    "x5-environment-install",
    "x5-ptq-deploy",
    "x5-model-preflight",
    "x5-calibration-data-prepare",
    "x5-ptq-config-authoring",
    "x5-ptq-compile",
    "x5-qat-deploy",
    "x5-qat-adaptation",
    "x5-qat-training",
    "x5-qat-compile",
    "x5-runtime-deploy",
    "x5-runtime-cpp-infer",
    "x5-runtime-perf-eval",
    "x5-board-monitor",
    "x5-bpu-python-api",
    "x5-model-diagnostics",
    "x5-accuracy-diagnostics",
    "x5-consistency-diagnostics",
    "x5-performance-diagnostics",
)
COMMON_HEADINGS = (
    "## 目标与边界",
    "## 输入合同",
    "## 前置检查",
    "## 执行步骤",
    "## 产物与完成标准",
    "## 风险与确认",
    "## 失败与交接",
    "## 按需参考",
)
PACK_REQUIRED_HEADINGS = (
    "## 范围",
    "## 兼容性与资料",
    "## 输入资产与前置",
    "## 全局完成标准",
    "## 全局风险策略",
    "## 状态与恢复",
    "## Skill 架构",
    "## Pack 资产",
    "## 验收",
)
PACK_REQUIRED_TERMS = (
    "Pack 版本",
    PACK_VERSION,
    "bayes-e",
    "March.BAYES_E",
    "March.BAYES",
    "HAT",
    "X3",
    "input.json",
    "environment.json",
    "route.json",
    "plan.json",
    "run-state.json",
    "artifacts.json",
    "verification.json",
    "receipt.json",
    "同一策略最多尝试两次",
)
REQUIRED_SCHEMAS = (
    "artifacts.schema.json",
    "environment.schema.json",
    "plan.schema.json",
    "ptq-config.schema.json",
    "receipt.schema.json",
    "route.schema.json",
    "run-state.schema.json",
    "verification.schema.json",
)
REQUIRED_SCRIPTS = (
    "check_qat_target.py",
    "generate_ptq_config.py",
    "parse_somstatus.py",
    "probe_environment.py",
    "run_contract.py",
    "run_ptq.py",
    "validate_ptq_config.py",
)
REQUIRED_ASSETS = (
    "assets/ptq/onnx-single-input.yaml",
    "assets/ptq/caffe-single-input.yaml",
    "assets/runtime-cpp/CMakeLists.txt",
    "assets/runtime-cpp/main.cc",
    "assets/runtime-cpp/build.sh",
)
EXPECTED_RETRIEVAL = {
    "X5 hb_mapper makertbin": "/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_makertbin.html",
    "X5 hb_mapper checker": "/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_checker.html",
    "X5 March.BAYES_E": "/plugin/source/terminology/terminology.html",
    "X5 Runtime hbDNNInitializeFromFiles": "/runtime/source/",
    "X5 hrut_somstatus": "/runtime/source/tool_introduction/auxiliary_tool.html",
    "X5 HB_HBMRuntime Python API": "/local-python-api/x5-bpu",
}
MANUAL_FACTS = {
    "_sources/plugin/source/terminology/terminology.md.txt": ("March.BAYES_E", "March.BAYES"),
    "_sources/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_makertbin.rst.txt": ("bayes-e", "J5"),
    "_sources/runtime/source/runtime_dev.rst.txt": ("hbDNNInitializeFromFiles", "hbDNNInfer"),
    "_sources/runtime/source/tool_introduction/auxiliary_tool.rst.txt": ("hrut_somstatus",),
}
ISOLATION_CASES = {
    "reject-hat": "blocked_out_of_scope",
    "reject-j5-march": "reject_and_require_March.BAYES_E",
    "reject-s-series": "reject_platform_mixing",
    "reject-x3-reuse": "blocked_until_x3_pack_exists",
}
SOURCE_REFERENCE = re.compile(r"_sources/[A-Za-z0-9_./-]+\.(?:rst|md|ipynb)\.txt")
LOCAL_REFERENCE = re.compile(r"\.drobotics/[A-Za-z0-9_./-]+")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
FENCED_CODE_BLOCK = re.compile(r"(?ms)^(?:```|~~~)[^\r\n]*\r?\n(.*?)^(?:```|~~~)\s*$")
FORBIDDEN_S_EXECUTABLE = re.compile(
    r"\b(?:hb_compile|hbdk4|hbm_infer|hmct|libhbucp|nash-[A-Za-z0-9_-]+)\b",
    re.I,
)
FORBIDDEN_HAT_EXECUTABLE = re.compile(
    r"(?:\bimport\s+hat\b|\bfrom\s+hat(?:\.|\s)|tools[\\/]compile_perf\.py|\bhat\.)",
    re.I,
)
FORBIDDEN_J5_MARCH = re.compile(r"\bMarch\.BAYES\b")
FORBIDDEN_X3_MARCH = re.compile(r"\bMarch\.BERNOULLI2\b|\bmarch\s*[:=]\s*['\"]?bernoulli2\b", re.I)
MAINTAINER_PATH = re.compile(r"(?:D:\\20_Dev_Projects|C:\\Users\\chao04\.ma|/Users/chao04\.ma)", re.I)


def installed_root() -> Path:
    return Path(__file__).resolve().parents[1]


def assert_true(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def load_json(path: Path, failures: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"Unable to read JSON {path}: {error}")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"JSON root must be an object: {path}")
        return {}
    return payload


def load_yaml(path: Path, failures: list[str]) -> Any:
    try:
        import yaml
    except ImportError as error:
        failures.append(f"PyYAML is required to validate {path}: {error}")
        return None
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        failures.append(f"Unable to read YAML {path}: {error}")
        return None


def installed_path(root: Path, value: str) -> Path:
    return root / value.removeprefix(".drobotics/")


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


def check_pack_index(root: Path, failures: list[str]) -> dict[str, Any]:
    index_path = root / "platforms/x5/skill-index.json"
    assert_true(index_path.is_file(), f"Missing X5 V2 index: {index_path}", failures)
    if not index_path.is_file():
        return {}
    index = load_json(index_path, failures)
    pack = index.get("pack", {})
    assert_true(index.get("schema_version") == "2.0", "X5 index schema_version must be 2.0", failures)
    assert_true(pack.get("id") == "drobotics-x5", "X5 pack id must be drobotics-x5", failures)
    assert_true(pack.get("version") == PACK_VERSION, f"X5 pack version must be {PACK_VERSION}", failures)
    assert_true(pack.get("entry_skill") == "x5-router", "X5 entry Skill must be x5-router", failures)
    assert_true(pack.get("platform") == "X5", "X5 pack platform must be X5", failures)
    excluded = set(pack.get("excluded_capabilities", []))
    for boundary in ("HAT", "X3", "S-series workflows"):
        assert_true(boundary in excluded, f"X5 pack does not exclude {boundary}", failures)

    skills = index.get("skills")
    assert_true(isinstance(skills, list), "X5 index skills must be an array", failures)
    if not isinstance(skills, list):
        return index
    actual_ids = [item.get("id") for item in skills if isinstance(item, dict)]
    assert_true(actual_ids == list(EXPECTED_SKILLS), "X5 V2 index Skill list is incomplete or out of order", failures)
    registered = set(actual_ids)
    graph: dict[str, list[str]] = {}
    valid_kinds = {"router", "workflow", "environment", "diagnose"}
    valid_risks = {"low", "medium", "high", "critical"}
    required_fields = {
        "id",
        "kind",
        "entry",
        "intents",
        "accepts",
        "produces",
        "risk",
        "requires",
        "handoffs",
        "resources",
        "eval_tags",
    }
    for item in skills:
        if not isinstance(item, dict):
            failures.append("X5 index contains a non-object Skill entry")
            continue
        skill_id = str(item.get("id", ""))
        missing_fields = sorted(required_fields - set(item))
        assert_true(not missing_fields, f"{skill_id} index entry lacks fields: {', '.join(missing_fields)}", failures)
        expected_entry = f".drobotics/skills/{skill_id}/SKILL.md"
        assert_true(item.get("entry") == expected_entry, f"Wrong V2 entry path: {skill_id}", failures)
        assert_true(installed_path(root, expected_entry).is_file(), f"Missing Skill file: {skill_id}", failures)
        assert_true(item.get("kind") in valid_kinds, f"Invalid Skill kind: {skill_id}", failures)
        assert_true(item.get("risk") in valid_risks, f"Invalid risk level: {skill_id}", failures)
        for field in ("intents", "accepts", "produces", "eval_tags"):
            values = item.get(field)
            assert_true(
                isinstance(values, list) and bool(values) and all(isinstance(value, str) and value for value in values),
                f"{skill_id}.{field} must be a non-empty string array",
                failures,
            )
        handoffs = item.get("handoffs")
        assert_true(isinstance(handoffs, list), f"{skill_id}.handoffs must be an array", failures)
        graph[skill_id] = [value for value in handoffs or [] if isinstance(value, str)]
        for handoff in graph[skill_id]:
            assert_true(handoff in registered, f"{skill_id} hands off to unregistered Skill: {handoff}", failures)
            assert_true(handoff != skill_id, f"{skill_id} cannot hand off to itself", failures)
        resources = item.get("resources")
        assert_true(isinstance(resources, dict), f"{skill_id}.resources must be an object", failures)
        if isinstance(resources, dict):
            for category in ("references", "scripts"):
                values = resources.get(category)
                assert_true(isinstance(values, list), f"{skill_id}.resources.{category} must be an array", failures)
                for value in values or []:
                    if not isinstance(value, str):
                        failures.append(f"{skill_id} has a non-string {category} resource")
                        continue
                    if not value.startswith("_sources/"):
                        assert_true((root / value).is_file(), f"Missing resource for {skill_id}: {value}", failures)

    queue: deque[str] = deque([str(pack.get("entry_skill", ""))])
    reachable: set[str] = set()
    while queue:
        current = queue.popleft()
        if current in reachable or current not in graph:
            continue
        reachable.add(current)
        queue.extend(graph[current])
    unreachable = sorted(registered - reachable)
    assert_true(not unreachable, f"Skills unreachable from x5-router: {', '.join(unreachable)}", failures)
    router_handoffs = set(graph.get("x5-router", []))
    for workflow in (
        "x5-environment-setup",
        "x5-ptq-deploy",
        "x5-qat-deploy",
        "x5-runtime-deploy",
        "x5-bpu-python-api",
        "x5-model-diagnostics",
    ):
        assert_true(workflow in router_handoffs, f"x5-router does not expose main Workflow: {workflow}", failures)
    return index


def check_global_index(root: Path, pack_index: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    index_path = root / "skill-index.json"
    assert_true(index_path.is_file(), f"Missing global Skill index: {index_path}", failures)
    if not index_path.is_file():
        return {}
    index = load_json(index_path, failures)
    module_skills = index.get("modules", {}).get("x5", {}).get("skills")
    assert_true(module_skills == list(EXPECTED_SKILLS), "Global X5 module list does not match the V2 Pack", failures)
    return index


def parse_frontmatter(skill_id: str, text: str, failures: list[str]) -> dict[str, Any]:
    match = FRONTMATTER.match(text)
    assert_true(match is not None, f"Missing YAML frontmatter: {skill_id}", failures)
    if match is None:
        return {}
    try:
        import yaml
    except ImportError as error:
        failures.append(f"PyYAML is required for {skill_id}: {error}")
        return {}
    try:
        payload = yaml.safe_load(match.group(1))
    except yaml.YAMLError as error:
        failures.append(f"Invalid frontmatter for {skill_id}: {error}")
        return {}
    if not isinstance(payload, dict):
        failures.append(f"Frontmatter must be an object: {skill_id}")
        return {}
    assert_true(set(payload) == {"name", "description"}, f"{skill_id} frontmatter must contain only name and description", failures)
    assert_true(payload.get("name") == skill_id, f"Wrong frontmatter name: {skill_id}", failures)
    description = payload.get("description")
    assert_true(isinstance(description, str) and len(description.strip()) >= 30, f"Description is too weak: {skill_id}", failures)
    assert_true(isinstance(description, str) and "X5" in description, f"Description lacks X5 scope: {skill_id}", failures)
    return payload


def section_text(text: str, heading: str) -> str:
    match = re.search(rf"(?ms)^{re.escape(heading)}\r?\n(.*?)(?=^## |\Z)", text)
    return match.group(1).strip() if match else ""


def check_skill_contracts(
    root: Path,
    pack_index: dict[str, Any],
    global_index: dict[str, Any],
    failures: list[str],
) -> tuple[dict[str, str], set[str]]:
    skill_root = root / "skills"
    actual_ids = sorted(path.parent.name for path in skill_root.glob("*/SKILL.md"))
    assert_true(actual_ids == sorted(EXPECTED_SKILLS), "X5 Skill directories do not match the V2 index", failures)
    pack_items = {item.get("id"): item for item in pack_index.get("skills", []) if isinstance(item, dict)}
    global_paths = global_index.get("paths", {})
    skill_texts: dict[str, str] = {}
    manual_references: set[str] = set()

    for skill_id in EXPECTED_SKILLS:
        item = pack_items.get(skill_id, {})
        skill_file = installed_path(root, str(item.get("entry", "")))
        if not skill_file.is_file():
            continue
        text = skill_file.read_text(encoding="utf-8")
        skill_texts[skill_id] = text
        metadata = parse_frontmatter(skill_id, text, failures)
        description = metadata.get("description")
        assert_true(
            description == global_paths.get(skill_id, {}).get("description"),
            f"Global description does not match SKILL.md: {skill_id}",
            failures,
        )
        positions = [text.find(heading) for heading in COMMON_HEADINGS]
        assert_true(all(position >= 0 for position in positions), f"{skill_id} lacks one or more standard V2 sections", failures)
        assert_true(positions == sorted(positions), f"{skill_id} standard sections are out of order", failures)
        for heading in COMMON_HEADINGS:
            body = section_text(text, heading)
            assert_true(len(body) >= 12, f"{skill_id} has an empty or trivial section: {heading}", failures)

        for value in SOURCE_REFERENCE.findall(text):
            manual_references.add(value)
        for value in LOCAL_REFERENCE.findall(text):
            candidate = installed_path(root, value.rstrip(".,;:)]}"))
            assert_true(candidate.exists(), f"{skill_id} references a missing Pack path: {value}", failures)
        assert_true(MAINTAINER_PATH.search(text) is None, f"{skill_id} contains a maintainer absolute path", failures)

        for code_block in FENCED_CODE_BLOCK.findall(text):
            for pattern, label in (
                (FORBIDDEN_S_EXECUTABLE, "S-series executable"),
                (FORBIDDEN_HAT_EXECUTABLE, "HAT executable"),
                (FORBIDDEN_J5_MARCH, "J5 March.BAYES"),
                (FORBIDDEN_X3_MARCH, "X3/J3 march"),
            ):
                match = pattern.search(code_block)
                assert_true(match is None, f"{skill_id} code block contains {label}: {match.group(0) if match else ''}", failures)
            if skill_id.startswith("x5-qat-"):
                assert_true(
                    re.search(r"\bhb_mapper\s+makertbin\b", code_block, re.I) is None,
                    f"{skill_id} delegates QAT to hb_mapper makertbin",
                    failures,
                )
                assert_true(
                    re.search(r"(?:compile_model|export_hbir).*?[\"'][^\"']+\.bin[\"']", code_block, re.I | re.S) is None,
                    f"{skill_id} disguises a Plugin output as .bin",
                    failures,
                )

    router_text = skill_texts.get("x5-router", "")
    for term in (
        "x5-environment-setup",
        "x5-ptq-deploy",
        "x5-qat-deploy",
        "x5-runtime-deploy",
        "x5-bpu-python-api",
        "x5-model-diagnostics",
        "HAT",
        "X3",
        "March.BAYES",
        "route.json",
    ):
        assert_true(term in router_text, f"x5-router lacks route or isolation term: {term}", failures)
    return skill_texts, manual_references


def check_pack_documents(root: Path, failures: list[str]) -> set[str]:
    pack_root = root / "platforms/x5"
    pack_path = pack_root / "PACK.md"
    assert_true(pack_path.is_file(), f"Missing X5 PACK.md: {pack_path}", failures)
    manual_references: set[str] = set()
    documents = (
        pack_path,
        pack_root / "policies/compatibility.md",
        pack_root / "policies/risk-policy.md",
        pack_root / "references/run-contract.md",
        pack_root / "references/manual-map.md",
        pack_root / "CHANGELOG.md",
        root / "skills/README.md",
    )
    for path in documents:
        assert_true(path.is_file(), f"Missing X5 Pack document: {path}", failures)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        manual_references.update(SOURCE_REFERENCE.findall(text))
        assert_true(MAINTAINER_PATH.search(text) is None, f"Maintainer absolute path found in {path}", failures)

    if pack_path.is_file():
        pack_text = pack_path.read_text(encoding="utf-8")
        for heading in PACK_REQUIRED_HEADINGS:
            assert_true(heading in pack_text, f"X5 PACK.md lacks section: {heading}", failures)
        for term in PACK_REQUIRED_TERMS:
            assert_true(term in pack_text, f"X5 PACK.md lacks contract term: {term}", failures)
        for skill_id in EXPECTED_SKILLS:
            assert_true(skill_id in pack_text, f"X5 PACK.md does not list {skill_id}", failures)

    compatibility_path = pack_root / "policies/compatibility.md"
    if compatibility_path.is_file():
        compatibility = compatibility_path.read_text(encoding="utf-8")
        for term in (
            "hb_mapper checker",
            "hb_mapper makertbin",
            "march: bayes-e",
            "March.BAYES_E",
            "March.BAYES",
            ".hbm/.hbir",
            "HAT",
        ):
            assert_true(term in compatibility, f"compatibility.md lacks boundary: {term}", failures)

    run_contract_path = pack_root / "references/run-contract.md"
    if run_contract_path.is_file():
        contract = run_contract_path.read_text(encoding="utf-8")
        for name in (
            "input.json",
            "environment.json",
            "route.json",
            "plan.json",
            "run-state.json",
            "events.ndjson",
            "artifacts.json",
            "verification.json",
            "receipt.json",
        ):
            assert_true(name in contract, f"run-contract.md lacks {name}", failures)

    readme_path = root / "skills/README.md"
    if readme_path.is_file():
        readme = readme_path.read_text(encoding="utf-8")
        assert_true("S 系列的实战深度 + V2 的模块化、脚本化和机器可验证合同" in readme, "X5 README lacks the target standard", failures)
        for skill_id in EXPECTED_SKILLS:
            assert_true(skill_id in readme, f"X5 README does not list {skill_id}", failures)
    return manual_references


def check_router(root: Path, failures: list[str]) -> None:
    router_path = root / "skills/x5-router/SKILL.md"
    assert_true(router_path.is_file(), f"Missing x5-router: {router_path}", failures)
    if not router_path.is_file():
        return
    text = router_path.read_text(encoding="utf-8")
    for term in (
        "x5-router",
        "bayes-e",
        "March.BAYES_E",
        "HAT",
        "X3",
    ):
        assert_true(term in text, f"x5-router lacks boundary term: {term}", failures)


def check_eval_matrix(root: Path, failures: list[str]) -> None:
    path = root / "platforms/x5/evals/cases.yaml"
    assert_true(path.is_file(), f"Missing X5 Eval matrix: {path}", failures)
    if not path.is_file():
        return
    payload = load_yaml(path, failures)
    if not isinstance(payload, dict):
        return
    assert_true(payload.get("pack") == "x5", "Eval matrix uses the wrong Pack id", failures)
    required_categories = payload.get("required_categories")
    assert_true(
        required_categories == ["routing", "happy_path", "preflight_failure", "risk_confirmation"],
        "Eval required_categories are incomplete or out of order",
        failures,
    )
    category_contract = payload.get("category_contract", {})
    for category in required_categories or []:
        assert_true(bool(category_contract.get(category)), f"Eval category lacks a contract: {category}", failures)
    matrix = payload.get("skill_matrix")
    assert_true(isinstance(matrix, list), "Eval skill_matrix must be an array", failures)
    if isinstance(matrix, list):
        matrix_ids = [row.get("skill") for row in matrix if isinstance(row, dict)]
        assert_true(matrix_ids == list(EXPECTED_SKILLS), "Eval matrix does not cover all 22 Skills in index order", failures)
        for row in matrix:
            if not isinstance(row, dict):
                failures.append("Eval matrix contains a non-object row")
                continue
            skill_id = row.get("skill")
            for category in required_categories or []:
                assert_true(isinstance(row.get(category), str) and bool(row[category].strip()), f"{skill_id} lacks Eval case: {category}", failures)
    isolation = payload.get("isolation_cases")
    assert_true(isinstance(isolation, list), "Eval isolation_cases must be an array", failures)
    if isinstance(isolation, list):
        actual = {row.get("id"): row.get("expect") for row in isolation if isinstance(row, dict)}
        assert_true(actual == ISOLATION_CASES, "Eval isolation cases do not enforce HAT/J5/S/X3 boundaries", failures)


def check_schemas_and_assets(root: Path, failures: list[str]) -> None:
    pack_root = root / "platforms/x5"
    schema_root = pack_root / "schemas"
    try:
        import jsonschema
    except ImportError as error:
        failures.append(f"jsonschema is required for X5 validation: {error}")
        return

    schemas: dict[str, dict[str, Any]] = {}
    schema_ids: set[str] = set()
    for name in REQUIRED_SCHEMAS:
        path = schema_root / name
        assert_true(path.is_file(), f"Missing X5 schema: {name}", failures)
        if not path.is_file():
            continue
        schema = load_json(path, failures)
        schemas[name] = schema
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
        except jsonschema.SchemaError as error:
            failures.append(f"Invalid JSON Schema {name}: {error.message}")
        schema_id = schema.get("$id")
        assert_true(isinstance(schema_id, str) and bool(schema_id), f"Schema lacks $id: {name}", failures)
        assert_true(schema_id not in schema_ids, f"Duplicate schema $id: {schema_id}", failures)
        if isinstance(schema_id, str):
            schema_ids.add(schema_id)

    for name in REQUIRED_SCRIPTS:
        assert_true((pack_root / "scripts" / name).is_file(), f"Missing X5 executable script: {name}", failures)
    for relative in REQUIRED_ASSETS:
        assert_true((pack_root / relative).is_file(), f"Missing X5 Pack asset: {relative}", failures)

    ptq_schema = schemas.get("ptq-config.schema.json")
    if ptq_schema:
        validator = jsonschema.Draft202012Validator(ptq_schema)
        for relative in ("assets/ptq/onnx-single-input.yaml", "assets/ptq/caffe-single-input.yaml"):
            payload = load_yaml(pack_root / relative, failures)
            if payload is None:
                continue
            issues = sorted(validator.iter_errors(payload), key=lambda issue: list(issue.absolute_path))
            assert_true(not issues, f"{relative} violates ptq-config.schema.json: {issues[0].message if issues else ''}", failures)
            assert_true(payload.get("model_parameters", {}).get("march") == "bayes-e", f"{relative} does not target bayes-e", failures)

    main_path = pack_root / "assets/runtime-cpp/main.cc"
    if main_path.is_file():
        main_text = main_path.read_text(encoding="utf-8")
        for api in (
            "hbDNNInitializeFromFiles",
            "hbDNNGetModelNameList",
            "hbDNNGetModelHandle",
            "hbDNNGetInputTensorProperties",
            "hbDNNInfer",
            "hbDNNWaitTaskDone",
            "hbSysFlushMem",
            "hbDNNRelease",
        ):
            assert_true(api in main_text, f"Runtime C++ asset lacks API: {api}", failures)
    build_path = pack_root / "assets/runtime-cpp/build.sh"
    if build_path.is_file():
        build_text = build_path.read_text(encoding="utf-8")
        for term in ("LINARO_GCC_ROOT", "X5_DNN_ROOT", "aarch64-none-linux-gnu-g++", "set -euo pipefail"):
            assert_true(term in build_text, f"Runtime build asset lacks guard: {term}", failures)


def check_manual(
    root: Path,
    docs_root: Path,
    pack_index: dict[str, Any],
    referenced_sources: set[str],
    failures: list[str],
) -> None:
    assert_true(docs_root.is_dir(), f"Missing X5 local manual root: {docs_root}", failures)
    if not docs_root.is_dir():
        return
    for item in pack_index.get("skills", []):
        if not isinstance(item, dict):
            continue
        for value in item.get("resources", {}).get("references", []):
            if isinstance(value, str) and value.startswith("_sources/"):
                referenced_sources.add(value)
    assert_true(bool(referenced_sources), "X5 Pack does not cite any local manual sources", failures)
    for relative in sorted(referenced_sources):
        assert_true(not relative.lower().startswith("_sources/hat/"), f"HAT source leaked into X5 references: {relative}", failures)
        assert_true((docs_root / relative).is_file(), f"Missing X5 manual source: {relative}", failures)

    for relative, required_terms in MANUAL_FACTS.items():
        path = docs_root / relative
        assert_true(path.is_file(), f"Missing authoritative X5 source: {relative}", failures)
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            for term in required_terms:
                assert_true(term in text, f"Manual fact '{term}' missing from {relative}", failures)

    try:
        python_api_doc = resolve_python_api_doc(None)
        entries = load_platform_index(docs_root, "zh", python_api_doc)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        failures.append(f"Unable to load X5 local retrieval index: {error}")
        return
    hat_routes = [str(entry.get("routePath", "")) for entry in entries if str(entry.get("routePath", "")).lower().startswith("/hat/")]
    assert_true(not hat_routes, f"X5 retrieval still exposes HAT routes: {', '.join(hat_routes[:5])}", failures)
    for query, expected_route in EXPECTED_RETRIEVAL.items():
        routes = ranked_routes(entries, query)
        assert_true(
            any(expected_route in route for route in routes[:12]),
            f"Local X5 retrieval did not surface {expected_route} for '{query}'",
            failures,
        )


def invoke(
    command: list[str],
    label: str,
    failures: list[str],
    *,
    expected: tuple[int, ...] = (0,),
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = 45,
) -> subprocess.CompletedProcess[str] | None:
    process_env = os.environ.copy()
    process_env["PYTHONUTF8"] = "1"
    if env:
        process_env.update(env)
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=process_env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        failures.append(f"{label} could not run: {error}")
        return None
    if completed.returncode not in expected:
        output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
        failures.append(f"{label} returned {completed.returncode}, expected {expected}: {output[-2000:]}")
    return completed


def write_fake_tool(wrapper_dir: Path, name: str, python_script: Path) -> None:
    if os.name == "nt":
        wrapper = wrapper_dir / f"{name}.cmd"
        wrapper.write_text(
            f'@echo off\r\n"{sys.executable}" "%~dp0{python_script.name}" %*\r\n',
            encoding="utf-8",
        )
    else:
        wrapper = wrapper_dir / name
        wrapper.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "$(dirname "$0")/{python_script.name}" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)


def create_fake_toolchain(root: Path) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    mapper_script = root / "fake_hb_mapper.py"
    mapper_script.write_text(
        textwrap.dedent(
            """
            import sys
            from pathlib import Path
            import yaml

            args = sys.argv[1:]
            if not args:
                raise SystemExit(2)
            if args[0] == "checker":
                output = Path(args[args.index("--output") + 1])
                output.mkdir(parents=True, exist_ok=True)
                (output / "checker.ok").write_text("bayes-e checker passed\\n", encoding="utf-8")
                print("checker passed for bayes-e")
                raise SystemExit(0)
            if args[0] == "makertbin":
                config_path = Path(args[args.index("--config") + 1]).resolve()
                config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                model = config["model_parameters"]
                working_dir = Path(model["working_dir"]).expanduser()
                if not working_dir.is_absolute():
                    working_dir = (config_path.parent / working_dir).resolve()
                working_dir.mkdir(parents=True, exist_ok=True)
                prefix = model["output_model_file_prefix"]
                (working_dir / f"{prefix}.bin").write_bytes(b"fake-x5-bin")
                (working_dir / f"{prefix}_quantized_model.onnx").write_bytes(b"fake-quantized-onnx")
                print("makertbin passed for bayes-e")
                raise SystemExit(0)
            raise SystemExit(2)
            """
        ).lstrip(),
        encoding="utf-8",
    )
    model_info_script = root / "fake_hb_model_info.py"
    model_info_script.write_text('print("BPU march: bayes-e")\n', encoding="utf-8")
    write_fake_tool(root, "hb_mapper", mapper_script)
    write_fake_tool(root, "hb_model_info", model_info_script)
    path_value = str(root) + os.pathsep + os.environ.get("PATH", "")
    return {"PATH": path_value, "PATHEXT": os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD") + ";.CMD"}


def check_script_smoke(root: Path, docs_root: Path, failures: list[str]) -> None:
    scripts = root / "platforms/x5/scripts"
    with tempfile.TemporaryDirectory(prefix="x5-pack-validation-") as temporary:
        work = Path(temporary)
        model = work / "model.onnx"
        model.write_bytes(b"fake-onnx")
        calibration = work / "calibration"
        calibration.mkdir()
        (calibration / "sample.bin").write_bytes(b"sample")
        config = work / "x5.yaml"
        output_dir = work / "ptq-output"
        generate = invoke(
            [
                sys.executable,
                str(scripts / "generate_ptq_config.py"),
                "--model",
                str(model),
                "--output",
                str(config),
                "--working-dir",
                str(output_dir),
                "--input-name",
                "images",
                "--input-shape",
                "1x3x224x224",
                "--input-type-train",
                "rgb",
                "--input-layout-train",
                "NCHW",
                "--input-type-rt",
                "nv12",
                "--cal-data-dir",
                str(calibration),
                "--input-source",
                "images=pyramid",
                "--check-paths",
            ],
            "PTQ config generation smoke",
            failures,
            cwd=root.parent,
        )
        if generate is None or generate.returncode != 0:
            return
        validate = invoke(
            [sys.executable, str(scripts / "validate_ptq_config.py"), str(config), "--check-paths"],
            "PTQ config validation smoke",
            failures,
            cwd=root.parent,
        )
        if validate is None or validate.returncode != 0:
            return

        invalid_config = work / "invalid-x5.yaml"
        invalid_payload = load_yaml(config, failures)
        if isinstance(invalid_payload, dict):
            import yaml

            invalid_payload["model_parameters"]["march"] = "bayes"
            invalid_config.write_text(yaml.safe_dump(invalid_payload, sort_keys=False), encoding="utf-8")
            invoke(
                [sys.executable, str(scripts / "validate_ptq_config.py"), str(invalid_config)],
                "PTQ wrong-march rejection smoke",
                failures,
                expected=(2,),
                cwd=root.parent,
            )

        fake_env = create_fake_toolchain(work / "fake-bin")
        ptq_report = work / "ptq-report.json"
        full = invoke(
            [
                sys.executable,
                str(scripts / "run_ptq.py"),
                "full",
                "--config",
                str(config),
                "--report",
                str(ptq_report),
            ],
            "guarded PTQ orchestration smoke",
            failures,
            cwd=root.parent,
            env=fake_env,
        )
        if full is None or full.returncode != 0:
            return
        ptq_payload = load_json(ptq_report, failures)
        assert_true(ptq_payload.get("passed") is True, "run_ptq.py smoke did not pass", failures)
        bins = list(output_dir.glob("*.bin"))
        assert_true(len(bins) == 1, "run_ptq.py smoke did not create exactly one .bin", failures)

        valid_qat = work / "valid_qat.py"
        valid_qat.write_text(
            textwrap.dedent(
                """
                from horizon_plugin_pytorch import March, quantization

                def compile_for_x5(model):
                    quantization.set_march(March.BAYES_E)
                    prepared = quantization.prepare(model)
                    quantization.set_fake_quantize(prepared, True)
                    quantized = quantization.convert(prepared)
                    quantization.check_model(quantized)
                    return quantization.compile_model(quantized, "model.hbm")
                """
            ).lstrip(),
            encoding="utf-8",
        )
        invoke(
            [sys.executable, str(scripts / "check_qat_target.py"), "--source", str(valid_qat), "--stage", "all"],
            "Plugin QAT target smoke",
            failures,
            cwd=root.parent,
        )
        invalid_qat = work / "invalid_qat.py"
        invalid_qat.write_text(
            "import hat\nfrom horizon_plugin_pytorch import March\ntarget = March.BAYES\ncommand = 'hb_mapper makertbin'\n",
            encoding="utf-8",
        )
        invoke(
            [sys.executable, str(scripts / "check_qat_target.py"), "--source", str(invalid_qat), "--stage", "all"],
            "Plugin QAT isolation rejection smoke",
            failures,
            expected=(2,),
            cwd=root.parent,
        )

        somstatus = work / "somstatus.txt"
        somstatus.write_text(
            textwrap.dedent(
                """
                ========== 1 ==========
                temperature -->
                cpu : 45 (C)
                CPU frequency
                cpu0 : 300 1200 1500
                BPU status
                bpu0 : 400 800 1000 75
                DDR frequency
                ddr : 100 1600 3200
                """
            ).lstrip(),
            encoding="utf-8",
        )
        somstatus_json = work / "board-resource.json"
        parsed = invoke(
            [
                sys.executable,
                str(scripts / "parse_somstatus.py"),
                "--input",
                str(somstatus),
                "--output",
                str(somstatus_json),
            ],
            "hrut_somstatus parser smoke",
            failures,
            cwd=root.parent,
        )
        if parsed is not None and parsed.returncode == 0:
            board = load_json(somstatus_json, failures)
            assert_true(board.get("snapshot_count") == 1, "somstatus smoke snapshot_count must be 1", failures)
            ratio = board.get("summary", {}).get("bpu_ratio_percent", {}).get("bpu0", {}).get("peak")
            assert_true(ratio == 75.0, "somstatus smoke did not preserve BPU ratio", failures)

        environment_json = work / "environment.json"
        probe = invoke(
            [
                sys.executable,
                str(scripts / "probe_environment.py"),
                "--workflow",
                "environment",
                "--docs-root",
                str(docs_root),
                "--output",
                str(environment_json),
            ],
            "X5 environment probe smoke",
            failures,
            cwd=root.parent,
        )
        if probe is None or probe.returncode != 0:
            return
        environment = load_json(environment_json, failures)
        assert_true(environment.get("platform") == "X5", "Environment smoke has wrong platform", failures)
        assert_true(environment.get("documentation", {}).get("hat_in_scope") is False, "Environment smoke includes HAT", failures)

        run_root = work / "contract-run"
        contract_script = scripts / "run_contract.py"
        steps: list[tuple[list[str], str, tuple[int, ...]]] = [
            (
                [
                    sys.executable,
                    str(contract_script),
                    "init",
                    "--run-root",
                    str(run_root),
                    "--skill-id",
                    "x5-ptq-deploy",
                    "--risk",
                    "medium",
                    "--environment-json",
                    str(environment_json),
                    "--approval-required",
                ],
                "run contract init smoke",
                (0,),
            ),
            (
                [sys.executable, str(contract_script), "update", "--run-root", str(run_root), "--status", "preflight"],
                "run contract preflight smoke",
                (0,),
            ),
            (
                [sys.executable, str(contract_script), "update", "--run-root", str(run_root), "--status", "planned"],
                "run contract planned smoke",
                (0,),
            ),
            (
                [sys.executable, str(contract_script), "update", "--run-root", str(run_root), "--status", "running"],
                "run contract approval gate smoke",
                (2,),
            ),
            (
                [sys.executable, str(contract_script), "update", "--run-root", str(run_root), "--status", "awaiting_approval"],
                "run contract awaiting approval smoke",
                (0,),
            ),
            (
                [
                    sys.executable,
                    str(contract_script),
                    "update",
                    "--run-root",
                    str(run_root),
                    "--status",
                    "running",
                    "--approval-record",
                    "x5-pack-smoke-approved",
                ],
                "run contract approved execution smoke",
                (0,),
            ),
            (
                [
                    sys.executable,
                    str(contract_script),
                    "update",
                    "--run-root",
                    str(run_root),
                    "--status",
                    "verifying",
                    "--artifact",
                    f"{ptq_report}:ptq-report",
                ],
                "run contract artifact hash smoke",
                (0,),
            ),
            (
                [
                    sys.executable,
                    str(contract_script),
                    "verify",
                    "--run-root",
                    str(run_root),
                    "--name",
                    "fake-toolchain-smoke",
                    "--passed",
                    "--evidence",
                    str(ptq_report),
                    "--summary-evidence",
                    "ptq-report.json",
                ],
                "run contract verification smoke",
                (0,),
            ),
            (
                [sys.executable, str(contract_script), "update", "--run-root", str(run_root), "--status", "succeeded"],
                "run contract success gate smoke",
                (0,),
            ),
            (
                [
                    sys.executable,
                    str(contract_script),
                    "receipt",
                    "--run-root",
                    str(run_root),
                    "--limitation",
                    "fake toolchain only",
                    "--next-skill",
                    "x5-runtime-deploy",
                ],
                "run contract receipt smoke",
                (0,),
            ),
            (
                [sys.executable, str(contract_script), "validate", "--run-root", str(run_root)],
                "run contract schema smoke",
                (0,),
            ),
        ]
        for command, label, expected in steps:
            result = invoke(command, label, failures, expected=expected, cwd=root.parent)
            if result is None or result.returncode not in expected:
                return
        receipt = load_json(run_root / "receipt.json", failures)
        artifacts = receipt.get("artifacts", [])
        sha256 = artifacts[0].get("sha256") if artifacts else None
        assert_true(isinstance(sha256, str) and len(sha256) == 64, "Run receipt lacks an artifact SHA256", failures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-root", help="Override the X5 local documentation root")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip executable script smoke tests")
    args = parser.parse_args()

    root = installed_root()
    failures: list[str] = []
    pack_index = check_pack_index(root, failures)
    global_index = check_global_index(root, pack_index, failures)
    pack_manual_references = check_pack_documents(root, failures)
    check_router(root, failures)
    _, skill_manual_references = check_skill_contracts(root, pack_index, global_index, failures)
    check_eval_matrix(root, failures)
    check_schemas_and_assets(root, failures)

    docs_root: Path | None = None
    try:
        docs_root = resolve_doc_root(args.docs_root)
    except FileNotFoundError as error:
        failures.append(str(error))
    if docs_root is not None:
        check_manual(root, docs_root, pack_index, pack_manual_references | skill_manual_references, failures)
        if not args.skip_smoke:
            check_script_smoke(root, docs_root, failures)

    if failures:
        print("\n".join(f"FAIL: {failure}" for failure in failures), file=sys.stderr)
        return 1
    smoke_label = "static-only" if args.skip_smoke else "script-smoke"
    print(
        "X5_SKILL_VALIDATION_OK: "
        f"{len(EXPECTED_SKILLS)} skills, {len(REQUIRED_SCHEMAS)} schemas, "
        f"{len(REQUIRED_SCRIPTS)} scripts, {smoke_label}, HAT/S/X3 isolation"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
