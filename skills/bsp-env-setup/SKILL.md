---
name: bsp-env-setup
description: Prepare the host cross-compilation environment for RDK BSP development — Ubuntu host packages, the gcc-arm-11.2 aarch64 toolchain under /opt, the repo tool, and GitHub SSH keys. Use when the user wants to set up a build machine for RDK X3/X5 system development, or hits missing-build-tool errors (make/cmake/bc/bison not found, toolchain missing). 触发词:BSP 环境、编译环境搭建、交叉编译工具链、gcc-arm-11.2、repo 工具、build 机器准备. Do not use for S-series environments (bsp-s-series) or for building images/kernels directly (bsp-image-build / bsp-kernel-build).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, toolchain, cross-compile, ubuntu, repo]
  data-classification: public
---

# BSP Host Environment Setup

## Purpose

Set up a Linux development host so it can cross-compile the RDK Linux system for X3/X5. Covers the three prerequisites every other bsp-* skill assumes: Ubuntu build packages, the aarch64 cross toolchain installed under `/opt`, and the `repo` tool with GitHub SSH access.

## When to use

Use when:
- The user wants to prepare a new build machine for RDK X3/X5 BSP work
- Build tools are missing (`make`, `bc`, `bison`, `flex`, `device-tree-compiler` … not found)
- `repo init` fails because `repo` or SSH keys are not configured

Do not use:
- S-series (S100/S600) environments — `bsp-s-series`
- Actually building an image/kernel — `bsp-image-build` / `bsp-kernel-build`

## Instructions

1. Confirm the host OS. Recommended: Ubuntu 22.04 (same version as the RDK X5 system, minimizes dependency drift). Ubuntu 20.04/18.04 are documented in the source READMEs with their own package lists.

2. Install the host build packages (Ubuntu 22.04 list from `x5-rdk-gen` README):
   ```bash
   sudo apt-get install -y build-essential make cmake libpcre3 libpcre3-dev bc bison \
                           flex python3-numpy python3-pip mtd-utils zlib1g-dev debootstrap \
                           libdata-hexdumper-perl libncurses5-dev zip qemu-user-static \
                           curl repo git liblz4-tool apt-cacher-ng libssl-dev checkpolicy autoconf \
                           android-sdk-libsparse-utils mtools parted dosfstools udev rsync device-tree-compiler u-boot-tools ccache
   ```

3. Install the cross toolchain under `/opt`:
   ```bash
   curl -fO http://archive.d-robotics.cc/toolchain/gcc-arm-11.2-2022.02-x86_64-aarch64-none-linux-gnu.tar.xz
   sudo tar -xvf gcc-arm-11.2-2022.02-x86_64-aarch64-none-linux-gnu.tar.xz -C /opt
   ```

4. Ensure GitHub SSH access (source sync clones private repos via SSH):
   - User must have a GitHub account and add the dev server's SSH key per the official guide
   - Verify with `ssh -T git@github.com`

5. Verify the environment and report:
   ```bash
   /opt/gcc-arm-11.2-2022.02-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc --version
   repo version
   ```
   Report each check as pass/fail with the exact output. Do not continue to `bsp-source-sync` if any check fails.

## Safety

- All installs run as `sudo` on the user's host: show each command before running and get confirmation.
- Never remove or overwrite an existing toolchain directory without user confirmation.
- The toolchain URL is the official archive server; do not substitute other sources.
- This skill only prepares the host — it never touches boards.

> Sources: `x5-rdk-gen` README v3.5.0「开发环境」chapter; `rdk-gen` README v3.0.3「开发环境」chapter; GitHub SSH-key guide linked from both READMEs.
