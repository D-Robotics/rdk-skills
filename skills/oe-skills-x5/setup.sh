#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
#
# X5 Workspace initialization script.
#
# Usage: bash setup.sh [--update] [--force] [--ref <tag>] <project-root>
#
# --update  Rebuild only when the installed VERSION differs.
# --force   With --update, rebuild even when versions match.
# --ref     Installation anchor (for example v1.0.0), recorded in
#           .drobotics/INSTALLED_REF. Defaults to the source VERSION.

set -euo pipefail

RESOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
UPDATE=0
FORCE=0
PROVIDED_REF=""
PROJECT_ARGUMENT=""

usage() {
  echo "Usage: bash setup.sh [--update] [--force] [--ref <tag>] <project-root>" >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --update)
      UPDATE=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --ref)
      if [ -z "${2:-}" ]; then
        echo "ERROR: --ref 需要一个参数（如 v1.0.0）" >&2
        exit 2
      fi
      PROVIDED_REF="$2"
      shift 2
      ;;
    --*)
      echo "ERROR: 未知参数: $1" >&2
      usage
      exit 2
      ;;
    *)
      if [ -z "$PROJECT_ARGUMENT" ]; then
        PROJECT_ARGUMENT="$1"
        shift
      else
        echo "ERROR: 未知参数: $1" >&2
        usage
        exit 2
      fi
      ;;
  esac
done

if [ -z "$PROJECT_ARGUMENT" ]; then
  echo "ERROR: project root is required" >&2
  usage
  exit 1
fi

if ! PROJECT_ROOT="$(cd "$PROJECT_ARGUMENT" 2>/dev/null && pwd)"; then
  echo "ERROR: project directory does not exist or is inaccessible: $PROJECT_ARGUMENT" >&2
  exit 1
fi

if [ -d "$RESOURCE_DIR/x5" ]; then
  DROBOTICS_SRC="$RESOURCE_DIR/x5"
else
  DROBOTICS_SRC="$RESOURCE_DIR"
fi
DROBOTICS_DST="$PROJECT_ROOT/.drobotics"

if [ ! -d "$DROBOTICS_SRC" ]; then
  echo "ERROR: resource directory not found: $DROBOTICS_SRC" >&2
  exit 1
fi

SRC_VERSION="$(tr -d '\r' < "$DROBOTICS_SRC/VERSION" 2>/dev/null || true)"
INSTALLED_VERSION="$(tr -d '\r' < "$DROBOTICS_DST/VERSION" 2>/dev/null || true)"

echo "==> Resource:  $RESOURCE_DIR"
echo "==> Project:   $PROJECT_ROOT"
echo "==> Target:    $DROBOTICS_DST"

if [ "$UPDATE" -eq 1 ]; then
  if [ -n "$INSTALLED_VERSION" ] && [ "$INSTALLED_VERSION" = "$SRC_VERSION" ] && [ "$FORCE" -eq 0 ]; then
    echo "==> Already up to date ($INSTALLED_VERSION). Use --force to rebuild."
    exit 0
  fi
  if [ -n "$INSTALLED_VERSION" ]; then
    echo "==> Upgrade: $INSTALLED_VERSION -> $SRC_VERSION (rebuild, no stale files)"
  elif [ -e "$DROBOTICS_DST" ]; then
    echo "==> Existing workspace without VERSION record; --update rebuilds it"
  else
    echo "==> Fresh install (--update behaves like a normal install)"
  fi
  rm -rf "$DROBOTICS_DST"
fi

mkdir -p "$DROBOTICS_DST"

copy_directory() {
  local directory="$1"
  if [ -d "$DROBOTICS_SRC/$directory" ]; then
    mkdir -p "$DROBOTICS_DST/$directory"
    cp -R "$DROBOTICS_SRC/$directory/." "$DROBOTICS_DST/$directory/"
    echo "  [ok] $directory/"
  else
    echo "  [WARN] $directory/ resource directory is missing; skipped" >&2
  fi
}

copy_directory docs
copy_directory platforms
copy_directory scripts
copy_directory skills

if [ -d "$DROBOTICS_DST/skills" ]; then
  while IFS= read -r eval_file; do
    rm -rf "$(dirname "$eval_file")"
  done < <(find "$DROBOTICS_DST/skills" -path "*/test/eval.json" -type f 2>/dev/null)
  SKILL_COUNT="$(find "$DROBOTICS_DST/skills" -name SKILL.md -type f | wc -l | tr -d ' ')"
  echo "  [ok] skills/ ($SKILL_COUNT skills)"
fi

for file in X5.md skill-index.json VERSION; do
  if [ -f "$DROBOTICS_SRC/$file" ]; then
    cp "$DROBOTICS_SRC/$file" "$DROBOTICS_DST/$file"
    echo "  [ok] $file"
  else
    echo "  [WARN] $file is missing; skipped" >&2
  fi
done

RESOLVED_REF="${PROVIDED_REF:-${SRC_VERSION:-unknown}}"
printf '%s\n' "$RESOLVED_REF" > "$DROBOTICS_DST/INSTALLED_REF"
echo "  [ok] INSTALLED_REF ($RESOLVED_REF)"

MARKER='# X5 Workspace Rules'
ROUTING_RULES="$MARKER

If the user request involves X5 OpenExplorer related topics
(quantization, compile, deploy, evaluation, training, CLI usage, version issues),
you MUST follow the project rules defined in .drobotics/X5.md.

For X5 OpenExplorer related tasks:
- Do NOT guess toolchain APIs or CLI parameters based on general LLM knowledge.
- If uncertain, use .drobotics/scripts/search_local_docs.py to retrieve local documentation before answering."

for file in CLAUDE.md AGENTS.md; do
  target="$PROJECT_ROOT/$file"
  if [ -f "$target" ] && ! grep -q "$MARKER" "$target"; then
    printf '%s\n\n%s\n' "$ROUTING_RULES" "$(cat "$target")" > "$target"
    echo "  [ok] $file (injected)"
  fi
done

ERRORS=0
for file in \
  X5.md skill-index.json VERSION INSTALLED_REF \
  docs/offline-artifact-delivery.md \
  scripts/search_local_docs.py \
  scripts/validate_x5_skills.py \
  scripts/check_bpu_python_api_version.py \
  scripts/validate_bpu_python_api_skills.py \
  scripts/release_artifacts.py \
  scripts/validate_release_artifacts.py \
  platforms/x5/PACK.md \
  platforms/x5/skill-index.json \
  platforms/x5/evals/cases.yaml \
  platforms/x5/schemas/route.schema.json \
  platforms/x5/schemas/plan.schema.json \
  platforms/x5/schemas/artifacts.schema.json \
  platforms/x5/schemas/verification.schema.json \
  platforms/x5/scripts/run_contract.py \
  platforms/x5/scripts/run_ptq.py \
  platforms/x5/assets/runtime-cpp/main.cc \
  skills/x5-router/SKILL.md \
  skills/x5-bpu-python-api/SKILL.md \
  skills/x5-bpu-python-api/references/x5_bpu_pyapi.md; do
  if [ ! -f "$DROBOTICS_DST/$file" ]; then
    echo "  [FAIL] missing $file" >&2
    ERRORS=$((ERRORS + 1))
  fi
done

if [ ! -d "$DROBOTICS_DST/platforms" ]; then
  echo "  [FAIL] missing platforms/" >&2
  ERRORS=$((ERRORS + 1))
fi

DROBOTICS_SKILL_COUNT="$(find "$DROBOTICS_DST/skills" -name SKILL.md -type f 2>/dev/null | wc -l | tr -d ' ')"
if [ "$DROBOTICS_SKILL_COUNT" -ne 22 ]; then
  echo "  [FAIL] expected 22 X5 Skills, found $DROBOTICS_SKILL_COUNT" >&2
  ERRORS=$((ERRORS + 1))
fi

if [ "$ERRORS" -gt 0 ]; then
  echo "==> Installation completed with $ERRORS problem(s)." >&2
  exit 1
fi

echo "==> Done. .drobotics/ initialized at $DROBOTICS_DST"
