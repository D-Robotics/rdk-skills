#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
"""Search local X5 OpenExplorer documentation."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

DOC_DIRECTORY_NAME = "x5_doc-v1.2.8-py310-cn"
SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills"
DEFAULT_X5_BPU_PYAPI_DOC = SKILL_ROOT / "x5-bpu-python-api/references/x5_bpu_pyapi.md"
PYTHON_API_DOC_ROUTE = "/local-python-api/x5-bpu"
PYTHON_API_DOC_TITLE = "X5 BPU Python API (hbm_runtime)"
X5_QUERY_ALIASES = {
    "ptq": ("hb_mapper", "makertbin", "calibration"),
    "qat": ("horizon_plugin_pytorch", "quantization"),
    "编译": ("makertbin",),
    "量化": ("ptq", "makertbin", "calibration"),
    "模型检查": ("hb_mapper", "checker"),
}


def configure_text_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")
        except (AttributeError, OSError, ValueError):
            pass


def first_configured_env(*names: str) -> str | None:
    return next((value for name in names if (value := os.environ.get(name))), None)


def doc_root_candidates(value: str | None) -> list[Path]:
    configured: list[str] = []
    if value:
        configured.append(value)
    else:
        found = first_configured_env("OE_DROBOTICS_DOC_ROOT", "OE_X_SERIES_DOC_ROOT")
        if found:
            configured.append(found)

    candidates = [Path(item).expanduser() for item in configured]
    anchors = [Path.cwd(), *Path(__file__).resolve().parents]
    for anchor in anchors:
        candidates.extend(
            (
                anchor / DOC_DIRECTORY_NAME,
                anchor / "docs" / DOC_DIRECTORY_NAME,
                anchor / ".drobotics" / "manuals" / DOC_DIRECTORY_NAME,
            )
        )

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        key = str(resolved).lower()
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def resolve_doc_root(value: str | None) -> Path:
    candidates = doc_root_candidates(value)
    for root in candidates:
        if root.is_dir():
            return root
    checked = ", ".join(str(path) for path in candidates) or "<none>"
    raise FileNotFoundError(
        f"Local X5 documentation root was not found. Checked: {checked}. "
        "Set OE_DROBOTICS_DOC_ROOT or pass --root."
    )


def resolve_python_api_doc(value: str | None) -> Path:
    configured = value or first_configured_env("OE_DROBOTICS_BPU_PYAPI_DOC")
    document = Path(configured).expanduser() if configured else DEFAULT_X5_BPU_PYAPI_DOC

    if not document.is_file():
        raise FileNotFoundError(
            f"Local X5 BPU Python API document does not exist: {document}. "
            "Set OE_DROBOTICS_BPU_PYAPI_DOC or pass --python-api-doc."
        )
    return document


def load_docusaurus_index(root: Path, language: str) -> list[dict[str, Any]]:
    candidates = sorted((root / "static").glob(f"search_index.{language}.*.json"))
    if not candidates:
        return []
    data = json.loads(candidates[-1].read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Unexpected search index format: {candidates[-1]}")
    return [entry for entry in data if isinstance(entry, dict)]


def source_title(content: str, fallback: str) -> str:
    lines = [line.strip() for line in content.splitlines()]
    for index, line in enumerate(lines[:-1]):
        underline = lines[index + 1]
        if line and len(underline) >= len(line) and set(underline) <= {"=", "-", "~", "^", '"', "'", "`"}:
            return line
    first_line = next((line for line in lines if line), fallback)
    return first_line.lstrip("#").strip() or fallback


def source_document_name(source_root: Path, source_path: Path) -> str:
    relative = source_path.relative_to(source_root).as_posix()
    for suffix in (".rst.txt", ".md.txt", ".ipynb.txt"):
        if relative.endswith(suffix):
            return relative[: -len(suffix)]
    raise ValueError(f"Unsupported source filename: {source_path}")


def source_content(source_path: Path) -> str:
    raw_content = source_path.read_text(encoding="utf-8", errors="replace")
    if not source_path.name.endswith(".ipynb.txt"):
        return raw_content

    try:
        notebook = json.loads(raw_content)
    except json.JSONDecodeError:
        return raw_content

    cells = notebook.get("cells")
    if not isinstance(cells, list):
        return raw_content

    fragments: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        cell_source = cell.get("source", "")
        if isinstance(cell_source, list):
            fragments.append("".join(str(line) for line in cell_source))
        elif isinstance(cell_source, str):
            fragments.append(cell_source)
    return "\n".join(fragments) or raw_content


def load_sphinx_source_index(root: Path) -> list[dict[str, Any]]:
    source_root = root / "_sources"
    if not source_root.is_dir():
        return []

    source_files = sorted(
        source_path
        for pattern in ("*.rst.txt", "*.md.txt", "*.ipynb.txt")
        for source_path in source_root.rglob(pattern)
    )
    entries: list[dict[str, Any]] = []
    for source_path in source_files:
        content = source_content(source_path)
        document = source_document_name(source_root, source_path)
        entries.append(
            {
                "title": source_title(content, document),
                "content": content,
                "routePath": f"/{document}.html",
                "source_path": str(source_path),
            }
        )
    return entries


def load_index(root: Path, language: str) -> list[dict[str, Any]]:
    docusaurus_entries = load_docusaurus_index(root, language)
    if docusaurus_entries:
        return docusaurus_entries

    sphinx_entries = load_sphinx_source_index(root)
    if sphinx_entries:
        return sphinx_entries

    raise FileNotFoundError(
        f"No supported local documentation index found under {root}. Expected a Docusaurus "
        "static/search_index.*.json file or a Sphinx _sources directory."
    )


def load_platform_index(
    root: Path,
    language: str,
    python_api_doc: Path | None = None,
) -> list[dict[str, Any]]:
    entries = load_index(root, language)
    # Filter out HAT entries — not applicable to X5
    entries = [
        entry
        for entry in entries
        if not str(entry.get("routePath", "")).lower().startswith("/hat/")
    ]

    document = python_api_doc or resolve_python_api_doc(None)
    content = document.read_text(encoding="utf-8", errors="replace")
    entries.append(
        {
            "title": PYTHON_API_DOC_TITLE,
            "content": content,
            "routePath": PYTHON_API_DOC_ROUTE,
            "source_path": str(document),
            "local_path": str(document),
        }
    )
    return entries


def terms(query: str) -> list[str]:
    query_terms = [term.lower() for term in re.split(r"\s+", query.strip()) if term]
    if len(query_terms) > 1:
        query_terms = [term for term in query_terms if term != "x5"]
    expanded = list(query_terms)
    for term in query_terms:
        expanded.extend(X5_QUERY_ALIASES.get(term, ()))
    return list(dict.fromkeys(expanded))


def score(entry: dict[str, Any], query_terms: list[str]) -> int:
    title = str(entry.get("title", "")).lower()
    content = str(entry.get("content", "")).lower()
    route = str(entry.get("routePath", "")).lower()
    total = 0
    for term in query_terms:
        total += title.count(term) * 12
        total += route.count(term) * 6
        total += content.count(term)
    return total


def excerpt(content: str, query_terms: list[str], width: int = 280) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    lower = compact.lower()
    positions = [lower.find(term) for term in query_terms if lower.find(term) >= 0]
    start = max(0, min(positions) - width // 3) if positions else 0
    result = compact[start : start + width]
    if start > 0:
        result = "…" + result
    if start + width < len(compact):
        result += "…"
    return result


def local_html_path(root: Path, route: str) -> Path:
    relative = route.lstrip("/")
    if not relative.endswith(".html"):
        relative += ".html"
    return root / relative


def main() -> int:
    configure_text_output()
    parser = argparse.ArgumentParser(description="Search local X5 OpenExplorer documentation")
    parser.add_argument("--query", required=True, help="Keywords or a natural-language question")
    parser.add_argument("--root", help="Local documentation root; overrides OE_DROBOTICS_DOC_ROOT")
    parser.add_argument(
        "--python-api-doc",
        help="Override the standalone X5 hbm_runtime Python API Markdown for this query.",
    )
    parser.add_argument("--lang", choices=("zh", "en"), default="zh")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of formatted text")
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    root = resolve_doc_root(args.root)
    query_terms = terms(args.query)
    if not query_terms:
        parser.error("--query must contain at least one term")

    python_api_doc = resolve_python_api_doc(args.python_api_doc)

    ranked = []
    for entry in load_platform_index(root, args.lang, python_api_doc):
        entry_score = score(entry, query_terms)
        if entry_score <= 0:
            continue
        route = str(entry.get("routePath", ""))
        ranked.append(
            {
                "score": entry_score,
                "title": str(entry.get("title", "")),
                "route": route,
                "html_path": str(entry.get("local_path") or local_html_path(root, route)),
                "source_path": str(entry.get("source_path", "")),
                "excerpt": excerpt(str(entry.get("content", "")), query_terms),
            }
        )

    ranked.sort(key=lambda item: (-item["score"], item["title"]))
    results = ranked[: args.limit]
    if args.json:
        print(json.dumps({"platform": "x5", "root": str(root), "results": results}, ensure_ascii=False, indent=2))
        return 0

    if not results:
        print(f"No local documentation results for: {args.query}")
        return 1

    for index, result in enumerate(results, 1):
        print(f"[{index}] {result['title']} (score={result['score']})")
        print(f"route: {result['route']}")
        print(f"file:  {result['html_path']}")
        if result["source_path"]:
            print(f"source:{result['source_path']}")
        print(f"excerpt: {result['excerpt']}\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
