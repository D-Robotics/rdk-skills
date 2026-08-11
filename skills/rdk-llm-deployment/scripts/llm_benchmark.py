#!/usr/bin/env python3
"""Look up on-device LLM benchmark data for RDK boards.

Returns structured JSON with TTFT / TPS / memory so the agent can cite
exact performance numbers without parsing Markdown tables (anti-hallucination).

Usage:
    python3 llm_benchmark.py --board s600
    python3 llm_benchmark.py --board s600 --model Qwen3-4B
    python3 llm_benchmark.py --board s100p
    python3 llm_benchmark.py                # list all boards

Source of truth: references/llm-voice-stack.md §6 (verified from the official
model_zoo_doc appendix and the S600/S100 SDK docs). Deployment flow lives in
rdk-llm-deployment Workflows; this script only gives benchmark numbers.
"""
from __future__ import annotations

import argparse
import json
import sys

# ── S600 benchmark (max context 4096; benchmark only, not runtime) ───────────
S600_LLM = [
    {"model": "DeepSeek-R1-Distill-Qwen-1.5B", "qtype": "w4",
     "bpu_cores": "2/2", "max_context": 4096,
     "ttft_ms": 68.9, "tps": 92.4, "memory_gb": 2.2},
    {"model": "Qwen3-0.6B", "qtype": "w8",
     "bpu_cores": "4/4", "max_context": 4096,
     "ttft_ms": 75.4, "tps": 92.9, "memory_gb": 3.0},
    {"model": "Qwen3-1.7B", "qtype": "w4",
     "bpu_cores": "4/4", "max_context": 4096,
     "ttft_ms": 91.2, "tps": 75.0, "memory_gb": 3.7},
    {"model": "Qwen3-4B", "qtype": "w4",
     "bpu_cores": "4/4", "max_context": 4096,
     "ttft_ms": 232.1, "tps": 45.8, "memory_gb": 6.6},
    {"model": "Qwen3-4B", "qtype": "w8",
     "bpu_cores": "4/4", "max_context": 4096,
     "ttft_ms": 235.3, "tps": 32.3, "memory_gb": 8.3},
    {"model": "Qwen3-8B", "qtype": "w4",
     "bpu_cores": "4/4", "max_context": 4096,
     "ttft_ms": 283.6, "tps": 31.4, "memory_gb": 9.1},
]

# ── S100P benchmark (selected; benchmark only) ──────────────────────────────
S100P_LLM = [
    {"model": "DeepSeek-R1-Distill-Qwen-1.5B", "qtype": "q4",
     "max_context": 1024,
     "ttft_ms": 108.0, "tps": 39.49, "memory_gb": 1.1},
    {"model": "DeepSeek-R1-Distill-Qwen-1.5B", "qtype": "q4",
     "max_context": 4096,
     "ttft_ms": 224.0, "tps": 32.35, "memory_gb": 1.2},
    {"model": "DeepSeek-R1-Distill-Qwen-7B", "qtype": "q8",
     "max_context": 1024,
     "ttft_ms": 544.0, "tps": 6.76, "memory_gb": 7.4},
    {"model": "InternLM2-1.8B", "qtype": "q8",
     "max_context": 1024,
     "ttft_ms": 132.0, "tps": 23.83, "memory_gb": 1.8},
    {"model": "Qwen2.5-1.5B-Instruct", "qtype": "q8",
     "max_context": 1024,
     "ttft_ms": 130.0, "tps": 24.40, "memory_gb": 1.8},
]

# ── X3 legacy (hobot_llm, Bloom 1.4B) ────────────────────────────────────────
X3_LLM = [
    {"model": "Bloom-1.4B", "qtype": "fp32",
     "max_context": None,
     "ttft_ms": None, "tps": None, "memory_gb": 1.7,
     "prefill_ms_per_token": 305.34, "eval_ms_per_token": 364.78,
     "note": "X3 4GB only. BPU reserved memory must be raised to 1.7GB (0x6a400000)."},
]

BOARDS = {
    "s600": {
        "display": "RDK S600",
        "sdk": "D-Robotics_LLM_S600 1.0.2",
        "runtime": "oellm_runtime (libxlm.so)",
        "march": "nash-p",
        "artifact": ".hbm",
        "entries": S600_LLM,
        "note": "S600 does NOT use hobot_llamacpp. Deploy via D-Robotics_LLM_S600 SDK.",
    },
    "s100p": {
        "display": "RDK S100P",
        "sdk": "D-Robotics_LLM_S100 1.0.0",
        "runtime": "oellm_runtime (libxlm.so)",
        "march": "nash-m",
        "artifact": ".hbm",
        "entries": S100P_LLM,
        "note": "S100P benchmarks; S100 is same chip, different bin. Can also use hobot_llamacpp.",
    },
    "s100": {
        "display": "RDK S100",
        "sdk": "D-Robotics_LLM_S100 1.0.0",
        "runtime": "oellm_runtime (libxlm.so) or hobot_llamacpp",
        "march": "nash-e",
        "artifact": ".hbm / GGUF",
        "entries": S100P_LLM,
        "note": "S100 benchmarks are S100P proxy. S100 also supports hobot_llamacpp (GGUF).",
    },
    "x3": {
        "display": "RDK X3 (4GB)",
        "sdk": "hobot_llm (apt)",
        "runtime": "hobot-dnn",
        "march": "bernoulli2",
        "artifact": ".bin (Bloom tarball)",
        "entries": X3_LLM,
        "note": "X3 4GB only. Legacy path. Use hobot_llamacpp on X5/S100 for new projects.",
    },
}

ALIASES = {
    "sunrise3": "x3", "xj3": "x3", "j3": "x3", "rdkx3": "x3",
    "super100": "s100", "rdks100": "s100",
    "super100p": "s100p", "rdks100p": "s100p",
    "rdks600": "s600", "super600": "s600",
}


def normalize_board(raw: str) -> str | None:
    key = raw.strip().lower().replace("rdk_", "").replace("rdk-", "").replace(" ", "").replace("_", "")
    if key in BOARDS:
        return key
    return ALIASES.get(key)


def normalize_model(raw: str) -> str:
    return raw.strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def lookup(board: str, model: str | None) -> list[dict]:
    entry = BOARDS[board]
    if model is None:
        return entry["entries"]
    needle = normalize_model(model)
    matches = []
    for e in entry["entries"]:
        haystack = normalize_model(e["model"])
        if needle in haystack or haystack in needle:
            matches.append(e)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Look up on-device LLM benchmark data for RDK boards.")
    parser.add_argument("--board", help="Board name (s600/s100/s100p/x3)")
    parser.add_argument("--model", help="Model name (partial match, case-insensitive)")
    parser.add_argument("--text", action="store_true", help="Output human-readable text")
    args = parser.parse_args()

    if args.board is None:
        print(json.dumps({
            "boards": {k: {"display": v["display"], "sdk": v["sdk"],
                           "runtime": v["runtime"], "entries": len(v["entries"])}
                       for k, v in BOARDS.items()}
        }, indent=2, ensure_ascii=False))
        return 0

    board = normalize_board(args.board)
    if board is None:
        print(json.dumps({"error": f"Unknown board: {args.board!r}",
                          "known": list(BOARDS)}, ensure_ascii=False), file=sys.stderr)
        return 1

    results = lookup(board, args.model)
    if not results and args.model:
        print(json.dumps({"error": "model_not_found", "board": board, "query": args.model,
                          "available": sorted({e["model"] for e in BOARDS[board]["entries"]})},
                         ensure_ascii=False), file=sys.stderr)
        return 1

    output = {
        "board": board,
        "display": BOARDS[board]["display"],
        "sdk": BOARDS[board]["sdk"],
        "runtime": BOARDS[board]["runtime"],
        "march": BOARDS[board]["march"],
        "artifact": BOARDS[board]["artifact"],
        "note": BOARDS[board]["note"],
        "results": results,
    }

    if args.text:
        print(f"# {output['display']} — {output['sdk']}")
        print(f"# Runtime: {output['runtime']}, march: {output['march']}, artifact: {output['artifact']}")
        print(f"# {output['note']}")
        for r in results:
            print(f"  {r['model']} [{r.get('qtype', '?')}]")
            for k, v in r.items():
                if k != "model":
                    print(f"    {k}: {v}")
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
