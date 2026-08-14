---
name: bsp-source-sync
description: Sync the RDK Linux source tree (kernel, bootloader, hobot-* package sources) using repo and the official manifests — X5 uses D-Robotics/x5-manifest, X3 uses D-Robotics/manifest. Use when the user wants to download/checkout the BSP source, switch branches, or repo init/sync fails. 触发词:repo init、repo sync、同步源码、下载源码、manifest、源码树、develop 分支. Do not use for building after the source is ready (bsp-image-build and later skills), or for S-series source acquisition (bsp-s-series).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, repo, manifest, source-sync]
  data-classification: public
---

# BSP Source Sync

## Purpose

Bring down the full RDK Linux source tree — kernel, bootloader, and all `hobot-*` package sources — so the other bsp-* skills can build from it. The entry point is the Google `repo` tool plus a board-specific manifest.

## When to use

Use when:
- Starting a new BSP workspace (`repo init` / `repo sync`)
- Switching between the `main` (stable, matches the latest released image) and `develop` (rolling) branches
- `repo sync` fails or the user asks where the source lives

Do not use:
- For S-series source acquisition — `bsp-s-series`
- For building once sources exist — `bsp-image-build` etc.

## Instructions

1. Confirm the target board first: **X5 → `x5-manifest`**, **X3 → `manifest`**. The manifests are different; mixing them breaks the workspace.

2. Prerequisites (from `bsp-env-setup`): GitHub SSH key registered, `repo` installed.

3. Optional but recommended in China: switch repo to the Tsinghua mirror:
   ```bash
   export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo/'
   ```

4. Initialize the manifest (main line matches the latest officially released image version):
   ```bash
   # RDK X5
   repo init -u git@github.com:D-Robotics/x5-manifest.git -b main
   # RDK X3
   repo init -u git@github.com:D-Robotics/manifest.git -b main
   ```

5. Sync the code:
   ```bash
   repo sync
   ```

6. After the sync, the build workspace contains the `rdk-gen` scripts plus a `source/` tree (bootloader, hobot-boot, hobot-dtb, hobot-kernel-headers, hobot-* packages, kernel). Report what landed and where.

7. Branch guidance: `-b develop` gets the rolling development line (new features and fixes, less stable than `main`). Mention this when the user asks for the newest code.

## Safety

- `repo init` writes a `.repo/` workspace and network volume is large: confirm disk space (tens of GB) and the working directory with the user first.
- Never mix manifests in one workspace — check `.repo/manifests.git` origin before re-init.
- Cloning uses SSH (`git@github.com`): if it fails with permission errors, that is a GitHub SSH-key problem (see `bsp-env-setup`), not a manifest problem.

> Sources: `x5-rdk-gen` README v3.5.0「下载源码」chapter; `rdk-gen` README v3.0.3「下载源码」chapter.
