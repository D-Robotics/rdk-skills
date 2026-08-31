#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.
#
# Build plugin distributions from plugins.d/*.yml definitions.
#
# For each plugin yaml (excluding _-prefixed includes), this script:
#   1. Reads include_skills list and copies/symlinks each skill
#      into plugins/<name>/skills/
#   2. Generates .claude-plugin/plugin.json, .codex-plugin/plugin.json,
#      .cursor-plugin/plugin.json inside the plugin dir
#   3. Regenerates top-level marketplace.json files:
#      - .claude-plugin/marketplace.json
#      - .agents/plugins/marketplace.json
#      - .cursor-plugin/marketplace.json
#
# Usage:
#   .github/scripts/build-plugins.sh [--dry-run]

set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1
PYTHON_BIN="${PYTHON_BIN:-python}"

# Validate catalog inputs before any plugin distribution is removed. A dry run
# checks includes without regenerating tracked catalog data.
if [ "$DRY_RUN" -eq 0 ]; then
  "$PYTHON_BIN" .github/scripts/generate_plugin_catalog.py --repo-root .
fi
"$PYTHON_BIN" .github/scripts/generate_plugin_catalog.py --repo-root . --check-plugin-includes

# Load defaults
DEFAULTS_FILE="plugins.d/_defaults.yml"
default_version=$(yq '.version // "1.0.0"' "$DEFAULTS_FILE" 2>/dev/null || echo "1.0.0")
default_author_name=$(yq '.author.name // "D-Robotics"' "$DEFAULTS_FILE" 2>/dev/null || echo "D-Robotics")
default_author_url=$(yq '.author.url // "https://github.com/D-Robotics/rdk-skills"' "$DEFAULTS_FILE" 2>/dev/null || echo "https://github.com/D-Robotics/rdk-skills")
default_homepage=$(yq '.homepage // "https://developer.d-robotics.com"' "$DEFAULTS_FILE" 2>/dev/null || echo "https://developer.d-robotics.com")
default_repo=$(yq '.repository // "https://github.com/D-Robotics/rdk-skills"' "$DEFAULTS_FILE" 2>/dev/null || echo "https://github.com/D-Robotics/rdk-skills")
default_license=$(yq '.license // "Apache-2.0 AND CC-BY-4.0"' "$DEFAULTS_FILE" 2>/dev/null || echo "Apache-2.0 AND CC-BY-4.0")
default_brand=$(yq '.brand_color // "#1D9E75"' "$DEFAULTS_FILE" 2>/dev/null || echo "#1D9E75")
default_skill_files=$(yq '.skill_files // "copy"' "$DEFAULTS_FILE" 2>/dev/null || echo "copy")

# Collect all plugin definitions.
plugin_files=""
for f in plugins.d/*.yml; do
  [ -f "$f" ] || continue
  basename=$(basename "$f" .yml)
  # Skip includes
  case "$basename" in _*) continue ;; esac
  plugin_files="$plugin_files $basename"
done

# Build each plugin.
claude_plugins="[]"
codex_plugins="[]"
cursor_plugins="[]"
dsh_bundles="[]"

for pname in $plugin_files; do
  yml_file="plugins.d/${pname}.yml"
  plugin_dir="plugins/$pname"

  echo "=== Building plugin: $pname ==="

  name=$(yq '.name // "'"$pname"'"' "$yml_file")
  version=$(yq '.version // "'"$default_version"'"' "$yml_file")
  description=$(yq '.description // ""' "$yml_file")
  display_name=$(yq '.display_name // "'"$name"'"' "$yml_file")
  short_description=$(yq '.short_description // ""' "$yml_file")
  long_description=$(yq '.long_description // ""' "$yml_file")
  category=$(yq '.category // "Coding"' "$yml_file")
  skill_files_mode=$(yq '.skill_files // "'"$default_skill_files"'"' "$yml_file")

  author_name=$(yq '.author.name // "'"$default_author_name"'"' "$yml_file")
  author_url=$(yq '.author.url // "'"$default_author_url"'"' "$yml_file")

  if [ "$DRY_RUN" -eq 0 ]; then
    # Clean and recreate plugin dir
    rm -rf "$plugin_dir"
    mkdir -p "$plugin_dir/skills"

    # Copy/symlink skills
    while IFS= read -r skill_path; do
      [ -z "$skill_path" ] && continue
      skill_basename=$(basename "$skill_path")
      dest="$plugin_dir/skills/$skill_basename"

      if [ "$skill_files_mode" = "symlink" ]; then
        ln -sf "../../../skills/$skill_basename" "$dest"
      else
        rsync -a "$skill_path/" "$dest/"
      fi
    done < <(yq -r '.include_skills[]?' "$yml_file")

    # Generate plugin.json for each platform
    for platform in .claude-plugin .codex-plugin .cursor-plugin; do
      mkdir -p "$plugin_dir/$platform"
      cat > "$plugin_dir/$platform/plugin.json" <<EOF
{
  "name": "$name",
  "version": "$version",
  "description": "$short_description",
  "display_name": "$display_name",
  "category": "$category",
  "author": {
    "name": "$author_name",
    "url": "$author_url"
  },
  "license": "$default_license"
}
EOF
    done

    # Generate the DeepSeek Harness (DSH) plugin manifest when the plugin
    # declares dsh_plugins bundles.
    dsh_entry_list=$(yq -o json '.dsh_plugins // []' "$yml_file")
    if [ "$dsh_entry_list" != "[]" ]; then
      mkdir -p "$plugin_dir/.dsh-plugin"
      cat > "$plugin_dir/.dsh-plugin/plugin.json" <<EOF
{
  "name": "$name",
  "version": "$version",
  "description": "$short_description",
  "author": {
    "name": "$author_name",
    "url": "$author_url"
  },
  "license": "$default_license",
  "plugins": $dsh_entry_list
}
EOF
    fi
  fi

  # Accumulate marketplace entries
  dsh_bundles=$(echo "$dsh_bundles" | yq -o json -r ". + $(yq -o json '.dsh_plugins // []' "$yml_file")")

  # Accumulate marketplace entries
  claude_plugins=$(echo "$claude_plugins" | yq -o json -r ". + [{
    \"name\": \"$name\",
    \"source\": \"./plugins/$pname\",
    \"description\": \"$description\"
  }]")
  codex_plugins=$(echo "$codex_plugins" | yq -o json -r ". + [{
    \"name\": \"$name\",
    \"source\": {
      \"source\": \"local\",
      \"path\": \"./plugins/$pname\"
    },
    \"policy\": {
      \"installation\": \"AVAILABLE\",
      \"authentication\": \"ON_INSTALL\"
    },
    \"category\": \"$category\"
  }]")
  cursor_plugins=$(echo "$cursor_plugins" | yq -o json -r ". + [{
    \"name\": \"$name\",
    \"source\": \"./plugins/$pname\",
    \"description\": \"$description\"
  }]")
done

if [ "$DRY_RUN" -eq 0 ]; then
  # Generate top-level marketplace.json files
  mkdir -p .claude-plugin .agents/plugins .cursor-plugin
  plugin_tmp_dir=".tmp/plugin-build-$$"
  mkdir -p "$plugin_tmp_dir"
  trap 'rm -rf "$plugin_tmp_dir"' EXIT

  echo "$claude_plugins" | yq -P -o json > "$plugin_tmp_dir/claude-plugins.json"
  "$PYTHON_BIN" -c "
import json
plugins = json.load(open('$plugin_tmp_dir/claude-plugins.json'))
marketplace = {
    'name': 'd-robotics-official',
    'owner': {
        'name': 'D-Robotics',
        'url': 'https://github.com/D-Robotics/rdk-skills'
    },
    'metadata': {
        'description': 'D-Robotics plugin marketplace — install the curated D-Robotics plugins and skills from this catalog repo.',
        'version': '1.0.0'
    },
    'plugins': plugins
}
json.dump(marketplace, open('.claude-plugin/marketplace.json', 'w'), indent=4)
print('.claude-plugin/marketplace.json generated')
"

  echo "$codex_plugins" | yq -P -o json > "$plugin_tmp_dir/codex-plugins.json"
  "$PYTHON_BIN" -c "
import json
plugins = json.load(open('$plugin_tmp_dir/codex-plugins.json'))
marketplace = {
    'name': 'd-robotics-official',
    'interface': {
        'displayName': 'D-Robotics Official'
    },
    'plugins': plugins
}
json.dump(marketplace, open('.agents/plugins/marketplace.json', 'w'), indent=4)
print('.agents/plugins/marketplace.json generated')
"

  echo "$cursor_plugins" | yq -P -o json > "$plugin_tmp_dir/cursor-plugins.json"
  "$PYTHON_BIN" -c "
import json
plugins = json.load(open('$plugin_tmp_dir/cursor-plugins.json'))
marketplace = {
    'name': 'd-robotics-official',
    'owner': {
        'name': 'D-Robotics',
        'url': 'https://github.com/D-Robotics/rdk-skills'
    },
    'plugins': plugins
}
json.dump(marketplace, open('.cursor-plugin/marketplace.json', 'w'), indent=4)
print('.cursor-plugin/marketplace.json generated')
"

  # Generate the DeepSeek Harness (DSH) marketplace: installable dsh bundles
  # (npm / git), discoverable through the dsh-plugin GitHub topic.
  mkdir -p .dsh-plugin
  echo "$dsh_bundles" | yq -P -o json > "$plugin_tmp_dir/dsh-bundles.json"
  "$PYTHON_BIN" -c "
import json
bundles = json.load(open('$plugin_tmp_dir/dsh-bundles.json'))
marketplace = {
    'name': 'd-robotics-dsh',
    'owner': {
        'name': 'D-Robotics',
        'url': 'https://github.com/D-Robotics/rdk-skills'
    },
    'metadata': {
        'description': 'D-Robotics DeepSeek Harness (DSH) plugin marketplace — npm/git-installable dsh bundles for the RDK ecosystem.',
        'version': '1.0.0'
    },
    'plugins': bundles
}
json.dump(marketplace, open('.dsh-plugin/marketplace.json', 'w'), indent=4)
print('.dsh-plugin/marketplace.json generated')
"

fi

echo "Plugin build complete."
