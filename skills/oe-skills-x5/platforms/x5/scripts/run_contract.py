#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Create and update machine-readable X5 workflow run records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATUSES = (
    "created",
    "preflight",
    "planned",
    "awaiting_approval",
    "running",
    "verifying",
    "succeeded",
    "failed",
    "blocked",
    "cancelled",
)
TERMINAL_STATUSES = {"succeeded", "failed", "blocked", "cancelled"}
ALLOWED_TRANSITIONS = {
    "created": {"created", "preflight", "blocked", "cancelled"},
    "preflight": {"preflight", "planned", "blocked", "failed", "cancelled"},
    "planned": {"planned", "awaiting_approval", "running", "blocked", "cancelled"},
    "awaiting_approval": {"awaiting_approval", "running", "blocked", "cancelled"},
    "running": {"running", "verifying", "failed", "blocked", "cancelled"},
    "verifying": {"verifying", "succeeded", "failed", "blocked", "cancelled"},
    "succeeded": {"succeeded"},
    "failed": {"failed"},
    "blocked": {"blocked"},
    "cancelled": {"cancelled"},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, newline="\n"
    ) as handle:
        handle.write(text)
        temporary = Path(handle.name)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def append_event(run_root: Path, event: str, details: dict[str, Any] | None = None) -> None:
    payload = {"timestamp": utc_now(), "event": event, "details": details or {}}
    with (run_root / "events.ndjson").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def file_sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_artifact(value: str) -> tuple[Path, str]:
    path_text, separator, artifact_type = value.rpartition(":")
    if not separator or not path_text or not artifact_type:
        raise argparse.ArgumentTypeError("artifact must use PATH:TYPE")
    return Path(path_text).expanduser(), artifact_type


def command_init(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).expanduser().resolve()
    state_path = run_root / "run-state.json"
    if state_path.exists() and not args.resume:
        raise FileExistsError(f"run already exists: {run_root}; pass --resume to reuse it")

    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "logs").mkdir(exist_ok=True)
    if args.resume:
        state = read_json(state_path)
        append_event(run_root, "run-resumed", {"status": state["status"]})
        print(run_root)
        return 0

    input_payload: Any = {}
    if args.input_json:
        input_payload = read_json(Path(args.input_json).expanduser().resolve())
    run_id = args.run_id or run_root.name or str(uuid.uuid4())
    state = {
        "schema_version": "1.0",
        "run_id": run_id,
        "skill_id": args.skill_id,
        "status": "created",
        "stage": "initialized",
        "risk": args.risk,
        "retry_count": 0,
        "approval": {"required": args.approval_required, "record": None},
        "artifacts": [],
        "logs": [],
        "next_step": "preflight",
        "updated_at": utc_now(),
    }
    write_json(run_root / "input.json", input_payload)
    if args.environment_json:
        write_json(
            run_root / "environment.json",
            read_json(Path(args.environment_json).expanduser().resolve()),
        )
    write_json(
        run_root / "route.json",
        {
            "schema_version": "1.0",
            "platform": "X5",
            "selected_skill": args.skill_id,
            "candidates": [args.skill_id],
            "rejections": [],
            "handoffs": [],
        },
    )
    write_json(
        run_root / "plan.json",
        {
            "schema_version": "1.0",
            "skill_id": args.skill_id,
            "risk": args.risk,
            "approval_required": args.approval_required,
            "steps": [],
            "side_effects": [],
            "verification": [],
        },
    )
    write_json(state_path, state)
    write_json(run_root / "artifacts.json", {"schema_version": "1.0", "artifacts": []})
    write_json(
        run_root / "verification.json",
        {"schema_version": "1.0", "passed": False, "checks": [], "evidence": None},
    )
    (run_root / "events.ndjson").touch()
    append_event(run_root, "run-created", {"skill_id": args.skill_id, "risk": args.risk})
    print(run_root)
    return 0


def command_update(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).expanduser().resolve()
    state_path = run_root / "run-state.json"
    state = read_json(state_path)
    old_status = state["status"]
    new_status = args.status or old_status
    if new_status not in ALLOWED_TRANSITIONS[old_status]:
        raise ValueError(f"invalid status transition: {old_status} -> {new_status}")
    if args.retry_increment:
        state["retry_count"] += 1
        if state["retry_count"] > 2:
            raise ValueError("retry_count cannot exceed two; hand off to diagnosis")

    if args.approval_record is not None:
        state["approval"]["record"] = args.approval_record
    if new_status == "running" and state["approval"]["required"] and not state["approval"]["record"]:
        raise ValueError("approval record is required before entering running")

    state["status"] = new_status
    if args.stage is not None:
        state["stage"] = args.stage
    if args.next_step is not None:
        state["next_step"] = args.next_step
    artifacts_payload = read_json(run_root / "artifacts.json")
    for path, artifact_type in args.artifact or []:
        resolved = path.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"artifact is not a file: {resolved}")
        artifact = {
            "path": str(resolved),
            "type": artifact_type,
            "sha256": file_sha256(resolved),
            "recorded_at": utc_now(),
        }
        artifacts_payload["artifacts"] = [
            item
            for item in artifacts_payload["artifacts"]
            if not (item["path"] == artifact["path"] and item["type"] == artifact["type"])
        ]
        artifacts_payload["artifacts"].append(artifact)
        state["artifacts"].append(str(resolved))

    for log in args.log or []:
        resolved_log = str(Path(log).expanduser().resolve())
        if resolved_log not in state["logs"]:
            state["logs"].append(resolved_log)

    if new_status == "succeeded":
        verification = read_json(run_root / "verification.json")
        if not verification.get("passed"):
            raise ValueError("cannot mark succeeded before verification.json passes")
        if not artifacts_payload["artifacts"]:
            raise ValueError("cannot mark succeeded without at least one hashed artifact")

    state["updated_at"] = utc_now()
    write_json(state_path, state)
    write_json(run_root / "artifacts.json", artifacts_payload)
    append_event(
        run_root,
        "run-updated",
        {"from": old_status, "to": new_status, "stage": state["stage"]},
    )
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


def command_verify(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).expanduser().resolve()
    payload = read_json(run_root / "verification.json")
    check = {
        "name": args.name,
        "passed": args.passed,
        "evidence": args.evidence,
        "recorded_at": utc_now(),
    }
    payload["checks"].append(check)
    payload["passed"] = bool(payload["checks"]) and all(item["passed"] for item in payload["checks"])
    payload["evidence"] = args.summary_evidence or payload.get("evidence")
    write_json(run_root / "verification.json", payload)
    append_event(run_root, "verification-recorded", check)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def command_receipt(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).expanduser().resolve()
    state = read_json(run_root / "run-state.json")
    if state["status"] not in TERMINAL_STATUSES:
        raise ValueError("receipt requires a terminal run status")
    for name in ("environment.json", "route.json", "plan.json"):
        if not (run_root / name).is_file():
            raise FileNotFoundError(f"receipt requires {name}")
    artifacts = read_json(run_root / "artifacts.json")["artifacts"]
    verification = read_json(run_root / "verification.json")
    if state["status"] == "succeeded" and not verification.get("passed"):
        raise ValueError("a succeeded receipt requires passed verification")
    receipt = {
        "schema_version": "1.0",
        "run_id": state["run_id"],
        "skill_id": state["skill_id"],
        "status": state["status"],
        "risk": state["risk"],
        "approval": state["approval"],
        "artifacts": [
            {"path": item["path"], "type": item["type"], "sha256": item["sha256"]}
            for item in artifacts
        ],
        "verification": {
            "passed": bool(verification.get("passed")),
            "evidence": verification.get("evidence") or "verification.json",
        },
        "limitations": args.limitation or [],
        "handoff": {
            "next_skill": args.next_skill,
            "required_inputs": args.required_input or [],
        },
        "completed_at": utc_now(),
    }
    write_json(run_root / "receipt.json", receipt)
    append_event(run_root, "receipt-written", {"status": state["status"]})
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


def load_schema(name: str) -> dict[str, Any]:
    return read_json(Path(__file__).resolve().parents[1] / "schemas" / name)


def validate_with_jsonschema(payload: Any, schema: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError("jsonschema is required for the validate command") from error
    jsonschema.validate(payload, schema, format_checker=jsonschema.FormatChecker())


def command_validate(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).expanduser().resolve()
    required = [
        "input.json",
        "environment.json",
        "route.json",
        "plan.json",
        "run-state.json",
        "events.ndjson",
        "artifacts.json",
        "verification.json",
    ]
    missing = [name for name in required if not (run_root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing run files: {', '.join(missing)}")
    validate_with_jsonschema(read_json(run_root / "run-state.json"), load_schema("run-state.schema.json"))
    validate_with_jsonschema(read_json(run_root / "environment.json"), load_schema("environment.schema.json"))
    validate_with_jsonschema(read_json(run_root / "route.json"), load_schema("route.schema.json"))
    validate_with_jsonschema(read_json(run_root / "plan.json"), load_schema("plan.schema.json"))
    validate_with_jsonschema(read_json(run_root / "artifacts.json"), load_schema("artifacts.schema.json"))
    validate_with_jsonschema(read_json(run_root / "verification.json"), load_schema("verification.schema.json"))
    receipt_path = run_root / "receipt.json"
    if receipt_path.exists():
        validate_with_jsonschema(read_json(receipt_path), load_schema("receipt.schema.json"))
    print(f"X5_RUN_CONTRACT_OK: {run_root}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--run-root", required=True)
    init_parser.add_argument("--skill-id", required=True)
    init_parser.add_argument("--risk", choices=("low", "medium", "high", "critical"), required=True)
    init_parser.add_argument("--run-id")
    init_parser.add_argument("--input-json")
    init_parser.add_argument("--environment-json")
    init_parser.add_argument("--approval-required", action="store_true")
    init_parser.add_argument("--resume", action="store_true")
    init_parser.set_defaults(func=command_init)

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("--run-root", required=True)
    update_parser.add_argument("--status", choices=STATUSES)
    update_parser.add_argument("--stage")
    update_parser.add_argument("--next-step")
    update_parser.add_argument("--retry-increment", action="store_true")
    update_parser.add_argument("--approval-record")
    update_parser.add_argument("--artifact", action="append", type=parse_artifact)
    update_parser.add_argument("--log", action="append")
    update_parser.set_defaults(func=command_update)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--run-root", required=True)
    verify_parser.add_argument("--name", required=True)
    verify_parser.add_argument("--passed", action=argparse.BooleanOptionalAction, required=True)
    verify_parser.add_argument("--evidence")
    verify_parser.add_argument("--summary-evidence")
    verify_parser.set_defaults(func=command_verify)

    receipt_parser = subparsers.add_parser("receipt")
    receipt_parser.add_argument("--run-root", required=True)
    receipt_parser.add_argument("--limitation", action="append")
    receipt_parser.add_argument("--next-skill")
    receipt_parser.add_argument("--required-input", action="append")
    receipt_parser.set_defaults(func=command_receipt)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--run-root", required=True)
    validate_parser.set_defaults(func=command_validate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
