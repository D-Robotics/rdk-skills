<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# RDK Skills vX.Y.Z

> One-sentence release summary.

## Overview

Describe the release scope, the user-facing outcome, and the component-tag policy in two or three sentences.

## Highlights

- **BSP Skills**: Describe BSP changes, if any.
- **RDK Device Skills**: Describe board-side changes, if any.
- **OE Tool Chain (X5 / S)**: Describe workspace-pack changes, if any.
- **Hub experience**: Describe finder, installer, registry, plugin, or catalog changes, if any.
- **Compatibility and licenses**: State migration, compatibility, or licensing information when relevant.

## Install

Install an individual flat skill:

```bash
npx skills add d-robotics/rdk-skills
```

Install a workspace pack from a Hub checkout:

```bash
git clone --depth 1 https://github.com/D-Robotics/rdk-skills.git
bash skills/oe-skills-x5/setup.sh --ref vX.Y.Z "$PROJECT_ROOT"
# or: bash skills/oe-skills-s/setup.sh --ref vX.Y.Z "$PROJECT_ROOT"
```

## Verification

- List the release-contract and full-suite commands that passed.
- Record clean-clone or installation smoke-test results.
- Record the source component tags and Hub tag that were cross-checked.

## Component tags

| Component | Tag |
| --- | --- |
| BSP Skills | `vX.Y.Z` |
| RDK Device Skills | `vX.Y.Z` |
| OE Skills X5 | `vX.Y.Z` |
| OE Skills S | `vX.Y.Z` |
| RDK Skills Hub | `vX.Y.Z` |

## Compatibility notes

Document upgrade behavior, migrations, deprecations, or known limitations. Omit this section only when there are no compatibility considerations.
