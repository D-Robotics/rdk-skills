---
name: bsp-image-build
description: Build a complete RDK X3/X5 system image with pack_image.sh after explicitly selecting board, desktop/server, beta/release, checkout, free space, and any third-party deb. Use when the user wants a flashable RDK OS image or preinstalled debs. 触发词:系统镜像、整机镜像、pack_image.sh、desktop/server 版本、build_params、third_packages、.img. Do not use for kernel-only builds (bsp-kernel-build), deb-only builds (bsp-deb-build), or S-series (bsp-s-series).
version: 1.0.0
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
- The user wants a complete, flashable RDK X3 or X5 image
- The user wants a third-party `.deb` preinstalled in that image
- The user needs to select the desktop/server and beta/release image variant

If the request is only to build, rebuild, or obtain a deb package (including a
changed `hobot-multimedia` deb), route to `bsp-deb-build`. Do not suggest or
run an image build command for package-only work. Do not use this skill for
kernel-, bootloader-, or S-series-only work.

## Instructions

1. Classify the work. Confirm the user needs a complete image, not only a deb.
   For package-only requests, hand off to `bsp-deb-build` before discussing
   `pack_image.sh`.

2. Before planning a build, collect and repeat these explicit selections:
   - board: `X3` or `X5`
   - Ubuntu flavor: `desktop` or `server`
   - release channel: `beta` or `release`
   - source checkout: the absolute prepared `x5-rdk-gen` or legacy `rdk-gen`
     checkout path (do not assume the current directory)
   - intended third-party deb: its exact path, or explicit confirmation that
     none is to be preinstalled

3. Confirm prerequisites for that checkout: `bsp-env-setup` and
   `bsp-source-sync` completed, `sudo` available, and at least roughly 50 GB
   of free space on the filesystem holding the checkout. Check the available
   space instead of inferring it from total disk capacity.

4. Derive and show the exact selected configuration before any build command:
   ```text
   build_params/ubuntu-22.04_{desktop|server}_rdk-{x3|x5}_{beta|release}.conf
   ```
   For example, X5 desktop release selects
   `build_params/ubuntu-22.04_desktop_rdk-x5_release.conf`. Verify that exact
   file exists under the chosen checkout's `build_params/` directory.

5. If a third-party deb is requested, before the costly-build confirmation
   verify that its exact path exists and is a readable regular file. Only after
   those checks, optionally inspect its package metadata/architecture to
   validate board compatibility, then put that exact file in
   `<checkout>/third_packages/`. The pack process installs debs from that
   directory into the image filesystem.

6. Explain the cost and request an explicit confirmation. Image output uses
   substantial time and storage, downloads gigabytes on a first full build,
   and runs with `sudo`. Do not invoke `pack_image.sh` until the user confirms
   the selected config, checkout, free-space result, and third-party-deb plan.

7. After that confirmation, run from the chosen checkout:
   ```bash
   sudo ./pack_image.sh -c "<selected build_params file from step 4>"
   ```
   Substitute the exact selected config from step 4; never silently fall back
   to the default config or copy a config for another variant.

8. Useful options:
   - `-l` — local build: skip downloading samplefs and deb packages from the official server (use after the first full build, for fast iteration)
   - `-c <file>` — select a build config

9. What `pack_image.sh` does (report this to the user):
   1. `download_samplefs.sh` + `download_deb_pkgs.sh` fetch the official base filesystem and preinstalled debs
   2. unpack samplefs and run `hobot_customize_rootfs.sh` to customize the filesystem
   3. install deb packages into the filesystem
   4. generate the system image

10. Verify the outputs under `deploy/` — `*.img` image files plus rootfs,
    kernel intermediates. Report the exact `.img` path and size.

## Safety

- Runs as sudo and downloads gigabytes: confirm the explicit X3/X5,
  desktop/server, beta/release, checkout, free-space result, selected config,
  and third-party deb plan before starting `pack_image.sh`.
- `-l` reuses previously downloaded artifacts; if those are missing the build fails — rerun a full build once.
- Never use an image build as a substitute for package-only work; use
  `bsp-deb-build` to rebuild the deb first, then return here only if the user
  wants it preinstalled in a complete image.
- Building does not flash anything: hand the `.img` to the official flashing docs / `rdk-board-knowledge`, never flash without user confirmation.

> Sources: `x5-rdk-gen` README v3.5.0「编译系统镜像」「pack_image.sh 打包步骤」; `rdk-gen` README v3.0.3「编译系统镜像」; `x5-rdk-gen/build_params/` config file list.
