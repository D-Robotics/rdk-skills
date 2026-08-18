"""Search the generated RDK Skill catalog deterministically."""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = 1
REQUIRED_RECORD_FIELDS = (
    "name",
    "description",
    "pack",
    "repo",
    "catalog_path",
    "install_type",
)
ASCII_TOKEN = re.compile(r"[A-Za-z0-9]+")
CJK_TOKEN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")
NORMALIZED_TOKEN = re.compile(r"[A-Za-z0-9]+|[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+")


def tokens(text: str) -> set[str]:
    """Return the fixed ASCII and Chinese tokens used for matching."""
    result = {match.group().casefold() for match in ASCII_TOKEN.finditer(text)}
    for match in CJK_TOKEN.finditer(text):
        segment = match.group()
        result.add(segment)
        result.update(segment[index : index + 2] for index in range(len(segment) - 1))
    return result


def normalized(text: str) -> str:
    """Create the canonical comparable form used by exact-name scoring."""
    return " ".join(match.group().casefold() for match in NORMALIZED_TOKEN.finditer(text))


def validate_index(index: Any) -> dict[str, Any]:
    """Validate the generated index before any search result is returned."""
    errors = []
    if not isinstance(index, dict):
        raise ValueError("index must be a JSON object")
    schema_version = index.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != SCHEMA_VERSION
    ):
        errors.append(f"unsupported schema_version: {schema_version!r}")
    records = index.get("skills")
    if not isinstance(records, list):
        errors.append("skills must be an array")
    elif not records:
        errors.append("skills must be a non-empty array")
    else:
        for record_index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"skills[{record_index}] must be an object")
                continue
            for field in REQUIRED_RECORD_FIELDS:
                if not isinstance(record.get(field), str) or not record[field]:
                    errors.append(
                        f"skills[{record_index}].{field} must be a non-empty string"
                    )
            if record.get("install_type") not in {"flat", "workspace"}:
                errors.append(
                    f"skills[{record_index}].install_type must be flat or workspace"
                )
    if errors:
        raise ValueError("; ".join(errors))
    return index


def _record_tokens(record: dict[str, str], fields: tuple[str, ...]) -> set[str]:
    return set().union(*(tokens(record[field]) for field in fields))


def _action(record: dict[str, str]) -> str:
    if record["install_type"] == "workspace":
        return "use rdk-pack-installer"
    return f"npx skills add d-robotics/rdk-skills --skill {record['name']}"


def search(
    index: dict[str, Any],
    query: str,
    *,
    pack: str | None = None,
    platform: str | None = None,
    install_type: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    """Return matching catalog records with stable scoring and actions."""
    validate_index(index)
    query_tokens = tokens(query)
    query_normalized = normalized(query)
    platform_tokens = tokens(platform) if platform else set()
    matches = []

    for record in index["skills"]:
        if pack is not None and record["pack"].casefold() != pack.casefold():
            continue
        if install_type is not None and record["install_type"] != install_type:
            continue
        searchable_tokens = _record_tokens(
            record, ("name", "description", "pack", "catalog_path")
        )
        if platform_tokens and not platform_tokens.issubset(searchable_tokens):
            continue

        name_tokens = tokens(record["name"])
        description_tokens = tokens(record["description"])
        score = 100 if query_normalized == normalized(record["name"]) else 0
        score += 10 * len(query_tokens & name_tokens)
        score += 3 * len(query_tokens & description_tokens)
        if score == 0:
            continue

        matches.append(
            {
                **{field: record[field] for field in REQUIRED_RECORD_FIELDS},
                "score": score,
                "action": _action(record),
            }
        )

    matches.sort(key=lambda match: (-match["score"], match["name"]))
    if limit is not None:
        matches = matches[:limit]
    return {
        "query": query,
        "matches": matches,
        "fallback": None if matches else "rdk-docs-reference",
    }


def load_index(path: Path) -> dict[str, Any]:
    """Load and validate a generated catalog index."""
    with path.open(encoding="utf-8") as index_file:
        return validate_index(json.load(index_file))


def write_json(payload: dict[str, Any]) -> None:
    """Write CLI JSON as UTF-8 independently of the console code page."""
    sys.stdout.buffer.write(
        (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", metavar="QUERY")
    parser.add_argument("--pack")
    parser.add_argument("--platform")
    parser.add_argument("--install-type", choices=("flat", "workspace"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be zero or greater")

    default_index = Path(__file__).resolve().parents[1] / "references" / "skill-index.json"
    index_path = Path(os.environ.get("RDK_SKILL_INDEX", default_index))
    try:
        result = search(
            load_index(index_path),
            args.query,
            pack=args.pack,
            platform=args.platform,
            install_type=args.install_type,
            limit=args.limit,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        write_json({"error": str(error), "matches": [], "fallback": None})
        return 1
    write_json(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
