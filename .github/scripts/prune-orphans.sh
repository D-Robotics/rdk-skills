#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
#
# Prune orphaned skill directories — top-level skills/ dirs that have no
# corresponding components.d registration and are not listed in
# catalog-exceptions.yml.
#
# Called by the sync-skills workflow after all component rsyncs are done.
#
# Safety:
#   - Skipped entirely if any components.d file fails to parse.
#   - Refuses to act (flags for human triage) if more than 5 dirs would
#     be removed at once.
#   - Dirs listed in catalog-exceptions.yml are always preserved.

set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

CONFIG=/tmp/components.aggregated.yml

# If no aggregated config, try to build it.
if [ ! -f "$CONFIG" ]; then
  if ! yq ea '[.] | {"components": .}' components.d/*.yml > "$CONFIG" 2>/dev/null; then
    echo "prune-orphans: FAILED to parse components.d — skipping prune entirely"
    exit 0
  fi
fi

# Collect all registered catalog_dirs.
registered_dirs=$(mktemp)
yq -r '.components[].skills[].catalog_dir' "$CONFIG" 2>/dev/null | sort > "$registered_dirs"

# Collect exception dirs.
exception_dirs=$(mktemp)
if [ -f catalog-exceptions.yml ]; then
  yq -r '.exceptions[].dir' catalog-exceptions.yml 2>/dev/null | sort > "$exception_dirs"
fi

# Find orphaned dirs.
orphans=$(mktemp)
if [ -d skills ]; then
  for d in skills/*/; do
    [ -d "$d" ] || continue
    dirname=$(basename "$d")
    # Skip .gitkeep or hidden files
    [ "$dirname" = ".gitkeep" ] && continue
    if ! grep -qx "$dirname" "$registered_dirs" && ! grep -qx "$dirname" "$exception_dirs"; then
      echo "$dirname" >> "$orphans"
    fi
  done
fi

orphan_count=$(wc -l < "$orphans" | tr -d ' ')

if [ "$orphan_count" -eq 0 ]; then
  echo "prune-orphans: no orphans found — catalog is clean"
  rm -f "$registered_dirs" "$exception_dirs" "$orphans"
  exit 0
fi

if [ "$orphan_count" -gt 5 ]; then
  echo "prune-orphans: REFUSING to prune $orphan_count orphans (>5 threshold) — flagging for human triage:"
  cat "$orphans"
  rm -f "$registered_dirs" "$exception_dirs" "$orphans"
  exit 1
fi

echo "prune-orphans: removing $orphan_count orphaned skill dir(s):"
truncate -s 0 /tmp/pruned-orphans.txt 2>/dev/null || : > /tmp/pruned-orphans.txt
while read -r dirname; do
  echo "  - $dirname"
  rm -rf "skills/$dirname"
  echo "$dirname" >> /tmp/pruned-orphans.txt
done < "$orphans"

rm -f "$registered_dirs" "$exception_dirs" "$orphans"
