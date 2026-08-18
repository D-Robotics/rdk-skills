#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026 D-Robotics. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# rdk-docs-reference: full-text search over the official D-Robotics doc repos
# (rdk_x_doc / rdk_s_doc / tros_doc). Read-only; results are file:line:matched-line.
#
# Usage:
#   search_docs.sh --query <kw> [--query <kw2> ...] [--repo x|s|tros|all] [--limit N]
#   search_docs.sh --query <kw> --summary          # hits grouped by doc chapter
#   search_docs.sh --toc [--query <kw>] [--repo x|s|tros|all]  # list/filter doc paths

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default docs root: <repo>/.refs ; override with RDK_DOCS_ROOT
DOCS_ROOT="${RDK_DOCS_ROOT:-$SCRIPT_DIR/../../../.refs}"

QUERIES=()
REPO=all
LIMIT=30
TOC=0
SUMMARY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --query)   QUERIES+=("${2:?--query requires a keyword}"); shift 2 ;;
    --repo)    REPO="${2:-all}"; shift 2 ;;
    --limit)   LIMIT="${2:-30}"; shift 2 ;;
    --toc)     TOC=1; shift ;;
    --summary) SUMMARY=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

repo_dirs() {
  case "$REPO" in
    x)   echo "$DOCS_ROOT/rdk_x_doc/docs" ;;
    s)   echo "$DOCS_ROOT/rdk_s_doc/docs" ;;
    tros) echo "$DOCS_ROOT/tros_doc/docs" ;;
    all) echo "$DOCS_ROOT/rdk_x_doc/docs $DOCS_ROOT/rdk_s_doc/docs $DOCS_ROOT/tros_doc/docs" ;;
    *) echo "invalid --repo '$REPO' (valid: x, s, tros, all)" >&2; exit 1 ;;
  esac
}

DIRS=""
for d in $(repo_dirs); do
  if [ -d "$d" ]; then
    DIRS="$DIRS $d"
  fi
done

if [ -z "$DIRS" ]; then
  echo "docs-not-found: no official doc clone under $DOCS_ROOT" >&2
  echo "Fetch them first:" >&2
  echo "  git clone --depth 1 https://github.com/D-Robotics/rdk_x_doc.git $DOCS_ROOT/rdk_x_doc" >&2
  echo "  git clone --depth 1 https://github.com/D-Robotics/rdk_s_doc.git $DOCS_ROOT/rdk_s_doc" >&2
  echo "  git clone --depth 1 https://github.com/D-Robotics/tros_doc.git $DOCS_ROOT/tros_doc" >&2
  exit 2
fi

if [ "$TOC" -eq 1 ]; then
  # With --query: filter doc paths by keyword (case-insensitive). This finds a
  # chapter by CAPABILITY name (e.g. "can" -> 09_mcu_can.md) even when the
  # artifact term (e.g. "can0") never appears in the target board's docs.
  # shellcheck disable=SC2086
  if [ "${#QUERIES[@]}" -gt 0 ]; then
    find $DIRS -name "*.md" | sed "s|$DOCS_ROOT/||" | grep -i -- "${QUERIES[0]}" | sort || true
  else
    find $DIRS -name "*.md" | sed "s|$DOCS_ROOT/||" | sort
  fi
  exit 0
fi

if [ "${#QUERIES[@]}" -eq 0 ]; then
  echo "usage: search_docs.sh --query <kw> [--query <kw2>] [--repo x|s|tros|all] [--limit N] | --toc" >&2
  exit 1
fi

# First keyword: full-text grep. Additional keywords: filter to files that
# contain ALL keywords (intersection), then show first-keyword hits in them.
FIRST="${QUERIES[0]}"

# shellcheck disable=SC2086
FILES="$(grep -ril --include="*.md" -- "$FIRST" $DIRS 2>/dev/null || true)"
for kw in "${QUERIES[@]:1}"; do
  [ -n "$FILES" ] || break
  FILES="$(printf '%s\n' "$FILES" | xargs -I{} grep -li -- "$kw" {} 2>/dev/null || true)"
done

if [ -z "$FILES" ]; then
  echo "no-match: keywords [${QUERIES[*]}] not found in $REPO docs."
  exit 0
fi

# --summary: group hit files by top-level doc chapter. The chapter path is an
# applicability signal (e.g. hits only under 05_mcu_development mean the term
# lives in the MCU domain, not the Linux userspace domain).
if [ "$SUMMARY" -eq 1 ]; then
  printf '%s\n' "$FILES" | sed "s|$DOCS_ROOT/||" \
    | awk -F/ '{ if (NF >= 5) print $1 "/" $3 "/" $4; else print $1 "/" $3 }' \
    | sort | uniq -c | sort -rn
  exit 0
fi

printf '%s\n' "$FILES" | while IFS= read -r f; do
  grep -in -- "$FIRST" "$f" 2>/dev/null | head -n 3 | while IFS= read -r line; do
    echo "${f#"$DOCS_ROOT"/}:$line"
  done
# awk (not head) for the global limit: head would close the pipe early and
# make the whole pipeline exit 141 under `set -o pipefail`.
done | awk -v n="$LIMIT" 'NR <= n'
