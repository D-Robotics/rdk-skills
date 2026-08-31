---
name: bsp-source-sync
description: Sync the RDK Linux source tree (kernel, bootloader, hobot-* package sources) using repo and the official manifests — X5 uses D-Robotics/x5-manifest, X3 uses D-Robotics/manifest. Use when the user wants to download/checkout the BSP source, switch branches, or repo init/sync fails. 触发词:repo init、repo sync、同步源码、下载源码、manifest、源码树、develop 分支. Do not use for building after the source is ready (bsp-image-build and later skills), or for S-series source acquisition (bsp-s-series).
version: 1.0.0
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
- For S-series source acquisition — hand off to `bsp-s-series`.
- For image-only requests or building once sources exist — hand off to `bsp-image-build`.

## Instructions

1. Route before collecting details. S-series acquisition belongs to `bsp-s-series`; an image-only build belongs to `bsp-image-build`. Do not start a source sync for either request.

2. Before proposing any `repo init` or `repo sync`, obtain all of the following explicitly:
   - board family: **X5 → `D-Robotics/x5-manifest`**; **X3 → `D-Robotics/manifest`**;
   - manifest branch: normally `main`, or `develop` only when the user accepts its rolling, less-stable nature;
   - exact, absolute target directory;
   - available free disk space (the source sync needs tens of GB and substantial network bandwidth);
   - whether local changes may be overwritten. If the workspace has local work, ask whether it must be preserved and whether backup/stash is authorized.

3. Prerequisites (from `bsp-env-setup`): GitHub SSH key registered and `repo` installed. Optional in China, the repo client itself can use the Tsinghua mirror:
   ```bash
   export REPO_URL='https://mirrors.tuna.tsinghua.edu.cn/git/git-repo/'
   ```

4. For an existing checkout, inspect before making a change. Check the current manifest origin and active project/local-work state; never mix manifests in one directory. Explain any branch drift between the current checkout and the requested manifest branch. If local work exists, offer a user-approved backup (for example, patches, a commit, or a stash) before a branch switch or synchronization. Do not create a backup or alter the checkout without that approval.
   ```bash
   cd <target-directory>
   git -C .repo/manifests.git remote -v
   repo status
   repo forall -c 'git status --short'
   ```

5. Present a preflight summary: board family and manifest URL, requested branch, exact target directory, observed local-work/branch-drift state, available disk, and the expected large network transfer. For an existing checkout, changing the manifest branch may move project revisions; `repo sync` may update many projects. Ask for one explicit confirmation that includes permission to proceed with the requested branch change and sync.

6. Only after the explicit confirmation, initialize the selected manifest (the `main` line matches the latest officially released image version) and sync:
   ```bash
   # RDK X5
   repo init -u git@github.com:D-Robotics/x5-manifest.git -b <main-or-develop>
   # RDK X3
   repo init -u git@github.com:D-Robotics/manifest.git -b <main-or-develop>

   repo sync
   ```

7. After the sync, report what landed and where: the `rdk-gen` scripts plus the `source/` tree (bootloader, hobot-boot, hobot-dtb, hobot-kernel-headers, `hobot-*` packages, and kernel).

## Safety

- Do not run `repo init -b …` in an existing checkout or run a large `repo sync` until the user has explicitly confirmed the reviewed preflight summary.
- An existing checkout requires a manifest-origin check, local-change inspection, and a user-approved preservation decision before a branch switch or synchronization. Do not assume that local work may be overwritten.
- `develop` is a rolling development line. Warn that it can diverge from the current project branches and is less stable than `main`.
- `repo init` writes a `.repo/` workspace and `repo sync` transfers tens of GB: confirm the target directory, available disk, and bandwidth impact first.
- Cloning uses SSH (`git@github.com`): if it fails with permission errors, that is a GitHub SSH-key problem (see `bsp-env-setup`), not a manifest problem.

> Sources: `x5-rdk-gen` README v3.5.0「下载源码」chapter; `rdk-gen` README v3.0.3「下载源码」chapter.
