#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
# Regenerate the README's Available Skills and Getting Help & Contributing
# tables from components.d/*.yml. Used by the sync-skills workflow; can also
# be run locally to preview the result.
#
# Reads:
#   components.d/*.yml      — per-component catalog files (source of truth)
#   skills/<catalog_dir>/   — to count SKILL.md files per component
#   /tmp/sync-versions.txt  — optional, populated by the sync workflow with
#                             upstream short SHA, full SHA, and committer
#                             date per component. When absent, the Version
#                             cell is rendered as an em dash.
#
# Writes:
#   README.md (in place) — content between marker pairs is replaced:
#     <!-- skills-table-start --> ... <!-- skills-table-end -->
#     <!-- help-table-start  --> ... <!-- help-table-end  -->

set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

VERSIONS_FILE="${VERSIONS_FILE:-/tmp/sync-versions.txt}"

# Aggregate per-component files into a single config.
CONFIG=/tmp/components.aggregated.yml
yq ea '[.] | {"components": .}' components.d/*.yml > "$CONFIG"

sorted_indices=$(yq -r '.components | to_entries | sort_by(.value.name | downcase) | .[].key' "$CONFIG")

# Count SKILL.md files for a component index.
component_skill_count() {
  local idx=$1
  local total=0
  while read -r catalog_dir; do
    if [ -d "skills/$catalog_dir" ]; then
      cnt=$(find "skills/$catalog_dir" -name SKILL.md -type f 2>/dev/null | wc -l | tr -d ' ')
      total=$((total + cnt))
    fi
  done < <(yq -r ".components[$idx].skills[].catalog_dir" "$CONFIG")
  echo "$total"
}

# Build the skills table rows.
skills_rows=""
help_rows=""

for idx in $sorted_indices; do
  name=$(yq ".components[$idx].name" "$CONFIG")
  repo=$(yq ".components[$idx].repo" "$CONFIG")
  description=$(yq ".components[$idx].description" "$CONFIG")
  count=$(component_skill_count "$idx")

  # Build skill links
  skill_links=""
  while read -r catalog_dir; do
    if [ -d "skills/$catalog_dir" ]; then
      link="[ \`$catalog_dir\`](skills/$catalog_dir)"
      if [ -z "$skill_links" ]; then
        skill_links="$link"
      else
        skill_links="$skill_links, $link"
      fi
    fi
  done < <(yq -r ".components[$idx].skills[].catalog_dir" "$CONFIG")

  # Skills table row
  skills_rows="${skills_rows}| **${name}** | ${description} | ${skill_links} |
"

  # Help table row
  contributing=$(yq ".components[$idx].links.contributing // \"CONTRIBUTING.md\"" "$CONFIG")
  discussions=$(yq ".components[$idx].links.discussions // true" "$CONFIG")

  contributing_link="—"
  if [ "$contributing" != "false" ]; then
    contributing_link="[Contributing](https://github.com/${repo}/blob/main/${contributing})"
  fi

  discussions_link="—"
  if [ "$discussions" = "true" ]; then
    discussions_link="[Discussions](https://github.com/${repo}/discussions)"
  fi

  help_rows="${help_rows}| **${name}** | [Issues](https://github.com/${repo}/issues) | ${discussions_link} | ${contributing_link} |
"
done

# Replace content between markers in README.md.
python3 -c "
import re
import sys

with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

skills_rows = '''${skills_rows}'''
help_rows = '''${help_rows}'''

# Replace skills table
content = re.sub(
    r'(<!-- skills-table-start -->\n).*?(<!-- skills-table-end -->)',
    r'\1' + skills_rows + r'\2',
    content,
    flags=re.DOTALL
)

# Replace help table
content = re.sub(
    r'(<!-- help-table-start -->\n).*?(<!-- help-table-end -->)',
    r'\1' + help_rows + r'\2',
    content,
    flags=re.DOTALL
)

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(content)

print('README.md regenerated successfully')
"
