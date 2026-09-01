#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

# Apply a validated proposal to trusted main, push only its stable bot branch
# over SSH, and use a separate Pull-requests-only App token for PR operations.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

usage() {
  echo "usage: $0 --patch-file FILE --metadata-file FILE --summary-file FILE" >&2
  exit 2
}

patch_file=
metadata_file=
summary_file=
while [[ $# -gt 0 ]]; do
  case "$1" in
    --patch-file) patch_file=${2:-}; shift 2 ;;
    --metadata-file) metadata_file=${2:-}; shift 2 ;;
    --summary-file) summary_file=${2:-}; shift 2 ;;
    *) usage ;;
  esac
done
[[ -f "$patch_file" && -f "$metadata_file" && -n "$summary_file" ]] || usage
[[ -d "$(dirname "$summary_file")" && ! -d "$summary_file" ]] || usage
[[ -n "${GITHUB_REPOSITORY:-}" ]] || { echo "GITHUB_REPOSITORY is required" >&2; exit 2; }
[[ -n "${GH_TOKEN:-}" ]] || { echo "GH_TOKEN is required for PR operations" >&2; exit 2; }

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"
metadata_value() {
  python3 -B -c 'import json,sys; value=json.load(open(sys.argv[1], encoding="utf-8"))[sys.argv[2]]; print(str(value).lower() if isinstance(value, bool) else value)' "$metadata_file" "$1"
}
candidate_sha=$(metadata_value candidate_sha)
component_id=$(metadata_value component_id)
component_name=$(metadata_value component_name)
component_file=$(metadata_value component_file)
new_tag=$(metadata_value new_tag)
repair=$(metadata_value repair)
catalog_dirs_json=$(python3 -B -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1], encoding="utf-8"))["catalog_dirs"]))' "$metadata_file")
[[ "$candidate_sha" =~ ^[0-9a-fA-F]{40}$ ]] || { echo "invalid candidate SHA" >&2; exit 2; }
[[ "$component_id" =~ ^[a-z0-9][a-z0-9-]*$ ]] || { echo "invalid component id" >&2; exit 2; }
python3 -B .github/scripts/release_contract.py validate-tag "$new_tag"

git fetch --no-tags origin main
[[ "$(git rev-parse origin/main)" == "$candidate_sha" ]] || {
  echo "protected main advanced after proposal build; rerun the upgrade" >&2
  exit 1
}
branch="bot/component-upgrade/${component_id}"
branch_ref="refs/heads/$branch"
remote_branch_sha=$(git ls-remote --heads origin "$branch_ref" | awk 'NR == 1 { print $1 }')
if [[ -n "$remote_branch_sha" ]]; then
  [[ "$remote_branch_sha" =~ ^[0-9a-fA-F]{40}$ ]] || { echo "invalid remote proposal SHA" >&2; exit 1; }
  git fetch --no-tags origin "$branch_ref"
  proposal_tag=$(git show "$remote_branch_sha:$component_file" | python3 -B -c 'import sys,yaml; data=yaml.safe_load(sys.stdin.read()); value=data.get("ref") if isinstance(data,dict) else None; print(value or "")')
  python3 -B .github/scripts/component_upgrade.py require-release-order \
    --incoming-tag "$new_tag" \
    --main-tag "$(python3 -B -c 'import sys,yaml; print(yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["ref"])' "$component_file")" \
    --proposal-tag "$proposal_tag"
fi

# Never switch to the remote proposal. Reconstruct from the exact trusted-main
# candidate and apply only the already-tested binary patch artifact.
git switch --force-create "$branch" "$candidate_sha"
test -z "$(git status --porcelain --untracked-files=all)" || {
  echo "publication checkout is not clean" >&2
  exit 1
}
git apply --index --binary "$patch_file"
stage_args=(
  .github/scripts/component_upgrade.py stage-proposal
  --component-file "$component_file"
  --catalog-dirs-json "$catalog_dirs_json"
)
[[ "$repair" == true ]] && stage_args+=(--repair)
applied_paths_json=$(python3 -B "${stage_args[@]}")
python3 -B - "$metadata_file" "$applied_paths_json" <<'PY'
import json
import sys

metadata = json.load(open(sys.argv[1], encoding="utf-8"))
actual = json.loads(sys.argv[2])
if actual != metadata.get("staged_paths"):
    raise SystemExit("applied proposal paths differ from the validated artifact")
PY

labels_json=$(gh label list --repo "$GITHUB_REPOSITORY" --limit 100 --json name)
python3 -B .github/scripts/component_upgrade.py require-labels \
  --labels-json "$labels_json" --component "$component_id"

body_file=$(mktemp)
cleanup() { rm -f "$body_file"; }
trap cleanup EXIT
python3 -B - "$metadata_file" "$body_file" <<'PY'
import json
import sys
from pathlib import Path

metadata = json.load(open(sys.argv[1], encoding="utf-8"))
Path(sys.argv[2]).write_text(metadata["body"], encoding="utf-8", newline="\n")
PY
pr_title=$(metadata_value title)

git config user.name "rdk-component-branch-bot"
git config user.email "rdk-component-branch-bot@users.noreply.github.com"
git commit --signoff -m "chore: upgrade $component_name to $new_tag"
if [[ -n "$remote_branch_sha" ]]; then
  git push --force-with-lease="$branch_ref:$remote_branch_sha" origin "HEAD:$branch_ref"
else
  git push --force-with-lease="$branch_ref:" origin "HEAD:$branch_ref"
fi

pr_number=$(gh pr list --repo "$GITHUB_REPOSITORY" --head "$branch" --base main --state open --json number --jq '.[0].number')
if [[ -n "$pr_number" && "$pr_number" != null ]]; then
  gh pr edit "$pr_number" --repo "$GITHUB_REPOSITORY" --title "$pr_title" --body-file "$body_file"
else
  pr_url=$(gh pr create --repo "$GITHUB_REPOSITORY" --base main --head "$branch" --title "$pr_title" --body-file "$body_file")
  pr_number=${pr_url##*/}
fi
gh pr edit "$pr_number" --repo "$GITHUB_REPOSITORY" \
  --add-label component-upgrade --add-label "source:${component_id}"

python3 -B - "$summary_file" "$metadata_file" "$branch" "$pr_number" <<'PY'
import json
import sys
from pathlib import Path

metadata = json.load(open(sys.argv[2], encoding="utf-8"))
output = {
    "previous_tag": metadata["previous_tag"],
    "new_tag": metadata["new_tag"],
    "branch": sys.argv[3],
    "pr_number": sys.argv[4],
    "source_sha": metadata["source_sha"],
    "staged_paths": metadata["staged_paths"],
    "test_result": metadata["test_result"],
}
Path(sys.argv[1]).write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
PY
