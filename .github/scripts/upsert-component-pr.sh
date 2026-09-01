#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

# Create or update the one reviewable component-upgrade PR for a formal
# source Release. This script is intentionally called only after the workflow
# has validated the Release and rejected dry runs/noops.
set -euo pipefail

usage() {
  echo "usage: $0 --component ID --tag TAG --release-url URL --source-sha SHA --summary-file FILE" >&2
  exit 2
}

component_id=
new_tag=
release_url=
source_sha=
summary_file=
while [[ $# -gt 0 ]]; do
  case "$1" in
    --component) component_id=${2:-}; shift 2 ;;
    --tag) new_tag=${2:-}; shift 2 ;;
    --release-url) release_url=${2:-}; shift 2 ;;
    --source-sha) source_sha=${2:-}; shift 2 ;;
    --summary-file) summary_file=${2:-}; shift 2 ;;
    *) usage ;;
  esac
done

[[ "$component_id" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "invalid component id" >&2; exit 2; }
[[ "$new_tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "invalid release tag" >&2; exit 2; }
[[ "$source_sha" =~ ^[0-9a-fA-F]{40}$ ]] || { echo "invalid source SHA" >&2; exit 2; }
[[ -n "$release_url" && "$release_url" != *$'\n'* && "$release_url" != *$'\r'* ]] || { echo "invalid release URL" >&2; exit 2; }
[[ -n "$summary_file" && -d "$(dirname "$summary_file")" && ! -d "$summary_file" ]] || usage

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
component_file="components.d/$component_id.yml"
[[ -f "$component_file" ]] || { echo "unknown component: $component_id" >&2; exit 2; }

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
expected_url="https://github.com/$component_repo/releases/tag/$new_tag"
[[ "$release_url" == "$expected_url" ]] || { echo "release URL does not match component and tag" >&2; exit 2; }

branch="bot/component-upgrade/${component_id}"
git fetch --no-tags origin main
if git ls-remote --exit-code --heads origin "$branch" >/dev/null 2>&1; then
  git fetch --no-tags origin "$branch"
  git switch --force-create "$branch" "origin/$branch"
else
  git switch --force-create "$branch" origin/main
fi

# A newer event may update an existing bot branch, so the previous tag is read
# after selecting that branch rather than assumed from main.
previous_tag=$(python3 - "$component_file" <<'PY'
import sys
from pathlib import Path
import yaml

data = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))
if not isinstance(data, dict) or not isinstance(data.get("ref"), str):
    raise SystemExit("component ref is required")
print(data["ref"])
PY
)

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

# Validate the registration before synchronization makes any mirror changes.
# This also rejects a pre-existing bot branch that contains edits beyond the
# selected component's one pinned ref.
python3 - "$component_file" "$new_tag" <<'PY'
import subprocess
import sys

component_file, new_tag = sys.argv[1:]
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
if len(changes) != 2 or not changes[0].startswith("-ref: ") or changes[1] != f"+ref: {new_tag}":
    raise SystemExit("component upgrade may change only the selected component ref")
PY

sync_summary=$(mktemp)
test_log=$(mktemp)
trap 'rm -f "$sync_summary" "$test_log"' EXIT
work_root=".tmp/component-sync-${component_id}-${GITHUB_RUN_ID:-local}-${RANDOM}"
bash .github/scripts/sync-components.sh \
  --components-dir components.d \
  --component "$component_id" \
  --repo-base-url https://github.com \
  --work-root "$work_root" \
  --summary-file "$sync_summary"

.github/scripts/build-plugins.sh
bash .github/scripts/regenerate-readme.sh
python3 -B -m unittest discover -s tests -v 2>&1 | tee "$test_log"

# Bot branches may carry only their component registration plus that component's
# mirror and generated Hub artifacts. Never let a stale or tampered bot branch
# smuggle a second component ref into a PR.
mapfile -t catalog_dirs < <(python3 - "$sync_summary" <<'PY'
import json
import sys

summary = json.load(open(sys.argv[1], encoding="utf-8"))
for directory in summary["components"][0]["catalog_dirs"]:
    print(directory)
PY
)
mapfile -t changed_component_files < <(git diff --name-only origin/main -- components.d)
if [[ "${#changed_component_files[@]}" -ne 1 || "${changed_component_files[0]}" != "$component_file" ]]; then
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
generated_artifacts=$(git diff --name-only origin/main -- \
  README.md plugins .claude-plugin/marketplace.json .agents/plugins/marketplace.json \
  .cursor-plugin/marketplace.json .dsh-plugin/marketplace.json | sed 's/^/- /')
mirrored_dirs=$(printf '%s\n' "${catalog_dirs[@]}" | sed 's/^/- skills\//')
test_result="PASS: python3 -B -m unittest discover -s tests -v"

if ! git diff --quiet; then
  git config user.name "rdk-release-bot[bot]"
  git config user.email "rdk-release-bot[bot]@users.noreply.github.com"
  git add -A
  git commit --signoff -m "chore: upgrade $component_name to $new_tag"
  git push origin "HEAD:refs/heads/$branch"
fi

body_file=$(mktemp)
trap 'rm -f "$sync_summary" "$test_log" "$body_file"' EXIT
cat > "$body_file" <<EOF
## Automated component upgrade

| Field | Value |
| --- | --- |
| Component | $component_name (`$component_id`) |
| Previous tag | `$previous_tag` |
| New tag | `$new_tag` |
| Source Release | $release_url |
| Dereferenced source SHA | `$source_sha` |

### Mirrored directories

$mirrored_dirs

### Generated artifacts

${generated_artifacts:-- None}

### Tests

$test_result

A maintainer must review this PR and choose the eventual Hub version after merge.
EOF

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
