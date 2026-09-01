#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

# Preserve the historical shell entry point while keeping all YAML and
# source-controlled filenames as parsed data in a standalone Python program.
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
python3 -B "$repo_root/.github/scripts/regenerate_readme.py" --root "$repo_root"
