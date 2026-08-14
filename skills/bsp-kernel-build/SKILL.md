---
name: bsp-kernel-build
description: Build the RDK Linux kernel, device tree, and driver modules with mk_kernel.sh (X5 also offers mk_kernel_rt.sh for the real-time kernel). Use when the user wants to compile the kernel, rebuild dtb, add driver modules, or needs kernel_headers for out-of-tree builds. 触发词:编译内核、内核、设备树、dtb、驱动模块、mk_kernel、实时内核、RT 内核、kernel headers. Do not use for full images (bsp-image-build), deb packaging (bsp-deb-build), or S-series (bsp-s-series).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, kernel, dtb, drivers, rt-kernel]
  data-classification: public
---

# Kernel, Device Tree, and Driver Build

## Purpose

Compile the Linux kernel, device tree, and driver modules, and understand how their outputs feed the `hobot-boot` / `hobot-dtb` / `hobot-kernel-headers` deb packages. Kernel work is the entry point for most deep BSP customization (device tree changes, new drivers, RT requirements).

## When to use

Use when:
- The user wants to build/modify the kernel, dtb, or driver modules
- The kernel artifacts (`deploy/kernel`) are missing but deb packages are needed
- Setting up out-of-tree module builds that need `kernel_headers`

Do not use for the whole image build or deb-only rebuilds — sibling skills handle those.

## Instructions

1. Prerequisites: one completed full image build (`bsp-image-build`) — it downloads the rootfs whose headers/libraries application packages use, plus the official debs.

2. Run the kernel build from the workspace root:
   ```bash
   ./mk_kernel.sh          # kernel, dtb, driver modules
   ./mk_kernel_rt.sh       # X5 only: real-time kernel
   ```

3. Verify outputs in `deploy/kernel`:
   ```
   dtb  Image  Image.lz4  kernel_headers  modules
   ```

4. Explain the dependency chain (report this to the user): these outputs are consumed by the `hobot-boot`, `hobot-dtb`, and `hobot-kernel-headers` deb packages — so any customization of those three packages requires rebuilding the kernel first, then `bsp-deb-build`.

5. For driver development: point the user to `deploy/kernel/kernel_headers` for out-of-tree module builds; do not invent include paths.

## Safety

- Kernel builds are CPU/disk heavy: confirm available resources before a long run.
- Do not modify kernel configs or dts files without showing the diff and getting user confirmation.
- RT kernel (`mk_kernel_rt.sh`) changes scheduling behavior on the target — flag the difference before switching.

> Sources: `x5-rdk-gen` README v3.5.0「编译 kernel」; `rdk-gen` README v3.0.3「编译 kernel」。
