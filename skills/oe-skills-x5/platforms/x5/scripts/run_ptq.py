#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Run guarded X5 OE Mapper PTQ checker, compile, and model verification stages."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_ptq_config import load_yaml, split_values, validate_config


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def executable(name: str) -> str:
    value = shutil.which(name)
    if not value:
        raise RuntimeError(f"required command is not available: {name}")
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, newline="\n") as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def resolve_value(config_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (config_path.parent / path).resolve()


def model_contract(config_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    model = config["model_parameters"]
    inputs = config["input_parameters"]
    if model.get("onnx_model"):
        model_type = "onnx"
        model_path = resolve_value(config_path, str(model["onnx_model"]))
        proto_path = None
    else:
        model_type = "caffe"
        model_path = resolve_value(config_path, str(model["caffe_model"]))
        proto_path = resolve_value(config_path, str(model["prototxt"]))
    names = split_values(inputs["input_name"])
    shapes = split_values(inputs["input_shape"])
    working_dir = resolve_value(config_path, str(model["working_dir"]))
    return {
        "model_type": model_type,
        "model_path": model_path,
        "proto_path": proto_path,
        "input_shapes": list(zip(names, shapes, strict=True)),
        "working_dir": working_dir,
        "output_prefix": str(model["output_model_file_prefix"]),
    }


def run_command(command: list[str], cwd: Path, log_path: Path) -> dict[str, Any]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started_at = utc_now()
    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        completed = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, check=False, text=True)
    return {
        "command": command,
        "cwd": str(cwd),
        "log": str(log_path),
        "returncode": completed.returncode,
        "started_at": started_at,
        "completed_at": utc_now(),
    }


def validated_config(config_path: Path, check_paths: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    config = load_yaml(config_path)
    report = validate_config(config, config_path=config_path, check_paths=check_paths)
    if not report["valid"]:
        raise ValueError("PTQ config is invalid: " + "; ".join(report["errors"]))
    return config, report


def checker_stage(config_path: Path, output_dir: Path) -> dict[str, Any]:
    config, validation = validated_config(config_path)
    contract = model_contract(config_path, config)
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"checker output is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        executable("hb_mapper"),
        "checker",
        "--model-type",
        contract["model_type"],
        "--march",
        "bayes-e",
        "--model",
        str(contract["model_path"]),
    ]
    if contract["proto_path"]:
        command.extend(["--proto", str(contract["proto_path"])])
    for name, shape in contract["input_shapes"]:
        command.extend(["--input-shape", name, shape])
    command.extend(["--output", str(output_dir)])
    execution = run_command(command, config_path.parent, output_dir / "hb_mapper_checker.log")
    return {
        "stage": "checker",
        "passed": execution["returncode"] == 0,
        "validation": validation,
        "execution": execution,
        "output_dir": str(output_dir),
    }


def locate_artifacts(working_dir: Path, prefix: str) -> dict[str, list[str]]:
    bins = sorted(path.resolve() for path in working_dir.rglob("*.bin") if path.is_file()) if working_dir.is_dir() else []
    expected = working_dir / f"{prefix}.bin"
    if expected.is_file():
        bins = [expected.resolve()] + [path for path in bins if path.resolve() != expected.resolve()]
    quantized = sorted(path.resolve() for path in working_dir.rglob("*.onnx") if path.is_file()) if working_dir.is_dir() else []
    return {"bin": [str(path) for path in bins], "onnx": [str(path) for path in quantized]}


def model_info_stage(model_path: Path, log_path: Path) -> dict[str, Any]:
    command = [executable("hb_model_info"), str(model_path.resolve())]
    execution = run_command(command, log_path.parent.resolve(), log_path.resolve())
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    match = re.search(r"BPU\s+march\s*:\s*([A-Za-z0-9_-]+)", text, re.I)
    march = match.group(1).lower() if match else None
    return {
        "stage": "model-info",
        "passed": execution["returncode"] == 0 and march == "bayes-e",
        "execution": execution,
        "model": str(model_path.resolve()),
        "bpu_march": march,
        "errors": [] if march == "bayes-e" else ["hb_model_info did not prove BPU march: bayes-e"],
    }


def compile_stage(config_path: Path, allow_nonempty_working_dir: bool) -> dict[str, Any]:
    config, validation = validated_config(config_path)
    contract = model_contract(config_path, config)
    working_dir: Path = contract["working_dir"]
    if working_dir.exists() and any(working_dir.iterdir()) and not allow_nonempty_working_dir:
        raise FileExistsError(
            f"working_dir is not empty: {working_dir}; use a new attempt directory or pass "
            "--allow-nonempty-working-dir only after review"
        )
    working_dir.mkdir(parents=True, exist_ok=True)
    log_path = working_dir / "hb_mapper_makertbin.log"
    command = [
        executable("hb_mapper"),
        "makertbin",
        "--config",
        str(config_path),
        "--model-type",
        contract["model_type"],
    ]
    execution = run_command(command, config_path.parent, log_path)
    artifacts = locate_artifacts(working_dir, contract["output_prefix"])
    errors: list[str] = []
    model_info: dict[str, Any] | None = None
    if execution["returncode"] != 0:
        errors.append("hb_mapper makertbin failed")
    if len(artifacts["bin"]) != 1:
        errors.append(f"expected exactly one .bin artifact, found {len(artifacts['bin'])}")
    if not errors:
        model_info = model_info_stage(Path(artifacts["bin"][0]), working_dir / "hb_model_info.log")
        if not model_info["passed"]:
            errors.extend(model_info["errors"])
    return {
        "stage": "compile",
        "passed": not errors,
        "validation": validation,
        "execution": execution,
        "working_dir": str(working_dir),
        "artifacts": artifacts,
        "model_info": model_info,
        "errors": errors,
    }


def command_checker(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    report = {
        "schema_version": "1.0",
        "platform": "X5",
        "contract": "oe-mapper-ptq",
        "stages": [checker_stage(config_path, Path(args.output_dir).expanduser())],
    }
    report["passed"] = all(stage["passed"] for stage in report["stages"])
    write_json(Path(args.report).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


def command_compile(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    stage = compile_stage(config_path, args.allow_nonempty_working_dir)
    report = {
        "schema_version": "1.0",
        "platform": "X5",
        "contract": "oe-mapper-ptq",
        "passed": stage["passed"],
        "stages": [stage],
    }
    write_json(Path(args.report).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


def command_verify(args: argparse.Namespace) -> int:
    model_path = Path(args.model).expanduser().resolve()
    if model_path.suffix.lower() != ".bin" or not model_path.is_file():
        raise ValueError("verify requires an existing X5 PTQ .bin")
    stage = model_info_stage(model_path, Path(args.log).expanduser().resolve())
    report = {
        "schema_version": "1.0",
        "platform": "X5",
        "contract": "oe-mapper-ptq",
        "passed": stage["passed"],
        "stages": [stage],
    }
    write_json(Path(args.report).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


def command_full(args: argparse.Namespace) -> int:
    config_path = Path(args.config).expanduser().resolve()
    config, _ = validated_config(config_path)
    contract = model_contract(config_path, config)
    checker_output = (
        Path(args.checker_output).expanduser().resolve()
        if args.checker_output
        else config_path.parent / f"{contract['output_prefix']}_checker"
    )
    checker = checker_stage(config_path, checker_output)
    stages = [checker]
    if checker["passed"]:
        stages.append(compile_stage(config_path, args.allow_nonempty_working_dir))
    report = {
        "schema_version": "1.0",
        "platform": "X5",
        "contract": "oe-mapper-ptq",
        "passed": len(stages) == 2 and all(stage["passed"] for stage in stages),
        "stages": stages,
    }
    write_json(Path(args.report).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    checker = subparsers.add_parser("checker")
    checker.add_argument("--config", required=True)
    checker.add_argument("--output-dir", required=True)
    checker.add_argument("--report", required=True)
    checker.set_defaults(func=command_checker)

    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("--config", required=True)
    compile_parser.add_argument("--report", required=True)
    compile_parser.add_argument("--allow-nonempty-working-dir", action="store_true")
    compile_parser.set_defaults(func=command_compile)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--model", required=True)
    verify.add_argument("--log", required=True)
    verify.add_argument("--report", required=True)
    verify.set_defaults(func=command_verify)

    full = subparsers.add_parser("full")
    full.add_argument("--config", required=True)
    full.add_argument("--checker-output")
    full.add_argument("--report", required=True)
    full.add_argument("--allow-nonempty-working-dir", action="store_true")
    full.set_defaults(func=command_full)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, RuntimeError, FileExistsError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
