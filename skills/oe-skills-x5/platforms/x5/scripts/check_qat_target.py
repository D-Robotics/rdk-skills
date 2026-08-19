#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Check X5 Plugin QAT source for target, API, and scope violations."""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any


def dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


class SourceFacts(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.attributes: set[str] = set()
        self.calls: set[str] = set()
        self.string_literals: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        self.imports.update(alias.name for alias in node.names)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        name = dotted_name(node)
        if name:
            self.attributes.add(name)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = dotted_name(node.func)
        if name:
            self.calls.add(name)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            self.string_literals.append(node.value)


def has_call(calls: set[str], *names: str) -> bool:
    return any(call == name or call.endswith("." + name) for call in calls for name in names)


def inspect_sources(paths: list[Path], stage: str) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    facts = SourceFacts()
    source_texts: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        source_texts.append(text)
        try:
            facts.visit(ast.parse(text, filename=str(path)))
        except SyntaxError as error:
            errors.append(f"{path}: syntax error at line {error.lineno}: {error.msg}")

    combined = "\n".join(source_texts)
    if any(name == "hat" or name.startswith("hat.") for name in facts.imports):
        errors.append("HAT imports are outside the X5 Plugin QAT Pack")
    if re.search(r"tools[\\/]compile_perf\.py", combined, re.I):
        errors.append("HAT tools/compile_perf.py is outside the X5 Plugin QAT Pack")
    if re.search(r"\bhb_mapper\s+makertbin\b", combined):
        errors.append("QAT source must not delegate compilation to hb_mapper makertbin")
    if re.search(r"\bMarch\.BAYES\b", combined):
        errors.append("March.BAYES targets J5; X5 must use March.BAYES_E")

    has_bayes_e = any(name.endswith("March.BAYES_E") for name in facts.attributes) or "March.BAYES_E" in combined
    has_set_march = has_call(facts.calls, "set_march")
    has_prepare = has_call(facts.calls, "prepare_qat_fx", "prepare_fx", "prepare")
    has_fake_quant = has_call(facts.calls, "set_fake_quantize")
    has_convert = has_call(facts.calls, "convert_fx", "convert")
    has_check = has_call(facts.calls, "check_model")
    has_compile = has_call(facts.calls, "compile_model")
    has_export_hbir = has_call(facts.calls, "export_hbir")

    if not has_bayes_e:
        errors.append("no explicit March.BAYES_E target evidence found")
    if not has_set_march:
        errors.append("set_march(...) must run before prepare/convert/compile")
    if stage in {"all", "adaptation", "training"} and not has_prepare:
        errors.append("QAT adaptation/training requires a Plugin prepare API")
    if stage in {"all", "training"} and not has_fake_quant:
        errors.append("QAT training must make fake-quant state transitions explicit")
    if stage in {"all", "training", "compile"} and not has_convert:
        errors.append("QAT training/compile requires an explicit quantized-model convert step")
    if stage in {"all", "compile"} and not has_check:
        errors.append("QAT compile requires check_model before compilation/export")
    if stage in {"all", "compile"} and not (has_compile or has_export_hbir):
        errors.append("QAT compile requires compile_model or export_hbir")
    if (has_compile or has_export_hbir) and re.search(r"['\"][^'\"]+\.bin['\"]", combined, re.I):
        errors.append("Plugin QAT compile output must not be disguised as a PTQ .bin")
    if has_compile and not re.search(r"['\"][^'\"]+\.hbm['\"]", combined, re.I):
        warnings.append("compile_model output .hbm is not visible as a literal; verify the resolved output path")
    if has_export_hbir and not re.search(r"['\"][^'\"]+\.hbir['\"]", combined, re.I):
        warnings.append("export_hbir output .hbir is not visible as a literal; verify the resolved output path")

    return {
        "schema_version": "1.0",
        "platform": "X5",
        "contract": "horizon-plugin-pytorch-qat",
        "stage": stage,
        "valid": not errors,
        "sources": [str(path) for path in paths],
        "detected": {
            "March.BAYES_E": has_bayes_e,
            "set_march": has_set_march,
            "prepare": has_prepare,
            "set_fake_quantize": has_fake_quant,
            "convert": has_convert,
            "check_model": has_check,
            "compile_model": has_compile,
            "export_hbir": has_export_hbir,
        },
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def probe_runtime(report: dict[str, Any]) -> None:
    try:
        plugin = importlib.import_module("horizon_plugin_pytorch")
        march = getattr(plugin, "March", None)
        if march is None:
            march = importlib.import_module("horizon_plugin_pytorch.march").March
        report["runtime_probe"] = {
            "available": True,
            "version": getattr(plugin, "__version__", None),
            "has_bayes_e": hasattr(march, "BAYES_E"),
        }
        if not report["runtime_probe"]["has_bayes_e"]:
            report["errors"].append("installed Plugin does not expose March.BAYES_E")
            report["valid"] = False
    except (ImportError, AttributeError) as error:
        report["runtime_probe"] = {"available": False, "error": str(error)}
        report["errors"].append("unable to import a Plugin runtime with March.BAYES_E")
        report["valid"] = False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", required=True)
    parser.add_argument("--stage", choices=("all", "adaptation", "training", "compile"), default="all")
    parser.add_argument("--probe-runtime", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()

    paths = [Path(value).expanduser().resolve() for value in args.source]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        parser.error("source files do not exist: " + ", ".join(missing))
    report = inspect_sources(paths, args.stage)
    if args.probe_runtime:
        probe_runtime(report)
    if args.report:
        output = Path(args.report).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
