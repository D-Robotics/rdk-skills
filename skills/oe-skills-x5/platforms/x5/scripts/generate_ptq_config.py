#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Generate a conservative, schema-valid X5 OE Mapper PTQ YAML."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from validate_ptq_config import validate_config


def infer_model_type(model: Path, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    suffix = model.suffix.lower()
    if suffix == ".onnx":
        return "onnx"
    if suffix in {".caffemodel", ".model"}:
        return "caffe"
    raise ValueError("cannot infer model type; pass --model-type onnx or caffe")


def parse_mapping(values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values or []:
        key, separator, item = value.partition("=")
        if not separator or not key.strip() or not item.strip():
            raise ValueError("mapping values must use NAME=VALUE")
        result[key.strip()] = item.strip()
    return result


def normalized_path(value: str, absolute: bool) -> str:
    path = Path(value).expanduser()
    return str(path.resolve()) if absolute else str(path)


def build_config(args: argparse.Namespace) -> dict[str, Any]:
    model_path = Path(args.model).expanduser()
    model_type = infer_model_type(model_path, args.model_type)
    if model_type == "caffe" and not args.proto:
        raise ValueError("--proto is required for a Caffe model")
    if model_type == "onnx" and args.proto:
        raise ValueError("--proto is only valid for a Caffe model")
    if args.calibration_type != "skip" and not args.cal_data_dir:
        raise ValueError("--cal-data-dir is required unless --calibration-type skip")

    prefix = args.output_prefix or re.sub(r"[^A-Za-z0-9_.-]+", "_", model_path.stem)
    model_parameters: dict[str, Any] = {
        "march": "bayes-e",
        "output_model_file_prefix": prefix,
        "working_dir": normalized_path(args.working_dir, args.absolute_paths),
        "layer_out_dump": bool(args.layer_out_dump),
    }
    if model_type == "onnx":
        model_parameters["onnx_model"] = normalized_path(args.model, args.absolute_paths)
    else:
        model_parameters["caffe_model"] = normalized_path(args.model, args.absolute_paths)
        model_parameters["prototxt"] = normalized_path(args.proto, args.absolute_paths)
    if args.output_nodes:
        model_parameters["output_nodes"] = args.output_nodes

    input_parameters: dict[str, Any] = {
        "input_name": args.input_name,
        "input_type_train": args.input_type_train,
        "input_layout_train": args.input_layout_train,
        "input_shape": args.input_shape,
        "input_type_rt": args.input_type_rt,
        "input_batch": args.input_batch,
        "norm_type": args.norm_type,
    }
    if args.input_layout_rt:
        input_parameters["input_layout_rt"] = args.input_layout_rt
    if args.input_space_and_range:
        input_parameters["input_space_and_range"] = args.input_space_and_range
    if args.mean_value:
        input_parameters["mean_value"] = args.mean_value
    if args.scale_value:
        input_parameters["scale_value"] = args.scale_value

    calibration_parameters: dict[str, Any] = {"calibration_type": args.calibration_type}
    if args.calibration_type != "skip":
        calibration_parameters["cal_data_dir"] = normalized_path(args.cal_data_dir, args.absolute_paths)
        calibration_parameters["cal_data_type"] = args.cal_data_type
    if args.per_channel:
        calibration_parameters["per_channel"] = True
    if args.max_percentile is not None:
        calibration_parameters["max_percentile"] = args.max_percentile

    compiler_parameters: dict[str, Any] = {
        "compile_mode": args.compile_mode,
        "debug": bool(args.debug),
        "core_num": args.core_num,
        "optimize_level": args.optimize_level,
        "input_source": parse_mapping(args.input_source),
        "jobs": args.jobs,
    }
    if args.max_time_per_fc:
        compiler_parameters["max_time_per_fc"] = args.max_time_per_fc

    return {
        "model_parameters": model_parameters,
        "input_parameters": input_parameters,
        "calibration_parameters": calibration_parameters,
        "compiler_parameters": compiler_parameters,
    }


def write_yaml(path: Path, config: dict[str, Any], overwrite: bool) -> None:
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("PyYAML is required to generate PTQ YAML") from error
    if path.exists() and not overwrite:
        raise FileExistsError(f"output exists: {path}; pass --overwrite only after review")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(config, allow_unicode=True, sort_keys=False, default_flow_style=False)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, newline="\n") as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-type", choices=("auto", "onnx", "caffe"), default="auto")
    parser.add_argument("--proto")
    parser.add_argument("--output", required=True)
    parser.add_argument("--output-prefix")
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--input-name", required=True, help="Use semicolons for multiple inputs")
    parser.add_argument("--input-shape", required=True, help="Use semicolons for multiple inputs")
    parser.add_argument("--input-type-train", required=True)
    parser.add_argument("--input-layout-train", required=True)
    parser.add_argument("--input-type-rt", required=True)
    parser.add_argument("--input-layout-rt")
    parser.add_argument("--input-space-and-range")
    parser.add_argument("--input-batch", type=int, default=1)
    parser.add_argument("--norm-type", choices=("data_mean_and_scale", "data_mean", "data_scale", "no_preprocess"), default="no_preprocess")
    parser.add_argument("--mean-value")
    parser.add_argument("--scale-value")
    parser.add_argument("--calibration-type", choices=("default", "mix", "kl", "max", "skip"), default="default")
    parser.add_argument("--cal-data-dir")
    parser.add_argument("--cal-data-type", default="float32")
    parser.add_argument("--max-percentile", type=float)
    parser.add_argument("--per-channel", action="store_true")
    parser.add_argument("--compile-mode", choices=("latency", "bandwidth"), default="latency")
    parser.add_argument("--core-num", type=int, default=1)
    parser.add_argument("--optimize-level", choices=("O0", "O1", "O2", "O3"), default="O2")
    parser.add_argument("--input-source", action="append", metavar="NAME=SOURCE", required=True)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--max-time-per-fc", type=int)
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--layer-out-dump", action="store_true")
    parser.add_argument("--output-nodes")
    parser.add_argument("--absolute-paths", action="store_true")
    parser.add_argument("--check-paths", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = build_config(args)
        output = Path(args.output).expanduser().resolve()
        report = validate_config(config, config_path=output, check_paths=args.check_paths)
        if not report["valid"]:
            raise ValueError("generated config failed validation: " + "; ".join(report["errors"]))
        write_yaml(output, config, args.overwrite)
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps({"config": str(output), "validation": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
