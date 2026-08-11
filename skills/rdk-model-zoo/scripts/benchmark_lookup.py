#!/usr/bin/env python3
"""Look up benchmark data for a Model Zoo model on a specific RDK board.

Returns structured JSON so the agent can cite exact latency/FPS/accuracy
numbers without parsing Markdown tables (anti-hallucination).

Usage:
    python3 benchmark_lookup.py --board x5 --model yolo11n
    python3 benchmark_lookup.py --board s100            # list all S100 models
    python3 benchmark_lookup.py                           # list all boards

Source of truth: references/per-board-model-catalog.md (verified appendix
snapshots from model_zoo_doc). Figures are official measurements and evolve
with firmware — treat them as a snapshot. Keep this in sync with the catalog
if the appendix updates.
"""
from __future__ import annotations

import argparse
import json
import sys

# ── S600 (Nash · .hbm) — LLM benchmark only in appendix ──────────────────────
S600 = [
    {"model": "DeepSeek-R1-Distill-Qwen-1.5B", "task": "llm", "qtype": "w4",
     "bpu_cores": "2/2", "max_context": 4096, "ttft_ms": 68.9, "tps": 92.4, "memory_gb": 2.2},
    {"model": "Qwen3-0.6B", "task": "llm", "qtype": "w8",
     "bpu_cores": "4/4", "max_context": 4096, "ttft_ms": 75.4, "tps": 92.9, "memory_gb": 3.0},
    {"model": "Qwen3-1.7B", "task": "llm", "qtype": "w4",
     "bpu_cores": "4/4", "max_context": 4096, "ttft_ms": 91.2, "tps": 75.0, "memory_gb": 3.7},
    {"model": "Qwen3-4B", "task": "llm", "qtype": "w4",
     "bpu_cores": "4/4", "max_context": 4096, "ttft_ms": 232.1, "tps": 45.8, "memory_gb": 6.6},
    {"model": "Qwen3-4B", "task": "llm", "qtype": "w8",
     "bpu_cores": "4/4", "max_context": 4096, "ttft_ms": 235.3, "tps": 32.3, "memory_gb": 8.3},
    {"model": "Qwen3-8B", "task": "llm", "qtype": "w4",
     "bpu_cores": "4/4", "max_context": 4096, "ttft_ms": 283.6, "tps": 31.4, "memory_gb": 9.1},
]

# ── S100 / S100P (Nash · .hbm) — 7 appendix chapters ─────────────────────────
S100 = [
    # Classification
    {"model": "EfficientNet_lite0", "task": "classification", "input": 224, "classes": 1000,
     "latency_ms": 0.448, "fps_single": 2107.8, "fps_dual": 4827.9},
    {"model": "EfficientNet_lite1", "task": "classification", "input": 240, "classes": 1000,
     "latency_ms": 0.489, "fps_single": 1949.0, "fps_dual": 4086.5},
    {"model": "MobileNetV2", "task": "classification", "input": 224, "classes": 1000,
     "latency_ms": 0.405, "fps_single": 2345.4, "fps_dual": 5026.5},
    {"model": "ResNet152", "task": "classification", "input": 224, "classes": 1000,
     "latency_ms": 2.131, "fps_single": 463.0, "fps_dual": 539.0},
    {"model": "YOLO11n-cls", "task": "classification", "input": 640, "classes": 80,
     "latency_ms": 0.53, "fps_single": 1827.9, "fps_dual": 3115.7},
    {"model": "YOLOv8n-cls", "task": "classification", "input": 640, "classes": 80,
     "latency_ms": 0.49, "fps_single": 1928.2, "fps_dual": 3399.9},
    {"model": "YOLO26n-cls", "task": "classification", "input": 224, "classes": 1000,
     "latency_ms": 0.56, "fps_single": 1659.7, "fps_dual": 3112.1},

    # Detection (representative: n/s/m/l/x tiers)
    {"model": "YOLO11n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 1.62, "fps_single": 596.5, "fps_dual": 813.9},
    {"model": "YOLO11s-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 2.63, "fps_single": 371.4, "fps_dual": 448.2},
    {"model": "YOLO11m-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 5.63, "fps_single": 175.7, "fps_dual": 191.6},
    {"model": "YOLO11l-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 6.96, "fps_single": 142.4, "fps_dual": 152.4},
    {"model": "YOLO11x-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 13.13, "fps_single": 75.8, "fps_dual": 78.8},
    {"model": "YOLOv8n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 1.53, "fps_single": 632.1, "fps_dual": 868.9},
    {"model": "YOLOv8s-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 2.63, "fps_single": 371.2, "fps_dual": 446.5},
    {"model": "YOLOv5nu-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 1.42, "fps_single": 674.9, "fps_dual": 959.1},
    {"model": "YOLOv9t-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 1.77, "fps_single": 546.0, "fps_dual": 730.7},
    {"model": "YOLOv10n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 1.58, "fps_single": 608.9, "fps_dual": 837.0},
    {"model": "YOLO26n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 1.70, "fps_single": 499.3, "fps_dual": 779.3},
    {"model": "YOLO12n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 2.65, "fps_single": 368.5, "fps_dual": 443.3},

    # Segmentation
    {"model": "YOLO11n-seg", "task": "segmentation", "input": 640, "classes": 80,
     "latency_ms": 2.06, "fps_single": 463.9, "fps_dual": None},
    {"model": "YOLOv8n-seg", "task": "segmentation", "input": 640, "classes": 80,
     "latency_ms": 1.93, "fps_single": 495.4, "fps_dual": None},

    # Pose
    {"model": "YOLO11n-pose", "task": "pose", "input": 640, "classes": 80,
     "latency_ms": 1.69, "fps_single": 568.0, "fps_dual": None},
    {"model": "YOLOv8n-pose", "task": "pose", "input": 640, "classes": 80,
     "latency_ms": 1.62, "fps_single": 587.6, "fps_dual": None},

    # OCR
    {"model": "PP-OCRv3_det", "task": "ocr", "input": "640x640",
     "latency_ms": 1.219, "fps_single": 798.6, "fps_dual": None},
    {"model": "PP-OCRv3_rec", "task": "ocr", "input": "48x320",
     "latency_ms": 2.588, "fps_single": 380.5, "fps_dual": None},

    # Depth
    {"model": "DepthAnythingV2", "task": "depth", "input": "518x518",
     "latency_ms": 137.4, "fps_single": 7.27, "fps_dual": None},

    # LLM (S100P benchmark)
    {"model": "DeepSeek-R1-Distill-Qwen-1.5B", "task": "llm", "qtype": "q4",
     "max_context": 1024, "ttft_ms": 108.0, "tps": 39.49, "memory_gb": 1.1},
    {"model": "DeepSeek-R1-Distill-Qwen-1.5B", "task": "llm", "qtype": "q4",
     "max_context": 4096, "ttft_ms": 224.0, "tps": 32.35, "memory_gb": 1.2},
    {"model": "DeepSeek-R1-Distill-Qwen-7B", "task": "llm", "qtype": "q8",
     "max_context": 1024, "ttft_ms": 544.0, "tps": 6.76, "memory_gb": 7.4},
    {"model": "InternLM2-1.8B", "task": "llm", "qtype": "q8",
     "max_context": 1024, "ttft_ms": 132.0, "tps": 23.83, "memory_gb": 1.8},
    {"model": "Qwen2.5-1.5B-Instruct", "task": "llm", "qtype": "q8",
     "max_context": 1024, "ttft_ms": 130.0, "tps": 24.40, "memory_gb": 1.8},
]

# ── X5 (Bayes-e · .bin) — 6 chapters, Float-vs-Quant accuracy ────────────────
X5 = [
    # Classification (representative)
    {"model": "edgenext-xxsmall", "task": "classification", "input": 256,
     "float_top1": 71.43, "quant_top1": 69.34, "latency_ms": 1.65, "fps_single": 2191, "fps_dual": None},
    {"model": "efficientnet-b0", "task": "classification", "input": 224,
     "float_top1": 77.55, "quant_top1": 75.08, "latency_ms": 4.67, "fps_single": 842, "fps_dual": None},
    {"model": "efficientnet-b4", "task": "classification", "input": 380,
     "float_top1": 82.27, "quant_top1": 80.55, "latency_ms": 18.52, "fps_single": 211, "fps_dual": None},
    {"model": "fasternet-t0", "task": "classification", "input": 224,
     "float_top1": 70.40, "quant_top1": 69.89, "latency_ms": 0.57, "fps_single": 1839, "fps_dual": None},
    {"model": "fastvit-t8", "task": "classification", "input": 256,
     "float_top1": 76.60, "quant_top1": 72.83, "latency_ms": 2.16, "fps_single": 1641, "fps_dual": None},
    {"model": "mobilenetv4-conv-small", "task": "classification", "input": 224,
     "float_top1": 77.24, "quant_top1": 75.32, "latency_ms": 1.88, "fps_single": 2035, "fps_dual": None},
    {"model": "repvit-m1_0", "task": "classification", "input": 224,
     "float_top1": 78.63, "quant_top1": 74.82, "latency_ms": 1.95, "fps_single": 1630, "fps_dual": None},
    {"model": "resnet18", "task": "classification", "input": 224,
     "float_top1": 71.49, "quant_top1": 70.50, "latency_ms": 8.87, "fps_single": 232.74, "fps_dual": None},

    # Detection (PyTorch AP vs Python AP)
    {"model": "yolo11n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 8.2, "fps_single": 122, "fps_dual": None, "ap_pytorch": 0.323, "ap_python": 0.308},
    {"model": "yolo11s-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 15.7, "fps_single": 63, "fps_dual": None, "ap_pytorch": 0.394, "ap_python": 0.380},
    {"model": "yolo11m-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 34.5, "fps_single": 29, "fps_dual": None, "ap_pytorch": 0.437, "ap_python": 0.422},
    {"model": "yolov8n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 7.0, "fps_single": 142, "fps_dual": None, "ap_pytorch": 0.306, "ap_python": 0.292},
    {"model": "yolov5nu-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 6.3, "fps_single": 157, "fps_dual": None, "ap_pytorch": 0.275, "ap_python": 0.260},
    {"model": "yolov9t-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 6.9, "fps_single": 144, "fps_dual": None, "ap_pytorch": 0.357, "ap_python": 0.346},
    {"model": "yolov10n-detect", "task": "detection", "input": 640, "classes": 80,
     "latency_ms": 8.7, "fps_single": 114, "fps_dual": None, "ap_pytorch": 0.387, "ap_python": 0.357},

    # Segmentation
    {"model": "yolo11n-seg", "task": "segmentation", "input": 640, "classes": 80,
     "latency_ms": 11.7, "fps_single": 85.6, "fps_dual": None},
    {"model": "yolov8n-seg", "task": "segmentation", "input": 640, "classes": 80,
     "latency_ms": 10.4, "fps_single": 96.0, "fps_dual": None},

    # Pose
    {"model": "yolo11n-pose", "task": "pose", "input": 640,
     "latency_ms": 8.3, "fps_single": 119.8, "fps_dual": None, "ap_pytorch": 0.465, "ap_python": 0.452},
    {"model": "yolov8n-pose", "task": "pose", "input": 640,
     "latency_ms": 7.0, "fps_single": 143.1, "fps_dual": None, "ap_pytorch": 0.476, "ap_python": 0.462},

    # OCR
    {"model": "PP-OCRv3_det", "task": "ocr", "input": "640x640",
     "latency_ms": None, "fps_single": 158.12, "fps_dual": None},
    {"model": "PP-OCRv3_rec", "task": "ocr", "input": "48x320",
     "latency_ms": None, "fps_single": 245.68, "fps_dual": None},

    # Matting
    {"model": "MODNet", "task": "matting", "input": "512x512",
     "latency_ms": 89.88, "fps_single": 11.12, "fps_dual": 15.27},
]

# ── X3 (Bernoulli2 · .bin) — 4 chapters, no pose/matting/depth/LLM ───────────
X3 = [
    # Classification
    {"model": "GoogLeNet", "task": "classification", "input": 224,
     "float_top1": 68.72, "quant_top1": 67.71, "latency_ms": 8.34, "fps_single": 243.51, "fps_dual": None},
    {"model": "MobileNetV2", "task": "classification", "input": 224,
     "float_top1": 72.0, "quant_top1": 68.17, "latency_ms": 2.41, "fps_single": 890.99, "fps_dual": None},
    {"model": "MobileNetV4", "task": "classification", "input": 224,
     "float_top1": 70.50, "quant_top1": 70.26, "latency_ms": 1.43, "fps_single": 1309.17, "fps_dual": None},
    {"model": "ResNet18", "task": "classification", "input": 224,
     "float_top1": 71.49, "quant_top1": 70.50, "latency_ms": 8.87, "fps_single": 232.74, "fps_dual": None},
    {"model": "RepVGG", "task": "classification", "input": 224,
     "float_top1": 74.46, "quant_top1": 62.78, "latency_ms": 11.58, "fps_single": 174.94, "fps_dual": None},

    # Detection
    {"model": "YOLOv5s_v2.0", "task": "detection", "input": 640,
     "latency_ms": None, "fps_single": 38.2, "fps_dual": None},
    {"model": "YOLOv5n_v7.0", "task": "detection", "input": 640,
     "latency_ms": None, "fps_single": 37.2, "fps_dual": None},
    {"model": "YOLOv8n", "task": "detection", "input": 640,
     "latency_ms": None, "fps_single": 34.1, "fps_dual": None},
    {"model": "YOLOv10n", "task": "detection", "input": 640,
     "latency_ms": None, "fps_single": 18.1, "fps_dual": None},
    {"model": "FCOS", "task": "detection", "input": 512,
     "latency_ms": None, "fps_single": 173.9, "fps_dual": None},

    # Segmentation
    {"model": "YOLOv8n-seg", "task": "segmentation", "input": 640,
     "latency_ms": None, "fps_single": 27.3, "fps_dual": None},

    # OCR
    {"model": "PP-OCRv3_det", "task": "ocr", "input": "640x640",
     "latency_ms": None, "fps_single": 41.96, "fps_dual": None},
    {"model": "PP-OCRv3_rec", "task": "ocr", "input": "48x320",
     "latency_ms": None, "fps_single": 78.92, "fps_dual": None},
]

# ── Board registry ──────────────────────────────────────────────────────────
BOARDS = {
    "s600": {"display": "RDK S600", "bpu_arch": "Nash", "artifact": ".hbm", "entries": S600,
              "note": "Appendix has LLM benchmark only. Vision/speech samples on rdk_s branch."},
    "s100": {"display": "RDK S100", "bpu_arch": "Nash", "artifact": ".hbm", "entries": S100,
              "note": "S100P generally faster. 7 appendix chapters incl. LLM."},
    "s100p": {"display": "RDK S100P", "bpu_arch": "Nash", "artifact": ".hbm", "entries": S100,
               "note": "Same rdk_s branch. LLM benchmarks are S100P measurements."},
    "x5": {"display": "RDK X5", "bpu_arch": "Bayes-e", "artifact": ".bin", "entries": X5,
            "note": "Float-vs-Quant and PyTorch-vs-Python AP for quantization drop analysis."},
    "x3": {"display": "RDK X3", "bpu_arch": "Bernoulli2", "artifact": ".bin", "entries": X3,
            "note": "Uses demos/ (not samples/). No pose/matting/depth/LLM."},
}

ALIASES = {
    "sunrise3": "x3", "xj3": "x3", "j3": "x3", "rdkx3": "x3",
    "sunrise5": "x5", "rdkx5": "x5",
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
        description="Look up Model Zoo benchmark data for a board + model.")
    parser.add_argument("--board", help="Board name (x3/x5/s100/s100p/s600)")
    parser.add_argument("--model", help="Model name (partial match, case-insensitive)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON (default)")
    parser.add_argument("--text", action="store_true", help="Output human-readable text")
    args = parser.parse_args()

    if args.board is None:
        # List all boards
        print(json.dumps({
            "boards": {k: {"display": v["display"], "bpu_arch": v["bpu_arch"],
                           "artifact": v["artifact"], "entries": len(v["entries"])}
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
        "bpu_arch": BOARDS[board]["bpu_arch"],
        "artifact": BOARDS[board]["artifact"],
        "note": BOARDS[board]["note"],
        "results": results,
    }

    if args.text:
        print(f"# {output['display']} ({output['bpu_arch']}, {output['artifact']})")
        print(f"# {output['note']}")
        for r in results:
            print(f"  {r['model']} [{r.get('task', '?')}]")
            for k, v in r.items():
                if k != "model":
                    print(f"    {k}: {v}")
    else:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
