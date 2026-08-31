#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

# Synchronize one registered component without touching other catalog trees.
set -euo pipefail

usage() {
  echo "usage: $0 --components-dir DIR --component ID --repo-base-url URL --work-root DIR --summary-file FILE" >&2
  exit 2
}

components_dir=
component_id=
repo_base_url=
work_root=
summary_file=
fail_after_replace=${SYNC_COMPONENTS_FAIL_AFTER_REPLACE:-}
pause_after_replace=${SYNC_COMPONENTS_PAUSE_AFTER_REPLACE:-}
pause_after_backup=${SYNC_COMPONENTS_PAUSE_AFTER_BACKUP:-}
fail_backup=${SYNC_COMPONENTS_FAIL_BACKUP:-}
ready_file=${SYNC_COMPONENTS_READY_FILE:-}
fail_compare=${SYNC_COMPONENTS_FAIL_COMPARE:-}
python_bin=${PYTHON_BIN:-python3}
while [[ $# -gt 0 ]]; do
  case "$1" in
    --components-dir) components_dir=${2:-}; shift 2 ;;
    --component) component_id=${2:-}; shift 2 ;;
    --repo-base-url) repo_base_url=${2:-}; shift 2 ;;
    --work-root) work_root=${2:-}; shift 2 ;;
    --summary-file) summary_file=${2:-}; shift 2 ;;
    --fail-after-replace) fail_after_replace=${2:-}; shift 2 ;;
    --pause-after-replace) pause_after_replace=${2:-}; shift 2 ;;
    --pause-after-backup) pause_after_backup=${2:-}; shift 2 ;;
    --fail-backup) fail_backup=true; shift ;;
    --ready-file) ready_file=${2:-}; shift 2 ;;
    --fail-compare) fail_compare=${2:-}; shift 2 ;;
    *) usage ;;
  esac
done

[[ -n "$components_dir" && -n "$component_id" && -n "$repo_base_url" && -n "$work_root" && -n "$summary_file" ]] || usage
[[ "$component_id" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "invalid component id: $component_id" >&2; exit 2; }
[[ -d "$components_dir" ]] || { echo "components directory does not exist: $components_dir" >&2; exit 2; }
[[ -d "$(dirname "$summary_file")" ]] || { echo "invalid summary destination: $summary_file" >&2; exit 2; }
[[ ! -d "$summary_file" ]] || { echo "invalid summary destination: $summary_file" >&2; exit 2; }
touch "$summary_file" 2>/dev/null || { echo "invalid summary destination: $summary_file" >&2; exit 2; }

# A cleanup target must be a newly-created child of this checkout's .tmp/
# namespace.  In particular, never accept an existing directory or skills/.
hub_root=$(realpath -m .)
work_root=$(realpath -m "$work_root")
allowed_tmp="$hub_root/.tmp"
case "$work_root" in "$allowed_tmp"/component-sync|"$allowed_tmp"/component-sync-*) ;; *)
  echo "unsafe work root: $work_root" >&2; exit 2 ;;
esac
[[ ! -e "$work_root" ]] || { echo "unsafe work root already exists: $work_root" >&2; exit 2; }

component_file="$components_dir/$component_id.yml"
[[ -f "$component_file" ]] || { echo "unknown component: $component_id" >&2; exit 2; }

config=$($python_bin - "$component_file" <<'PY'
import json
import re
import sys
from pathlib import PurePosixPath

import yaml

path = sys.argv[1]
try:
    data = yaml.safe_load(open(path, encoding="utf-8"))
except (OSError, yaml.YAMLError) as error:
    raise SystemExit(f"invalid component YAML: {path}: {error}")
if not isinstance(data, dict):
    raise SystemExit("component YAML must be a mapping")

def text(name, default=None):
    value = data.get(name, default)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"component {name} is required")
    return value

def safe_source(value):
    if not isinstance(value, str) or not value:
        raise SystemExit(f"unsafe source path: {value}")
    parsed = PurePosixPath(value)
    if value.startswith("/") or "\\" in value or ".." in parsed.parts or str(parsed) in ("", "."):
        raise SystemExit(f"unsafe source path: {value}")
    return str(parsed)

def safe_catalog(value):
    if not isinstance(value, str) or not value or "/" in value or "\\" in value or value in (".", ".."):
        raise SystemExit(f"unsafe catalog path: {value}")
    return value

skills = data.get("skills")
if not isinstance(skills, list) or not skills:
    raise SystemExit("component skills must be a non-empty list")
entries = []
for skill in skills:
    if not isinstance(skill, dict):
        raise SystemExit("component skill entry must be a mapping")
    entries.append({"path": safe_source(skill.get("path")), "catalog_dir": safe_catalog(skill.get("catalog_dir"))})
catalog_dirs = [entry["catalog_dir"] for entry in entries]
if len(catalog_dirs) != len(set(catalog_dirs)):
    raise SystemExit("component catalog directories must be unique")

install_type = data.get("install_type", "")
install_script = data.get("install_script", "")
if install_type == "workspace":
    if len(entries) != 1 or not isinstance(install_script, str) or not install_script:
        raise SystemExit("workspace component requires one skill and an install script")
    install_script = safe_source(install_script)
elif install_type:
    raise SystemExit(f"unsupported install type: {install_type}")

repo = text("repo")
if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo) is None:
    raise SystemExit(f"unsafe component repository: {repo}")

print(json.dumps({
    "repo": repo, "ref": text("ref", "main"), "skills": entries,
    "install_type": install_type, "install_script": install_script,
}))
PY
)

repo=$($python_bin -c 'import json,sys; print(json.load(sys.stdin)["repo"])' <<<"$config")
source_ref=$($python_bin -c 'import json,sys; print(json.load(sys.stdin)["ref"])' <<<"$config")
install_type=$($python_bin -c 'import json,sys; print(json.load(sys.stdin)["install_type"])' <<<"$config")
install_script=$($python_bin -c 'import json,sys; print(json.load(sys.stdin)["install_script"])' <<<"$config")

source_sha=""
changed=false
failure=""
catalog_dirs=$($python_bin -c 'import json,sys; print("\n".join(x["catalog_dir"] for x in json.load(sys.stdin)["skills"]))' <<<"$config")

write_summary() {
  $python_bin - "$summary_file" "$component_id" "$source_ref" "$source_sha" "$catalog_dirs" "$changed" "$failure" <<'PY'
import json
import sys

catalog_dirs = sys.argv[5].splitlines() if sys.argv[5] else []
json.dump({"components": [{
    "component_id": sys.argv[2], "source_ref": sys.argv[3], "source_sha": sys.argv[4],
    "catalog_dirs": catalog_dirs, "changed": sys.argv[6] == "true", "failure": sys.argv[7] or None,
}]}, open(sys.argv[1], "w", encoding="utf-8"), indent=2)
PY
}

# The clone work tree is always disposable. The staging root sits under skills/
# so each final rename is on the target filesystem.
cleanup() {
  [[ "${work_root_owned:-false}" == true ]] && rm -rf "$work_root"
  [[ "${rollback_failed:-false}" != true ]] && rm -rf "${stage_root:-}"
}
mkdir -p "$allowed_tmp"
mkdir "$work_root"
work_root_owned=true
transaction_active=false
rollback_failed=false
on_exit() {
  if [[ "$transaction_active" == true ]] && ! rollback; then rollback_failed=true; fi
  cleanup
}
on_signal() {
  if [[ "$transaction_active" == true ]] && ! rollback; then rollback_failed=true; fi
  cleanup
  trap - EXIT
  exit 143
}
trap on_exit EXIT
trap on_signal HUP INT TERM
mkdir -p skills
stage_root=$(mktemp -d "skills/.component-sync-${component_id}.XXXXXX")
checkout="$work_root/source"

fail() {
  failure=$1
  write_summary
  echo "$failure" >&2
  exit 1
}

clone_url="${repo_base_url%/}/${repo}.git"
git clone --depth 1 --filter=blob:none --sparse --branch "$source_ref" "$clone_url" "$checkout" >/dev/null 2>&1 || fail "could not clone $repo@$source_ref"
source_sha=$(git -C "$checkout" rev-parse HEAD) || fail "could not resolve source SHA"

mapfile -t source_paths < <($python_bin -c 'import json,sys; print("\n".join(x["path"] for x in json.load(sys.stdin)["skills"]))' <<<"$config")
if [[ "$install_type" == workspace ]]; then
  git -C "$checkout" sparse-checkout set --no-cone "${source_paths[@]}" "$install_script" >/dev/null 2>&1 || fail "could not sparse-checkout component paths"
else
  git -C "$checkout" sparse-checkout set --no-cone "${source_paths[@]}" >/dev/null 2>&1 || fail "could not sparse-checkout component paths"
fi

mapfile -t catalog_dir_list < <(printf '%s\n' "$catalog_dirs")
for index in "${!source_paths[@]}"; do
  source_path=${source_paths[$index]}
  catalog_dir=${catalog_dir_list[$index]}
  source_dir="$checkout/$source_path"
  [[ -d "$source_dir" && -n "$(find "$source_dir" -mindepth 1 -print -quit)" ]] || fail "source path is empty or missing: $source_path"
  mkdir -p "$stage_root/$catalog_dir"
  rsync -a --delete "$source_dir/" "$stage_root/$catalog_dir/"
done

if [[ "$install_type" == workspace ]]; then
  [[ -f "$checkout/$install_script" ]] || fail "workspace install script is missing: $install_script"
  cp "$checkout/$install_script" "$stage_root/${catalog_dir_list[0]}/$install_script"
fi

replacement_count=0
declare -a replacement_dirs=()
declare -A target_existed_before=()
declare -A staged_moved=()
rollback() {
  local catalog_dir target backup
  local status=0
  for catalog_dir in "${replacement_dirs[@]}"; do
    target="skills/$catalog_dir"
    backup="$stage_root/.previous-$catalog_dir"
    if [[ -e "$backup" ]]; then
      rm -rf "$target" || status=1
      mv "$backup" "$target" || status=1
    elif [[ "${target_existed_before[$catalog_dir]:-true}" == false && "${staged_moved[$catalog_dir]:-false}" == true ]]; then
      rm -rf "$target" || status=1
    fi
  done
  return "$status"
}

transaction_active=true
compare_output="$work_root/compare-output"
for catalog_dir in "${catalog_dir_list[@]}"; do
  target="skills/$catalog_dir"
  staged="$stage_root/$catalog_dir"
  needs_replace=false
  if [[ -n "$fail_after_replace" ]] || [[ ! -d "$target" ]]; then
    needs_replace=true
  else
    if [[ "$fail_compare" == "$catalog_dir" ]]; then
      fail "could not compare catalog directory: $catalog_dir"
    fi
    if ! rsync -ani --delete "$staged/" "$target/" >"$compare_output" 2>&1; then
      fail "could not compare catalog directory: $catalog_dir"
    fi
    [[ -s "$compare_output" ]] && needs_replace=true
  fi
  if [[ "$needs_replace" == true ]]; then
    changed=true
    backup="$stage_root/.previous-$catalog_dir"
    if [[ -e "$target" && "$fail_backup" == true ]]; then fail "could not backup catalog directory: $catalog_dir"; fi
    # Pre-register before moving: rollback only acts if the backup exists, so
    # this is safe both before a failed move and after a successful one.
    replacement_dirs+=("$catalog_dir")
    if [[ -e "$target" ]]; then target_existed_before[$catalog_dir]=true; else target_existed_before[$catalog_dir]=false; fi
    if [[ -e "$target" ]] && ! mv "$target" "$backup"; then fail "could not backup catalog directory: $catalog_dir"; fi
    [[ -n "$ready_file" ]] && : > "$ready_file"
    [[ -n "$pause_after_backup" ]] && sleep "$pause_after_backup"
    # Mark intent before the move so a signal in the post-move/pre-assignment
    # window removes a newly-created target or restores its backup.
    staged_moved[$catalog_dir]=true
    if ! mv "$staged" "$target"; then
      rollback
      fail "could not replace catalog directory: $catalog_dir"
    fi
    replacement_count=$((replacement_count + 1))
    [[ -n "$pause_after_replace" ]] && sleep "$pause_after_replace"
    if [[ "$fail_after_replace" == "$replacement_count" ]]; then
      rollback
      fail "injected replacement failure"
    fi
  fi
done

# Commit before disposing backups: signals after this point keep the complete
# new state, while signals before it always invoke rollback.
transaction_active=false
for catalog_dir in "${replacement_dirs[@]}"; do
  rm -rf "$stage_root/.previous-$catalog_dir"
done

write_summary



