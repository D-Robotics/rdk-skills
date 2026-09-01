#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

# Build a component-upgrade proposal exclusively from trusted origin/main.
# A pre-existing bot branch is only a remote ref protected by force-with-lease;
# its content is never checked out or executed.
set -euo pipefail

usage() {
  echo "usage: $0 --component ID --tag TAG --release-url URL --source-sha SHA --summary-file FILE [--repair]" >&2
  exit 2
}

component_id=
new_tag=
release_url=
source_sha=
summary_file=
repair=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --component) component_id=${2:-}; shift 2 ;;
    --tag) new_tag=${2:-}; shift 2 ;;
    --release-url) release_url=${2:-}; shift 2 ;;
    --source-sha) source_sha=${2:-}; shift 2 ;;
    --summary-file) summary_file=${2:-}; shift 2 ;;
    --repair) repair=true; shift ;;
    *) usage ;;
  esac
done

[[ "$component_id" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "invalid component id" >&2; exit 2; }
[[ "$new_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "invalid release tag" >&2; exit 2; }
[[ "$source_sha" =~ ^[0-9a-fA-F]{40}$ ]] || { echo "invalid source SHA" >&2; exit 2; }
[[ -n "$release_url" && "$release_url" != *$'\n'* && "$release_url" != *$'\r'* ]] || { echo "invalid release URL" >&2; exit 2; }
[[ -n "$summary_file" && -d "$(dirname "$summary_file")" && ! -d "$summary_file" ]] || usage
[[ -n "${GITHUB_REPOSITORY:-}" ]] || { echo "GITHUB_REPOSITORY is required" >&2; exit 2; }

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
component_file="components.d/$component_id.yml"
[[ -f "$component_file" ]] || { echo "unknown component: $component_id" >&2; exit 2; }

# Labels are a maintainer-provisioned repository prerequisite. This is the
# first operation that can talk to GitHub and occurs before any bot ref write.
labels_json=$(gh label list --repo "$GITHUB_REPOSITORY" --limit 100 --json name)
python3 .github/scripts/component_upgrade.py require-labels \
  --labels-json "$labels_json" --component "$component_id"

component_data=$(python3 - "$component_file" <<'PY'
import json
import sys
from pathlib import Path

import yaml

path = Path(sys.argv[1])
data = yaml.safe_load(path.read_text(encoding="utf-8"))
if not isinstance(data, dict):
    raise SystemExit("component YAML must be a mapping")
for field in ("name", "repo", "ref"):
    if not isinstance(data.get(field), str) or not data[field]:
        raise SystemExit(f"component {field} is required")
print(json.dumps({field: data[field] for field in ("name", "repo", "ref")}))
PY
)
component_name=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["name"])' <<<"$component_data")
component_repo=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["repo"])' <<<"$component_data")
previous_tag=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["ref"])' <<<"$component_data")
[[ "$previous_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "previous tag is not stable" >&2; exit 2; }
expected_url="https://github.com/$component_repo/releases/tag/$new_tag"
[[ "$release_url" == "$expected_url" ]] || { echo "release URL does not match component and tag" >&2; exit 2; }

branch="bot/component-upgrade/${component_id}"
branch_ref="refs/heads/$branch"
git fetch --no-tags origin main
remote_branch_sha=$(git ls-remote --heads origin "$branch_ref" | awk '{print $1}')

# Always reconstruct the proposal from trusted main. Never switch to or run a
# helper from the existing stable branch.
git switch --force-create "$branch" origin/main

if [[ "$previous_tag" != "$new_tag" ]]; then
  python3 - "$component_file" "$new_tag" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
tag = sys.argv[2]
raw = path.read_bytes()
updated, count = re.subn(
    rb"(?m)^ref:[^\r\n]*",
    b"ref: " + tag.encode("ascii"),
    raw,
)
if count != 1:
    raise SystemExit("component YAML must contain exactly one ref")
path.write_bytes(updated)
PY
elif [[ "$repair" != true ]]; then
  echo "same-tag proposal must be an explicit repair" >&2
  exit 2
fi

# Ensure the trusted proposal changes no component registration except the
# selected ref; a repair is allowed to leave all component files untouched.
python3 - "$component_file" "$new_tag" "$repair" <<'PY'
import subprocess
import sys

component_file, new_tag, repair = sys.argv[1:]
result = subprocess.run(
    ["git", "diff", "--unified=0", "origin/main", "--", component_file],
    check=True,
    text=True,
    capture_output=True,
)
changes = [
    line
    for line in result.stdout.splitlines()
    if line[:1] in ("+", "-") and not line.startswith(("+++", "---"))
]
expected = [] if repair == "true" else [None, f"+ref: {new_tag}"]
if (repair == "true" and changes) or (
    repair != "true" and (len(changes) != 2 or not changes[0].startswith("-ref: ") or changes[1] != expected[1])
):
    raise SystemExit("component upgrade may change only the selected component ref")
PY

sync_summary=$(mktemp)
trap 'rm -f "$sync_summary"' EXIT
work_root=".tmp/component-sync-${component_id}-${GITHUB_RUN_ID:-local}-${RANDOM}"
bash .github/scripts/sync-components.sh \
  --components-dir components.d \
  --component "$component_id" \
  --repo-base-url https://github.com \
  --work-root "$work_root" \
  --summary-file "$sync_summary"

# Bind mirrored bytes to the dereferenced SHA verified by the workflow before
# build, test, commit, push, or PR mutation can occur.
catalog_dirs_json=$(python3 .github/scripts/component_upgrade.py validate-sync-summary \
  --summary-file "$sync_summary" --source-sha "$source_sha")
mapfile -t catalog_dirs < <(python3 -c 'import json,sys; print("\n".join(json.load(sys.stdin)))' <<<"$catalog_dirs_json")

.github/scripts/build-plugins.sh
bash .github/scripts/regenerate-readme.sh
python3 -B -m unittest discover -s tests -v

mapfile -t changed_component_files < <(git diff --name-only origin/main -- components.d)
if [[ "$repair" == true ]]; then
  [[ "${#changed_component_files[@]}" -eq 0 ]] || { echo "repair changed a component registration" >&2; exit 1; }
elif [[ "${#changed_component_files[@]}" -ne 1 || "${changed_component_files[0]}" != "$component_file" ]]; then
  echo "component upgrade changed an unrelated component registration" >&2
  exit 1
fi

while IFS= read -r changed_path; do
  allowed=false
  case "$changed_path" in
    "$component_file"|README.md|.claude-plugin/marketplace.json|.agents/plugins/marketplace.json|.cursor-plugin/marketplace.json|.dsh-plugin/marketplace.json|plugins/*)
      allowed=true ;;
    skills/*)
      for catalog_dir in "${catalog_dirs[@]}"; do
        [[ "$changed_path" == "skills/$catalog_dir/"* ]] && allowed=true
      done ;;
  esac
  if [[ "$allowed" != true ]]; then
    echo "component upgrade changed an unexpected path: $changed_path" >&2
    exit 1
  fi
done < <(git diff --name-only origin/main)

git diff --check origin/main
generated_artifacts_json=$(git diff --name-only origin/main -- \
  README.md plugins .claude-plugin/marketplace.json .agents/plugins/marketplace.json \
  .cursor-plugin/marketplace.json .dsh-plugin/marketplace.json | python3 -c 'import json,sys; print(json.dumps([line.rstrip("\n") for line in sys.stdin if line.strip()]))')
test_result="PASS: python3 -B -m unittest discover -s tests -v"

body_file=$(mktemp)
trap 'rm -f "$sync_summary" "$body_file"' EXIT
python3 .github/scripts/component_upgrade.py render-pr-body \
  --component-name "$component_name" \
  --component "$component_id" \
  --previous-tag "$previous_tag" \
  --new-tag "$new_tag" \
  --release-url "$release_url" \
  --source-sha "$source_sha" \
  --catalog-dirs-json "$catalog_dirs_json" \
  --artifacts-json "$generated_artifacts_json" \
  --test-result "$test_result" > "$body_file"

if ! git diff --quiet; then
  git config user.name "rdk-release-bot[bot]"
  git config user.email "rdk-release-bot[bot]@users.noreply.github.com"
  git add -A
  git commit --signoff -m "chore: upgrade $component_name to $new_tag"
  if [[ -n "$remote_branch_sha" ]]; then
    git push --force-with-lease="$branch_ref:$remote_branch_sha" origin "HEAD:$branch_ref"
  else
    git push --force-with-lease="$branch_ref:" origin "HEAD:$branch_ref"
  fi
fi

pr_number=$(gh pr list --head "$branch" --base main --state open --json number --jq '.[0].number')
pr_title="chore: upgrade $component_name to $new_tag"
if [[ -n "$pr_number" ]]; then
  gh pr edit "$pr_number" --title "$pr_title" --body-file "$body_file"
else
  pr_url=$(gh pr create --base main --head "$branch" --title "$pr_title" --body-file "$body_file")
  pr_number=${pr_url##*/}
fi
gh pr edit "$pr_number" --add-label component-upgrade --add-label "source:${component_id}"

python3 - "$summary_file" "$previous_tag" "$new_tag" "$branch" "$pr_number" "$sync_summary" <<'PY'
import json
import sys

output = {
    "previous_tag": sys.argv[2],
    "new_tag": sys.argv[3],
    "branch": sys.argv[4],
    "pr_number": sys.argv[5],
    "sync": json.load(open(sys.argv[6], encoding="utf-8")),
    "test_result": "PASS: python3 -B -m unittest discover -s tests -v",
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(output, handle, indent=2)
    handle.write("\n")
PY
