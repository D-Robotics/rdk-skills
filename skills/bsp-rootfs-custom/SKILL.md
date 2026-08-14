---
name: bsp-rootfs-custom
description: Make and customize the RDK Ubuntu root filesystem — samplefs/make_ubuntu_rootfs.sh (desktop/server), debootstrap/chroot tooling, the package-list variables (BASE/DESKTOP/SERVER_PACKAGE_LIST…), and hobot_customize_rootfs.sh for users/services. Use when the user wants to build a custom samplefs, add/remove preinstalled apt or python packages, or create users/autostart entries in the image. 触发词:根文件系统、rootfs、samplefs、debootstrap、定制系统、预装软件包、创建用户、自启动. Do not use for whole-image builds (bsp-image-build) or S-series (bsp-s-series).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, rootfs, samplefs, debootstrap]
  data-classification: public
---

# Ubuntu Rootfs Customization

## Purpose

Build and customize the Ubuntu root filesystem that system images are assembled from. Two levels of customization exist: generating a fresh samplefs with `make_ubuntu_rootfs.sh`, and per-image tweaks via `hobot_customize_rootfs.sh` (users, services).

## When to use

Use when:
- The user wants a custom samplefs (desktop or server) with different preinstalled packages
- Adding users or enabling/disabling autostart services in the image
- Explaining what debootstrap/chroot do in this flow

Do not use for the full image pipeline or S-series.

## Instructions

1. Prerequisites: `bsp-env-setup`; for the full samplefs host dependency list (debootstrap, parted, qemu-user-static, …) quote the source README's「环境配置」package list instead of abbreviating it.

2. Generate the Ubuntu root filesystem:
   ```bash
   cd samplefs
   chmod +x make_ubuntu_rootfs.sh
   sudo ./make_ubuntu_rootfs.sh          # desktop (default)
   sudo ./make_ubuntu_rootfs.sh server   # server edition
   ```
   Outputs (X5): `desktop/jammy-rdk-arm64`, `desktop/samplefs_desktop_jammy-v3.0.0.tar.gz`, `…tar.gz.info` (installed apt list).
   Outputs (X3 legacy): `desktop/jammy-xj3-arm64`, `samplefs_desktop-v3.0.0.tar.gz`, `…info`.

3. Customize the package set via the documented variables in the make script:
   - `PYTHON_PACKAGE_LIST` — python packages to install
   - `DEBOOTSTRAP_LIST` — debootstrap-time debian packages
   - `BASE_PACKAGE_LIST` — minimal Ubuntu base packages
   - `SERVER_PACKAGE_LIST` — extras for the server edition
   - `DESKTOP_PACKAGE_LIST` — packages for the graphical desktop
   The official `samplefs_desktop` includes all of these; users edit the lists to add/remove.

4. Per-image system customization runs automatically during `pack_image.sh` via `hobot_customize_rootfs.sh` — creating users and enabling/disabling autostart entries. For changes here, point the user to that script and explain the image build step re-runs it.

5. Tooling background (brief): `debootstrap` builds a minimal Debian/Ubuntu system tree; `chroot` re-roots into it; `parted` handles image partitioning. Give exact commands only from the README.

## Safety

- Samplefs generation needs sudo and significant disk; confirm before running.
- Package list edits change what every subsequent image contains — show the diff and get confirmation.
- Never hand-edit files inside the generated rootfs to "fix" a build — change the source scripts instead, so images stay reproducible.

> Sources: `x5-rdk-gen` README v3.5.0「Ubuntu 文件系统制作」; `rdk-gen` README v3.0.3「制作 Ubuntu 文件系统」。
