---
name: bsp-env-setup
description: Prepare a supported Ubuntu host for RDK X3/X5 BSP development when a user needs build packages, the gcc-arm-11.2 aarch64 toolchain, repo, or GitHub SSH access. Use for missing-build-tool errors (make/cmake/bc/bison not found, toolchain missing). 触发词:BSP 环境、编译环境搭建、交叉编译工具链、gcc-arm-11.2、repo 工具、build 机器准备. Do not use for S-series environments (bsp-s-series) or for building images/kernels directly (bsp-image-build / bsp-kernel-build).
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, toolchain, cross-compile, ubuntu, repo]
  data-classification: public
---

# BSP Host Environment Setup

## Purpose

Set up a supported Ubuntu development host so it can cross-compile the RDK Linux system for X3/X5. Covers the three prerequisites every other bsp-* skill assumes: Ubuntu build packages, the aarch64 cross toolchain installed under `/opt`, and the `repo` tool with GitHub SSH access.

## When to use

Use when:
- The user wants to prepare a new build machine for RDK X3/X5 BSP work
- Build tools are missing (`make`, `bc`, `bison`, `flex`, `device-tree-compiler` … not found)
- `repo init` fails because `repo` or SSH keys are not configured

Do not use:
- S-series (S100/S600) environments — `bsp-s-series`
- Actually building an image/kernel — `bsp-image-build` / `bsp-kernel-build`

## Instructions

1. **Preflight gate — stop unless every condition passes.** Before emitting any package, toolchain, `repo`, `curl`, or SSH command, obtain all of the following from the user:
   - **Target route:** For S100 or S600, stop and route the request to `bsp-s-series`; do not apply this X3/X5 host flow.
   - **Supported host:** The build host is x86_64 Ubuntu 22.04. Windows, macOS, containers without a supported Ubuntu host, and unverified Ubuntu releases fail this gate. Direct the user to provision or use a supported Ubuntu 22.04 build host; do not provide installation commands.
   - **Disk capacity:** The filesystem planned for source sync and builds has at least **100 GB free**. 30 GB is insufficient. If the threshold is not met or cannot be confirmed, stop and ask the user to free space or choose a larger Ubuntu build volume; do not provide installation commands.
   - **Network and repository access:** The host can reach `archive.d-robotics.cc`, and the user's GitHub SSH key is registered and accepted by `git@github.com`. If either is unavailable, stop and ask the user to restore network access or register/test the SSH key; do not provide installation commands.
   - **Explicit approval:** Explain that the next steps install packages with `sudo` and extract a toolchain under `/opt`. Continue only after the user explicitly confirms both the passed preflight facts and approval for those changes.

   A failed or incomplete gate receives remediation only—never a partial command list. Ubuntu 20.04/18.04 have version-specific package lists in the source READMEs; treat them as unsupported for the Ubuntu 22.04 commands below and direct the user to the matching documentation.

2. **After the gate passes and approval is explicit**, install the host build packages (Ubuntu 22.04 list from `x5-rdk-gen` README):
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

4. Verify the preflight network and GitHub SSH access (source sync clones private repos via SSH):
   ```bash
   ssh -T git@github.com
   ```

5. Verify the environment and report:
   ```bash
   /opt/gcc-arm-11.2-2022.02-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-gcc --version
   repo version
   ```
   Report each check as pass/fail with the exact output. Do not continue to `bsp-source-sync` if any check fails.

## Safety

- The preflight gate is mandatory. Windows, insufficient disk, unavailable network/SSH, or missing explicit approval means no package or toolchain commands.
- All installs run as `sudo` on the user's host: show each command only after the gate passes and get confirmation before changing the host or `/opt`.
- Never remove or overwrite an existing toolchain directory without user confirmation.
- The toolchain URL is the official archive server; do not substitute other sources.
- This skill only prepares the host — it never touches boards.

> Sources: `x5-rdk-gen` README v3.5.0「开发环境」chapter; `rdk-gen` README v3.0.3「开发环境」chapter; GitHub SSH-key guide linked from both READMEs.
