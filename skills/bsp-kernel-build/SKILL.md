---
name: bsp-kernel-build
description: Build RDK Linux kernel, device-tree, and driver-module artifacts with mk_kernel.sh (X5 also offers mk_kernel_rt.sh). Require board family, target, config source, and deployment target; confirm boot replacement or reboot. Use for kernel/DTB/module/RT work, not full images (bsp-image-build), deb packaging (bsp-deb-build), or S-series (bsp-s-series).
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, kernel, dtb, drivers, rt-kernel]
  data-classification: public
---

# Kernel, Device Tree, and Driver Build

## Purpose

Compile Linux kernel, device-tree, and driver-module artifacts, and understand how
they feed the `hobot-boot` / `hobot-dtb` / `hobot-kernel-headers` deb packages.
This skill produces kernel artifacts; it does not build a complete flashable image
or deploy artifacts to a board.

## When to use

Use when:
- The user wants to build/modify the kernel, dtb, or driver modules
- The kernel artifacts (`deploy/kernel`) are missing but deb packages are needed
- Setting up out-of-tree module builds that need `kernel_headers`

For a complete flashable or release image, route to `bsp-image-build` before
suggesting `mk_kernel.sh`. For creation or rebuilding of a `hobot-*` deb
package, route to `bsp-deb-build` after the required kernel artifacts exist.
Do not use this skill for a whole-image build, deb-only rebuild, or S-series work.

## Instructions

1. Classify the request before offering a command:
   - A complete flashable or release image belongs to `bsp-image-build`; do not
     present `mk_kernel.sh` as the terminal answer.
   - Creation or rebuilding of `hobot-boot`, `hobot-dtb`, or
     `hobot-kernel-headers` packages belongs to `bsp-deb-build`. This skill
     supplies its prerequisite kernel artifacts.
   - Otherwise, continue only for a kernel, DTB, driver-module, or X5 RT-kernel
     artifact request.

2. Before planning the build, collect and repeat all of these required inputs:
   - board family and board variant: `X3` or `X5`, plus the exact target board;
   - kernel target: `kernel`, `DTB`, `module`, or `RT`;
   - configuration source: the exact DTS, defconfig/config fragment, or known-good
     configuration path/revision to use; and
   - deployment target: the intended board and delivery method (for example, a
     `hobot-dtb` package install or a boot-partition replacement).

   Also require a rollback method before any deployment plan: identify how the
   current Image/DTB will be backed up and restored, or an approved alternate
   boot/recovery path. Do not infer the board, configuration, delivery method,
   or rollback procedure from the current checkout.

3. Inspect the selected DTS/configuration diff and confirm the intended board
   configuration before changing source files or starting a build.

4. Prerequisite: one completed full image build (`bsp-image-build`) — it downloads the rootfs whose headers/libraries application packages use, plus the official debs.

5. After the inputs and source diff are confirmed, run the artifact build from
   the selected workspace root. `mk_kernel.sh` builds kernel, DTB, and modules
   together; do not invent a narrower command for a DTB-only or module-only
   request.
   ```bash
   ./mk_kernel.sh          # kernel, dtb, driver modules
   ./mk_kernel_rt.sh       # X5 only: real-time kernel
   ```
   Use `mk_kernel_rt.sh` only when the selected target is `RT` and the board
   family is X5. Explain its scheduling impact and obtain explicit confirmation
   before the long RT build.

6. Verify outputs in `deploy/kernel`:
   ```
   dtb  Image  Image.lz4  kernel_headers  modules
   ```

7. Explain the dependency chain: these outputs are consumed by the
   `hobot-boot`, `hobot-dtb`, and `hobot-kernel-headers` deb packages — so any
   customization of those packages requires rebuilding the kernel first, then
   handing off package creation to `bsp-deb-build`.

8. For driver development, point the user to `deploy/kernel/kernel_headers` for
   out-of-tree module builds; do not invent include paths.

9. Stop before deployment. Do not provide or execute a board-side install,
   boot-partition/Image/DTB replacement, or reboot command until the deployment
   target and rollback method have been explicitly confirmed. Replacing boot
   artifacts or rebooting is confirmation-required even after the build
   succeeds. Then use the board-specific, supported deployment procedure rather
   than assuming partition names or paths.

## Safety

- Kernel builds are CPU/disk heavy: confirm available resources before a long run.
- Do not modify kernel configs or DTS files without showing the diff and getting user confirmation.
- RT kernel (`mk_kernel_rt.sh`) changes scheduling behavior on the target — flag the difference and obtain confirmation before switching.
- Never overwrite a boot partition, Image, or DTB, and never reboot a board,
  without explicit confirmation of the deployment target and a tested or
  documented rollback method. Preserve the current boot artifacts first.

> Sources: `x5-rdk-gen` README v3.5.0「编译 kernel」; `rdk-gen` README v3.0.3「编译 kernel」。
