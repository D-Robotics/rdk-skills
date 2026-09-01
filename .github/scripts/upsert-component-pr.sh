#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

# Build and test a component proposal without any repository-write credential.
# The resulting binary patch and structured metadata are the only artifacts
# passed to the separate SSH/PR-App publication job.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

usage() {
  echo "usage: $0 --component ID --tag TAG --release-url URL --source-sha SHA --patch-file FILE --metadata-file FILE [--repair]" >&2
  exit 2
}

component_id=
new_tag=
release_url=
source_sha=
patch_file=
metadata_file=
repair=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --component) component_id=${2:-}; shift 2 ;;
    --tag) new_tag=${2:-}; shift 2 ;;
    --release-url) release_url=${2:-}; shift 2 ;;
    --source-sha) source_sha=${2:-}; shift 2 ;;
    --patch-file) patch_file=${2:-}; shift 2 ;;
    --metadata-file) metadata_file=${2:-}; shift 2 ;;
    --repair) repair=true; shift ;;
    *) usage ;;
  esac
done

[[ "$component_id" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "invalid component id" >&2; exit 2; }
python3 -B .github/scripts/release_contract.py validate-tag "$new_tag"
[[ "$source_sha" =~ ^[0-9a-fA-F]{40}$ ]] || { echo "invalid source SHA" >&2; exit 2; }
[[ -n "$release_url" && "$release_url" != *$'\n'* && "$release_url" != *$'\r'* ]] || { echo "invalid release URL" >&2; exit 2; }
for output in "$patch_file" "$metadata_file"; do
  [[ -n "$output" && -d "$(dirname "$output")" && ! -d "$output" ]] || usage
done

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
test -z "$(git status --porcelain --untracked-files=all)" || {
  echo "proposal checkout must start clean" >&2
  exit 1
}
candidate_sha=$(git rev-parse HEAD)
component_file="components.d/$component_id.yml"
[[ -f "$component_file" ]] || { echo "unknown component: $component_id" >&2; exit 2; }

component_data=$(python3 -B - "$component_file" <<'PY'
import json
import sys
from pathlib import Path

import yaml

path = Path(sys.argv[1])
data = yaml.safe_load(path.read_text(encoding="utf-8"))
if not isinstance(data, dict):
    raise SystemExit("component YAML must be a mapping")
for field in ("name", "repo", "ref"):
    if not isinstance(data.get(field), str) or not data[field] or "\n" in data[field] or "\r" in data[field]:
        raise SystemExit(f"component {field} is required as one line")
print(json.dumps({field: data[field] for field in ("name", "repo", "ref")}))
PY
)
component_name=$(python3 -B -c 'import json,sys; print(json.load(sys.stdin)["name"])' <<<"$component_data")
component_repo=$(python3 -B -c 'import json,sys; print(json.load(sys.stdin)["repo"])' <<<"$component_data")
previous_tag=$(python3 -B -c 'import json,sys; print(json.load(sys.stdin)["ref"])' <<<"$component_data")
python3 -B .github/scripts/component_upgrade.py require-release-order \
  --incoming-tag "$new_tag" --main-tag "$previous_tag"
expected_url="https://github.com/$component_repo/releases/tag/$new_tag"
[[ "$release_url" == "$expected_url" ]] || { echo "release URL does not match component and tag" >&2; exit 2; }

if [[ "$previous_tag" != "$new_tag" ]]; then
  python3 -B - "$component_file" "$new_tag" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
tag = sys.argv[2]
raw = path.read_bytes()
updated, count = re.subn(rb"(?m)^ref:[^\r\n]*", b"ref: " + tag.encode("ascii"), raw)
if count != 1:
    raise SystemExit("component YAML must contain exactly one ref")
path.write_bytes(updated)
PY
elif [[ "$repair" != true ]]; then
  echo "same-tag proposal must be an explicit repair" >&2
  exit 2
fi

python3 -B - "$component_file" "$new_tag" "$repair" <<'PY'
import subprocess
import sys

component_file, new_tag, repair = sys.argv[1:]
result = subprocess.run(
    ["git", "diff", "--unified=0", "HEAD", "--", component_file],
    check=True,
    text=True,
    capture_output=True,
)
changes = [
    line for line in result.stdout.splitlines()
    if line[:1] in ("+", "-") and not line.startswith(("+++", "---"))
]
if repair == "true":
    if changes:
        raise SystemExit("repair changed a component registration")
elif len(changes) != 2 or not changes[0].startswith("-ref: ") or changes[1] != f"+ref: {new_tag}":
    raise SystemExit("component upgrade may change only the selected component ref")
PY

sync_summary=$(mktemp)
body_file=$(mktemp)
cleanup() { rm -f "$sync_summary" "$body_file"; }
trap cleanup EXIT
work_root=".tmp/component-sync-${component_id}-${GITHUB_RUN_ID:-local}-${RANDOM}"
bash .github/scripts/sync-components.sh \
  --components-dir components.d \
  --component "$component_id" \
  --repo-base-url https://github.com \
  --work-root "$work_root" \
  --summary-file "$sync_summary"

catalog_dirs_json=$(python3 -B .github/scripts/component_upgrade.py validate-sync-summary \
  --summary-file "$sync_summary" --source-sha "$source_sha")
.github/scripts/build-plugins.sh
bash .github/scripts/regenerate-readme.sh
python3 -B -m unittest discover -s tests -v

stage_args=(
  .github/scripts/component_upgrade.py stage-proposal
  --component-file "$component_file"
  --catalog-dirs-json "$catalog_dirs_json"
)
[[ "$repair" == true ]] && stage_args+=(--repair)
staged_paths_json=$(python3 -B "${stage_args[@]}")
[[ "$(git diff --cached --name-only | wc -l | tr -d ' ')" -gt 0 ]] || {
  echo "upgrade action produced no staged proposal" >&2
  exit 1
}

generated_artifacts_json=$(python3 -B - "$staged_paths_json" <<'PY'
import json
import sys

paths = json.loads(sys.argv[1])
print(json.dumps([
    path for path in paths
    if path == "README.md" or path.startswith("plugins/") or "marketplace.json" in path
]))
PY
)
test_result="PASS: python3 -B -m unittest discover -s tests -v"
python3 -B .github/scripts/component_upgrade.py render-pr-body \
  --component-name "$component_name" \
  --component "$component_id" \
  --previous-tag "$previous_tag" \
  --new-tag "$new_tag" \
  --release-url "$release_url" \
  --source-sha "$source_sha" \
  --catalog-dirs-json "$catalog_dirs_json" \
  --artifacts-json "$generated_artifacts_json" \
  --test-result "$test_result" > "$body_file"

git diff --cached --binary --full-index --no-ext-diff > "$patch_file"
python3 -B - "$metadata_file" "$candidate_sha" "$component_id" "$component_name" \
  "$component_repo" "$component_file" "$previous_tag" "$new_tag" "$release_url" \
  "$source_sha" "$repair" "$catalog_dirs_json" "$generated_artifacts_json" \
  "$staged_paths_json" "$body_file" <<'PY'
import json
import sys
from pathlib import Path

(
    destination, candidate_sha, component_id, component_name, component_repo,
    component_file, previous_tag, new_tag, release_url, source_sha, repair,
    catalog_dirs, generated_artifacts, staged_paths, body_file,
) = sys.argv[1:]
metadata = {
    "candidate_sha": candidate_sha,
    "component_id": component_id,
    "component_name": component_name,
    "component_repo": component_repo,
    "component_file": component_file,
    "previous_tag": previous_tag,
    "new_tag": new_tag,
    "release_url": release_url,
    "source_sha": source_sha.lower(),
    "repair": repair == "true",
    "catalog_dirs": json.loads(catalog_dirs),
    "generated_artifacts": json.loads(generated_artifacts),
    "staged_paths": json.loads(staged_paths),
    "title": f"chore: upgrade {component_name} to {new_tag}",
    "body": Path(body_file).read_text(encoding="utf-8"),
    "test_result": "PASS: python3 -B -m unittest discover -s tests -v",
}
Path(destination).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")
PY
