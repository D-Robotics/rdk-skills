---
name: bsp-deb-build
description: Rebuild one supported official hobot-* Debian package with mk_debs.sh (for example hobot-boot, hobot-dtb, or hobot-multimedia). Use when the user wants to repackage a component or asks which packages can be built. Package output is not a flashable image; hand image assembly to bsp-image-build after the .deb exists. 触发词:hobot-* 包、mk_debs、deb 包、重新打包、hobot-boot、hobot-configs. Do not use for kernel compilation itself (bsp-kernel-build) or full images (bsp-image-build).
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, deb, hobot, packaging]
  data-classification: public
---

# hobot-* Deb Package Build

## Purpose

Rebuild one official D-Robotics Debian package (`hobot-*`) from its sources in the `source/` tree. These packages carry the kernel image, dtb, kernel headers, multimedia libraries, samples, and system configs that can later be preinstalled into system images.

`mk_debs.sh` produces `.deb` packages only. It does **not** create a flashable image.

## When to use

Use when:
- A `hobot-*` source package was modified and needs repackaging
- The user needs a rebuilt package for an image assembler or a compatible board
- Listing which packages the build system supports

Do not use for compiling the kernel itself or assembling a whole image. For a flashable image, use `bsp-image-build` only after this workflow has produced the requested `.deb`.

## Instructions

1. Collect and confirm all required request details before running a build:
   - Exact package name (one supported `hobot-*` identifier)
   - Target board and BSP source branch/release used by the checkout
   - Intended artifact consumer: a compatible board install or `bsp-image-build`
   - Available free disk space for build outputs
   If any detail is missing, ask for it; do not assume a board, branch, consumer, or disk capacity.

2. Prerequisite: kernel artifacts must exist first (see `bsp-kernel-build`) — the build system uses them for `hobot-boot`, `hobot-dtb`, `hobot-kernel-headers`.

3. Validate the requested package against the supported list below. If it is not listed, ask the user to choose a supported package or inspect the checkout's build metadata/help text; never invent a `mk_debs.sh` command.

4. Build the validated package:
   ```bash
   ./mk_debs.sh <package-name>
   ```
   The package output lands in `deploy/deb_pkgs/*.deb`.

5. Supported package names (from the official README help text):
   `hobot-boot` `hobot-kernel-headers` `hobot-dtb` `hobot-configs` `hobot-utils` `hobot-display` `hobot-wifi` `hobot-io` `hobot-io-samples` `hobot-multimedia` `hobot-multimedia-dev` `hobot-camera` `hobot-dnn` `hobot-spdev` `hobot-sp-samples` `hobot-multimedia-samples` `hobot-miniboot` `hobot-audio-config`
   For any other name the script answers "not supported" — report that verbatim instead of guessing.

6. Hand off based on the stated consumer:
   - For a compatible board install, provide the selected `deploy/deb_pkgs/*.deb` and confirm board compatibility before `dpkg -i`.
   - For a flashable image, first verify that the requested `.deb` exists, then place it in `third_packages/` and route the user to `bsp-image-build` for board, desktop/server, and release-image selections. Do not claim that `mk_debs.sh` assembled or flashed an image.

## Safety

- Wrong package name errors are informational — never edit `mk_debs.sh` to "add" a package without discussing with the user.
- Packages built from a dirty source tree silently carry uncommitted changes — ask the user to review `git status` in `source/` first.
- Mixing X3 and X5 artifacts in one workspace corrupts packages — confirm the workspace matches the target board.
- Stop before a build if free disk space is unknown or insufficient for the user's checkout and output retention needs; do not delete existing artifacts to make room without approval.

> Sources: `x5-rdk-gen` README v3.5.0「编译 RDK 官方 debian 软件包」; `rdk-gen` README v3.0.3「编译 debian 软件包」。
