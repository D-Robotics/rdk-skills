---
name: bsp-s-series
description: Entry point for S-series (S100/S100P/S600) BSP work — where to get the BSP source (developer.d-robotics.cc/resource download center), where the official environment/build guides live (rdk_s_doc §7.2.1 environment, §7.6 rdk_gen build system with ubuntu-2404_*_rdk-s600 conf), and how it differs from the X-series build flow. Use when the user wants S-series BSP source, S100/S600 system build, or asks whether X-series bsp skills apply to S boards. 触发词:S100 BSP、S600 BSP、S 系列源码、S 系列系统构建、nash、rdk_s_doc、下载中心. Do not apply X3/X5 build commands to S boards.
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics BSP Team
  tags: [bsp, s-series, s100, s600, horizon]
  data-classification: public
---

# S-series BSP (S100 / S600)

## Purpose

Own the S-series BSP entry points and keep them strictly separated from the X-series (X3/X5) build system. S-series BSP source is distributed through the official download center (not a public GitHub manifest like X-series), and its build is documented in `rdk_s_doc`.

## When to use

Use when:
- The user asks where to get S100/S600 BSP source
- Setting up an S-series system build environment
- Someone tries to apply X-series commands (`repo init x5-manifest`, `pack_image.sh` from x5-rdk-gen) to S boards

Do not use:
- X3/X5 host-side builds — the other bsp-* skills
- Board-side flashing/diagnostics — `rdk-board-knowledge` (RDK Device Skills pack)

## Instructions

1. **Series boundary gate.** Ask for the exact S board/chip (S100, S100P, or S600) and the intended artifact. Reject X3/X5 manifests, image configs, toolchains, and commands as non-interchangeable; route X3/X5 work to the appropriate X-series BSP Skill instead of adapting an X5 command.

2. **Source acquisition.** S-series BSP source is obtained from the official download center: `https://developer.d-robotics.cc/resource`（资源汇总页：`rdk_s_doc §1.6 资源汇总`）. Guide the user to log in, pick the S100/S600 BSP source package matching their target version, and download it. Report the exact package name/location once the user provides it — do not invent one. Keep this acquisition path separate from generic `bsp-source-sync` instructions.

3. **Environment setup.** Follow the official guide `rdk_s_doc §7.2.1 开发环境搭建及编译说明` (Advanced development → linux_development → environment_build) for the S-series host environment. Do not copy the X-series package list into S-series instructions.

4. **System build.** The S-series build system is documented in `rdk_s_doc §7.6 构建系统开发指南` (rdk_gen) — it is an rdk-gen-style flow with S-specific configs such as `ubuntu-2404_desktop_rdk-s600_*.conf`. Follow that chapter for the actual commands; it is the single source of truth.

5. **Platform differences to state** (verified facts):
   - Model format on S-series is `.hbm` (X-series uses `.bin`)
   - S100/S100P are Nash-e, S600 is Nash-p (4× Nash core)
   - Flashing uses xburn (DFU/Fastboot) — device-side, see `rdk-board-knowledge`

6. **Gap handling.** Until the downloaded source package is at hand, do not fabricate build commands. Present the official doc chapters above and offer to walk through them step by step with the user.

## Safety

- Download-center resources may require a D-Robotics developer account: never collect credentials; let the user log in themselves.
- S and X toolchains/artifacts are incompatible — block cross-series command reuse explicitly.
- Mark any not-yet-verified command as "per official docs, verify after source package arrives".

> Sources: `rdk_s_doc §1.6 资源汇总`, `§7.2.1 开发环境搭建及编译说明`, `§7.6 构建系统开发指南`（developer.d-robotics.cc / d-robotics.github.io 官方文档站）; user-provided entry point `developer.d-robotics.cc/resource`.
