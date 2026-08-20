#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Validate an X5 OE Mapper PTQ YAML against schema and semantic guards."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


CALIBRATION_TYPES = {"default", "mix", "kl", "max", "skip"}
FORBIDDEN_TEXT = (
    (re.compile(r"\bMarch\.BAYES\b"), "March.BAYES targets J5; X5 PTQ must use bayes-e"),
    (re.compile(r"\b(?:nash-[a-z0-9_-]+|bernoulli2|hbdk4|hmct|libhbucp)\b", re.I), "S/X3 toolchain term found in X5 PTQ config"),
    (re.compile(r"(?:^|[\\/_.-])hat(?:[\\/_.-]|$)", re.I), "HAT assets are outside the X5 Pack"),
    (re.compile(r"tools[\\/]compile_perf\.py", re.I), "HAT compile_perf.py is outside the X5 Pack"),
)
NODE_INFO_KEY = re.compile(r"^(?:ON|OutputType|InputType(?:[0-9]+)?)$")
NODE_INFO_STRING = re.compile(r"^[^:;]+:[^:;]+(?:\s*;\s*[^:;]+:[^:;]+)*$")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("PyYAML is required to validate PTQ YAML") from error
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("PTQ YAML root must be a mapping")
    return payload


def load_schema() -> dict[str, Any]:
    schema_path = Path(__file__).resolve().parents[1] / "schemas" / "ptq-config.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def split_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(";") if item.strip()]


def all_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from all_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from all_strings(item)


def resolve_declared_path(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def add_node_info_errors(model: dict[str, Any], errors: list[str]) -> None:
    node_info = model.get("node_info")
    if node_info is None:
        return
    if isinstance(node_info, str):
        if not NODE_INFO_STRING.fullmatch(node_info.strip()):
            errors.append("model_parameters.node_info string must use node:type entries separated by semicolons")
        return
    if not isinstance(node_info, dict):
        errors.append("model_parameters.node_info must be a string or mapping")
        return
    for node_name, settings in node_info.items():
        if not isinstance(node_name, str) or not node_name.strip():
            errors.append("model_parameters.node_info node names must be non-empty strings")
        if not isinstance(settings, dict) or not settings:
            errors.append(f"model_parameters.node_info[{node_name!r}] must be a non-empty mapping")
            continue
        for key, value in settings.items():
            if not isinstance(key, str):
                errors.append(
                    "model_parameters.node_info setting keys must be strings; quote YAML keys such as 'ON'"
                )
                continue
            if not NODE_INFO_KEY.fullmatch(key):
                errors.append(f"model_parameters.node_info[{node_name!r}] contains unsupported key: {key}")
                continue
            if key == "ON" and value not in {"BPU", "CPU"}:
                errors.append(f"model_parameters.node_info[{node_name!r}].ON must be 'BPU' or 'CPU'")
            elif key != "ON" and (not isinstance(value, str) or not value.strip()):
                errors.append(f"model_parameters.node_info[{node_name!r}].{key} must be a non-empty string")


def add_schema_errors(config: dict[str, Any], errors: list[str]) -> None:
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError("jsonschema is required to validate PTQ YAML") from error
    validator = jsonschema.Draft202012Validator(load_schema())
    for issue in sorted(validator.iter_errors(config), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in issue.absolute_path) or "<root>"
        errors.append(f"schema:{location}: {issue.message}")


def validate_config(
    config: dict[str, Any],
    *,
    config_path: Path | None = None,
    check_paths: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    add_schema_errors(config, errors)

    model = config.get("model_parameters", {})
    inputs = config.get("input_parameters", {})
    calibration = config.get("calibration_parameters", {})
    compiler = config.get("compiler_parameters", {})

    add_node_info_errors(model, errors)

    if model.get("march") != "bayes-e":
        errors.append("model_parameters.march must be exactly 'bayes-e'")

    model_paths = [key for key in ("onnx_model", "caffe_model") if model.get(key)]
    if len(model_paths) != 1:
        errors.append("configure exactly one model source: onnx_model or caffe_model + prototxt")
    if model.get("onnx_model") and Path(str(model["onnx_model"])).suffix.lower() != ".onnx":
        errors.append("onnx_model must end in .onnx")
    if model.get("caffe_model") and Path(str(model["caffe_model"])).suffix.lower() not in {".caffemodel", ".model"}:
        errors.append("caffe_model must use a Caffe model suffix")
    if model.get("prototxt") and Path(str(model["prototxt"])).suffix.lower() != ".prototxt":
        errors.append("prototxt must end in .prototxt")
    for key in ("onnx_model", "caffe_model", "prototxt"):
        value = model.get(key)
        if value and Path(str(value)).suffix.lower() in {".hbm", ".hbir", ".bin"}:
            errors.append(f"{key} is not a floating PTQ input; QAT/Runtime artifacts use a different contract")

    calibration_type = str(calibration.get("calibration_type", "")).lower()
    if calibration_type not in CALIBRATION_TYPES:
        errors.append(
            "calibration_type must be one of default, mix, kl, max, skip; "
            "Plugin 'load' integration is intentionally excluded from this PTQ contract"
        )
    if calibration_type != "skip" and not calibration.get("cal_data_dir"):
        errors.append("cal_data_dir is required unless calibration_type is skip")
    if calibration_type != "skip" and not calibration.get("cal_data_type"):
        errors.append("cal_data_type is required unless calibration_type is skip")
    if calibration_type == "skip" and calibration.get("cal_data_dir"):
        warnings.append("cal_data_dir is ignored when calibration_type is skip")

    aligned_fields = (
        "input_name",
        "input_shape",
        "input_type_train",
        "input_layout_train",
        "input_type_rt",
    )
    values = {field: split_values(inputs.get(field)) for field in aligned_fields}
    expected_count = len(values["input_name"])
    if expected_count == 0:
        errors.append("input_name must explicitly record every input for reproducibility")
    for field in aligned_fields[1:]:
        if expected_count and len(values[field]) != expected_count:
            errors.append(f"{field} count must match input_name count ({expected_count})")
    for shape in values["input_shape"]:
        if not re.fullmatch(r"[0-9]+(?:x[0-9]+)+", shape):
            errors.append(f"invalid input_shape value: {shape}")
    runtime_layouts = split_values(inputs.get("input_layout_rt"))
    runtime_types = [item.lower() for item in values["input_type_rt"]]
    if runtime_layouts and expected_count and len(runtime_layouts) != expected_count:
        errors.append(f"input_layout_rt count must match input_name count ({expected_count})")
    if not runtime_layouts and any(item != "nv12" for item in runtime_types):
        warnings.append("input_layout_rt is omitted for a non-nv12 Runtime input; confirm the manual contract")

    input_sources = compiler.get("input_source", {})
    if isinstance(input_sources, dict) and expected_count:
        unknown_sources = sorted(set(input_sources) - set(values["input_name"]))
        if unknown_sources:
            errors.append("compiler_parameters.input_source contains unknown inputs: " + ", ".join(unknown_sources))

    output_prefix = str(model.get("output_model_file_prefix", ""))
    if output_prefix and not re.fullmatch(r"[A-Za-z0-9_.-]+", output_prefix):
        errors.append("output_model_file_prefix may contain only letters, digits, dot, underscore, and dash")

    for text in all_strings(config):
        for pattern, message in FORBIDDEN_TEXT:
            if pattern.search(text):
                errors.append(f"{message}: {text}")

    if check_paths:
        base = config_path.parent.resolve() if config_path else Path.cwd().resolve()
        for key in ("onnx_model", "caffe_model", "prototxt"):
            value = model.get(key)
            if value and not resolve_declared_path(base, str(value)).is_file():
                errors.append(f"declared file does not exist: {key}={value}")
        if calibration_type != "skip":
            for value in split_values(calibration.get("cal_data_dir")):
                if not resolve_declared_path(base, value).is_dir():
                    errors.append(f"calibration directory does not exist: {value}")

    return {
        "schema_version": "1.0",
        "valid": not errors,
        "platform": "X5",
        "contract": "oe-mapper-ptq",
        "march": model.get("march"),
        "model_type": "onnx" if model.get("onnx_model") else "caffe" if model.get("caffe_model") else None,
        "input_count": expected_count,
        "calibration_type": calibration_type or None,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", help="X5 OE Mapper YAML")
    parser.add_argument("--check-paths", action="store_true")
    parser.add_argument("--report")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()
    try:
        report = validate_config(load_yaml(config_path), config_path=config_path, check_paths=args.check_paths)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.report:
        write_report(Path(args.report).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
