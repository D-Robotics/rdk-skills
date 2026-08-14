---
name: bsp-bootloader-build
description: Build the minimal boot image (miniboot / nand_disk.img) from the bootloader source using xbuild.sh lunch — covers selecting the board config and compiling uboot/miniboot for RDK X5. Use when the user wants to rebuild bootloader/miniboot, asks what nand_disk.img is, or needs a custom minimal boot firmware. 触发词:miniboot、bootloader、uboot、nand_disk.img、xbuild、最小启动镜像. Do not use for kernel or full image builds; X3 flow is not yet documented — say so instead of guessing.
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, bootloader, miniboot, uboot]
  data-classification: public
---

# Bootloader / miniboot Build

## Purpose

Build the RDK minimal boot firmware (`miniboot.img` / `nand_disk.img`): the image containing the partition table, spl, ddr, bl31, and uboot that runs before the OS. This is the most foundational BSP component — modifying it requires understanding the boot process.

## When to use

Use when:
- The user wants to rebuild the bootloader / miniboot for **RDK X5**
- Explaining what `nand_disk.img` / `miniboot_all.img` are
- The user needs a custom minimal boot firmware

Do not use:
- For X3 — the bootloader build steps for X3 are not documented in the official build README; say so and point to official docs rather than guessing
- For kernel/image builds — sibling skills

## Instructions

1. Prerequisites: `bsp-source-sync` completed; `source/bootloader` present.

2. Select the board config:
   ```bash
   cd source/bootloader/build
   ./xbuild.sh lunch
   ```
   The lunch menu offers (X5):
   ```
   0. rdk/x5/board_x5_rdk_ubuntu_nand_sdcard_debug_config.mk
   1. rdk/x5/board_x5_rdk_ubuntu_nand_sdcard_release_config.mk
   ```
   `lunch` also accepts a number or the config file name:
   ```bash
   ./xbuild.sh lunch 0
   ./xbuild.sh lunch board_x5_rdk_ubuntu_nand_sdcard_debug_config.mk
   ```

3. Build everything:
   ```bash
   ./xbuild.sh
   ```

4. Verify the outputs under `out/product/`: `nand_disk.img` (the minimal boot image), `uboot.img`, `miniboot_all.img`.

5. Note for the user: official releases maintain miniboot — downloadable from `https://archive.d-robotics.cc/downloads/miniboot/` (the `hobot-miniboot` package follows the same versions). Rebuilding is only needed for bootloader customization.

## Safety

- Bootloader bugs brick boards: recommend against rebuilding unless the user explicitly needs it; always remind them official miniboot images exist.
- Never flash a locally built miniboot without user confirmation and a recovery plan (official miniboot at hand).
- Quote the lunch menu verbatim; do not invent configs for boards not listed.

> Sources: `x5-rdk-gen` README v3.5.0「编译 bootloader」。
