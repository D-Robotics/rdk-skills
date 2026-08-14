---
name: bsp-deb-build
description: Rebuild the official hobot-* debian packages with mk_debs.sh (all or a named package like hobot-boot / hobot-dtb / hobot-multimedia). Use when the user wants to repackage a hobot-* component, inject fixes into the image via deb, or asks which packages can be built. 触发词:hobot-* 包、mk_debs、deb 包、重新打包、hobot-boot、hobot-configs. Do not use for kernel compilation itself (bsp-kernel-build) or full images (bsp-image-build).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, deb, hobot, packaging]
  data-classification: public
---

# hobot-* Deb Package Build

## Purpose

Rebuild the official D-Robotics debian packages (`hobot-*`) from their sources in the `source/` tree. These packages carry the kernel image, dtb, kernel headers, multimedia libraries, samples, and system configs that get preinstalled into system images.

## When to use

Use when:
- A `hobot-*` source package was modified and needs repackaging
- The user wants to inject a fixed package into the image instead of a full rebuild
- Listing which packages the build system supports

Do not use for compiling the kernel itself or the whole image.

## Instructions

1. Prerequisite: kernel artifacts must exist first (see `bsp-kernel-build`) — the build system uses them for `hobot-boot`, `hobot-dtb`, `hobot-kernel-headers`.

2. Build everything:
   ```bash
   ./mk_kernel.sh
   ./mk_debs.sh
   ```
   Outputs land in `deploy/deb_pkgs/*.deb`.

3. Build a single package by name:
   ```bash
   ./mk_debs.sh hobot-configs
   ```

4. Supported package names (from the official README help text):
   `hobot-boot` `hobot-kernel-headers` `hobot-dtb` `hobot-configs` `hobot-utils` `hobot-display` `hobot-wifi` `hobot-io` `hobot-io-samples` `hobot-multimedia` `hobot-multimedia-dev` `hobot-camera` `hobot-dnn` `hobot-spdev` `hobot-sp-samples` `hobot-multimedia-samples` `hobot-miniboot` `hobot-audio-config`
   For any other name the script answers "not supported" — report that verbatim instead of guessing.

5. To get a rebuilt package into an image: drop the `.deb` into `third_packages/` before `bsp-image-build`, or use it directly for on-board `dpkg -i` if the user asks (confirm target board compatibility first).

## Safety

- Wrong package name errors are informational — never edit `mk_debs.sh` to "add" a package without discussing with the user.
- Packages built from a dirty source tree silently carry uncommitted changes — ask the user to review `git status` in `source/` first.
- Mixing X3 and X5 artifacts in one workspace corrupts packages — confirm the workspace matches the target board.

> Sources: `x5-rdk-gen` README v3.5.0「编译 RDK 官方 debian 软件包」; `rdk-gen` README v3.0.3「编译 debian 软件包」。
