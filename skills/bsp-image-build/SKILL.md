---
name: bsp-image-build
description: Build an RDK system image identical to the official release using pack_image.sh — choose a build_params config (ubuntu-22.04 desktop/server × rdk-x5/rdk-x3 × beta/release), local build mode -l, and third_packages preinstalls. Use when the user wants to build/flash-able RDK OS image, customize preinstalled debs, or asks what pack_image.sh does. 触发词:系统镜像、整机镜像、pack_image.sh、desktop/server 版本、build_params、third_packages、.img. Do not use for kernel-only builds (bsp-kernel-build), deb-only builds (bsp-deb-build), or S-series (bsp-s-series).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, image, pack_image, rootfs]
  data-classification: public
---

# System Image Build

## Purpose

Produce a complete, flash-able RDK OS image (`.img`) that matches the official release, by orchestrating the official `pack_image.sh` entry point. This is the first build every BSP developer must complete before any deep development — it downloads the base filesystem and official debs that later steps depend on.

## When to use

Use when:
- The user wants to build the full system image for RDK X5 or X3
- Choosing desktop vs server, beta vs release
- Preinstalling extra deb packages into the image

Do not use for kernel/deb/bootloader-only builds or for S-series — see the sibling skills.

## Instructions

1. Confirm prerequisites: `bsp-env-setup` and `bsp-source-sync` completed, `sudo` available, ~50 GB+ free disk.

2. Identify the workspace:
   - X5: `x5-rdk-gen` (v3.5.0; its `build_params/` also ships rdk-x3 configs)
   - X3 legacy: `rdk-gen` (v3.0.3)

3. Build with the default config, or select one:
   ```bash
   sudo ./pack_image.sh                       # default config
   sudo ./pack_image.sh -c build_params/ubuntu-22.04_desktop_rdk-x5_release.conf
   ```
   Available configs in `x5-rdk-gen/build_params/`: `ubuntu-22.04_{desktop,server}_rdk-{x3,x5}_{beta,release}.conf`.

4. Useful options:
   - `-l` — local build: skip downloading samplefs and deb packages from the official server (use after the first full build, for fast iteration)
   - `-c <file>` — select a build config

5. Preinstall your own debs: create a `third_packages/` directory in the workspace root and drop the `.deb` files there — they are installed into the filesystem during step 3 of the pack process.

6. What pack_image.sh does (report this to the user):
   1. `download_samplefs.sh` + `download_deb_pkgs.sh` fetch the official base filesystem and preinstalled debs
   2. unpack samplefs and run `hobot_customize_rootfs.sh` to customize the filesystem
   3. install deb packages into the filesystem
   4. generate the system image

7. Verify the outputs under `deploy/` — `*.img` image files plus rootfs, kernel intermediates. Report the exact `.img` path and size.

## Safety

- Runs as sudo and downloads gigabytes: confirm disk space and the chosen config with the user before starting.
- `-l` reuses previously downloaded artifacts; if those are missing the build fails — rerun a full build once.
- Building does not flash anything: hand the `.img` to the official flashing docs / `rdk-board-knowledge`, never flash without user confirmation.

> Sources: `x5-rdk-gen` README v3.5.0「编译系统镜像」「pack_image.sh 打包步骤」; `rdk-gen` README v3.0.3「编译系统镜像」; `x5-rdk-gen/build_params/` config file list.
