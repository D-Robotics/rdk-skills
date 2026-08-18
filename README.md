<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# D-Robotics Agent Skills

[![License](https://img.shields.io/badge/license-Apache--2.0%20%2F%20CC--BY--4.0-green.svg)](#license)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Specification-blue)](https://agentskills.io)
[![Sync](https://github.com/D-Robotics/rdk-skills/actions/workflows/sync-skills.yml/badge.svg)](https://github.com/D-Robotics/rdk-skills/actions/workflows/sync-skills.yml)

> English | [中文](README_cn.md)

Official Agent Skills catalog for D-Robotics RDK developer kits. Each skill is a portable instruction set that teaches AI coding agents (Claude Code, Codex, Cursor, etc.) how to diagnose boards, quantize and compile models, run inference pipelines, configure on-device systems, and deploy to RDK boards — grounded in official D-Robotics documentation, not model memory.

This repository is the **central catalog (Hub)**: each Skill Pack maintains its source in an independent product repo, and this repo mirrors, indexes, and serves as the single install entry point.

---

## Supported Boards

| Board | BPU Architecture | Compute |
|-------|------------------|---------|
| RDK X3 / X3 Module | Bernoulli | 5 TOPS |
| RDK X5 / X5 Module | Bayes-e | 10 TOPS |
| RDK Ultra | Bayes | 96 TOPS |
| RDK S100 / S100P | Nash-e | 80 / 128 TOPS |
| RDK S600 | Nash-p (4x Nash core) | up to 560 TOPS |

Board parameters follow official documentation repositories [rdk_x_doc](https://github.com/D-Robotics/rdk_x_doc) and [rdk_s_doc](https://github.com/D-Robotics/rdk_s_doc). Model format is `.bin` on X series and `.hbm` on S series.

---

## Installation

### Option 1: Ask your AI to install (recommended)

Copy this prompt to your AI coding agent (Claude Code, Codex, Cursor, etc.):

```
Install D-Robotics RDK skills from the marketplace: run `npx skills add d-robotics/rdk-skills` and follow the interactive prompts to install the skills you need.
```

### Option 2: skills CLI

```bash
npx skills add d-robotics/rdk-skills
```

The CLI lists all available skills and installs the selected one into the appropriate agent skill directory.

> The CLI covers flat-layout skills (RDK Device Skills). Workspace-integrated packs (OE Tool Chain) are not individually installable — install those whole via [Option 5](#option-5-workspace-integrated-packs-oe-tool-chain-x5--s).

### Option 3: Claude Code plugin marketplace

```
/plugin marketplace add D-Robotics/rdk-skills
```

Run `/plugin`, browse the Discover tab, and install.

The Hub plugin uses `rdk-skill-finder` to search the catalog. For a flat skill it returns the appropriate installation command; for a workspace-integrated skill it hands the request to `rdk-pack-installer`.

### Option 4: Clone a Pack repo directly

Each Pack repo ships an `install.sh` supporting both symlink and copy modes across multiple agent runtimes:

```bash
git clone https://github.com/D-Robotics/rdk-device-skills.git
cd rdk-device-skills
./install.sh                          # default: symlink into ~/.claude/skills etc.
./install.sh --copy                   # copy instead of symlink
./install.sh --targets claude,cursor  # specific agents only
```

### Option 5: DeepSeek Harness (DSH) plugin

Install the whole RDK skill ecosystem into DeepSeek Harness as a native plugin bundle (npm package `dsh-plugin-rdk`, GitHub topic [`dsh-plugin`](https://github.com/topics/dsh-plugin)):

```bash
dsh plugin --profile <name> add dsh-plugin-rdk   # or: add github:<owner>/dsh-plugin-rdk
dsh --profile <name>
```

The bundle registers every skill in this catalog into the harness skill registry (so they load through the built-in `skill` tool), and adds two model tools: `rdk_skills` (browse/search the catalog) and `rdk_board_detect` (detect whether the host is an RDK board). See `.dsh-plugin/marketplace.json` and the plugin repo for details.

### Option 6: Workspace-integrated packs (OE Tool Chain X5 / S)

Some packs require workspace initialization — they install scripts, docs, and platform configs into `.drobotics/` and inject routing rules into `CLAUDE.md`. Install the whole pack, not individual skills:

```bash
# X5 tool chain
git clone https://github.com/D-Robotics/oe-skills-x5.git
cd oe-skills-x5
bash setup.sh $PROJECT_ROOT

# S-series tool chain (Horizon OE)
git clone https://github.com/D-Robotics/oe-skills-s.git
cd oe-skills-s
bash setup.sh $PROJECT_ROOT
```

Or tell your AI (works with the Hub plugin from Option 3, which ships `rdk-pack-installer`):

```
Install D-Robotics OE-Skills-X5 into this project.
```

`rdk-pack-installer` reads its bundled pack registry, clones the pack repo, runs `setup.sh` with your confirmed project root, and verifies the installed workspace. It supports every pack registered with `install_type: workspace` (OE Tool Chain X5 and S).

### Updating skills

- Flat skills: `npx skills update` (or re-run `npx skills add d-robotics/rdk-skills` and select again).
- Hub plugin: `/plugin` → manage the `d-robotics-skills` plugin to update the finder and installer skills.
- DSH bundle: `dsh plugin --profile <name> update dsh-plugin-rdk` (skill content refreshes with each bundle release).
- The catalog itself refreshes automatically every hour (sync pipeline) — cloned pack repos update with `git pull` + re-run `setup.sh`.

---

## Skill Catalog

Skills listed under a pack directory (`oe-skills-x5/`, `oe-skills-s/`) belong to workspace-integrated packs — browse them here, install the whole pack via [Option 5](#option-5-workspace-integrated-packs-oe-tool-chain-x5--s). All other skills install individually via Options 1–4.

<!-- skills-table-start -->
| Product | Description | Skills |
|---------|-------------|--------|
| **BSP Skills** | Board Support Package (BSP) development skills for RDK boards — host cross-compilation environment, repo/manifest source sync, system image build, kernel/DTB/driver modules, hobot-* deb packages, bootloader/miniboot, Ubuntu rootfs customization for X3/X5, and S-series source acquisition. | [ `bsp-env-setup`](skills/bsp-env-setup), [ `bsp-source-sync`](skills/bsp-source-sync), [ `bsp-image-build`](skills/bsp-image-build), [ `bsp-kernel-build`](skills/bsp-kernel-build), [ `bsp-deb-build`](skills/bsp-deb-build), [ `bsp-bootloader-build`](skills/bsp-bootloader-build), [ `bsp-rootfs-custom`](skills/bsp-rootfs-custom), [ `bsp-s-series`](skills/bsp-s-series) |
| **OE Tool Chain (S)** | Horizon OpenExplorer (OE) tool chain for S-series — PTQ/QAT quantization, HBDK compilation, UCP on-board inference, performance and accuracy evaluation, and LLM compression. Workspace-integrated pack requiring setup.sh initialization. | [ `hbdk-manual`](skills/oe-skills-s/hbdk/hbdk-manual), [ `j6-hbdk-compile`](skills/oe-skills-s/hbdk/j6-hbdk-compile), [ `hmct`](skills/oe-skills-s/hmct), [ `j6-hmct-cosine-similarity-tuning`](skills/oe-skills-s/hmct/j6-hmct-cosine-similarity-tuning), [ `horizon-router`](skills/oe-skills-s/horizon-router), [ `board-detection`](skills/oe-skills-s/horizon-router/board-detection), [ `oe-llm-package-detection`](skills/oe-skills-s/horizon-router/oe-llm-package-detection), [ `oe-llm-package-install`](skills/oe-skills-s/horizon-router/oe-llm-package-install), [ `oe-package-detection`](skills/oe-skills-s/horizon-router/oe-package-detection), [ `oe-package-install`](skills/oe-skills-s/horizon-router/oe-package-install), [ `hb-analyzer-performance`](skills/oe-skills-s/horizon_tc_ui/hb-analyzer-performance), [ `horizon-tc-ui`](skills/oe-skills-s/horizon_tc_ui/horizon-tc-ui), [ `j6-plugin-adaptation`](skills/oe-skills-s/plugin/j6-plugin-adaptation), [ `j6-plugin-dynamic-block`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-dynamic-block), [ `j6-plugin-insert-quant-dequant`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-insert-quant-dequant), [ `j6-plugin-prepare`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-prepare), [ `j6-plugin-set-fake-quantize`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-set-fake-quantize), [ `j6-plugin-set-march`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-set-march), [ `j6-plugin-consistency-debug`](skills/oe-skills-s/plugin/j6-plugin-consistency-debug), [ `j6-plugin-export`](skills/oe-skills-s/plugin/j6-plugin-export), [ `j6-plugin-graph-diff`](skills/oe-skills-s/plugin/j6-plugin-graph-diff), [ `j6-plugin-hbdk-generating`](skills/oe-skills-s/plugin/j6-plugin-hbdk-generating), [ `j6-hbdk-export-compile`](skills/oe-skills-s/plugin/j6-plugin-hbdk-generating/j6-hbdk-export-compile), [ `j6-plugin-quantization`](skills/oe-skills-s/plugin/j6-plugin-hbdk-generating/j6-plugin-quantization), [ `j6-plugin-model-check-result`](skills/oe-skills-s/plugin/j6-plugin-model-check-result), [ `j6-plugin-precision-tuning`](skills/oe-skills-s/plugin/j6-plugin-precision-tuning), [ `ucp`](skills/oe-skills-s/ucp), [ `j6-board-monitor`](skills/oe-skills-s/ucp/j6-board-monitor), [ `j6-ucp-hbm-infer`](skills/oe-skills-s/ucp/j6-ucp-hbm-infer), [ `j6-ucp-infer-generating`](skills/oe-skills-s/ucp/j6-ucp-infer-generating), [ `j6-ucp-model-perf-eval`](skills/oe-skills-s/ucp/j6-ucp-model-perf-eval), [ `j6-ucp-perfetto-trace-analysis`](skills/oe-skills-s/ucp/j6-ucp-perfetto-trace-analysis), [ `j6-ucp-perfetto-trace-catcher`](skills/oe-skills-s/ucp/j6-ucp-perfetto-trace-catcher) |
| **OE Tool Chain (X5)** | OpenExplorer X5 tool chain — model quantization (PTQ/QAT), compilation, inference, performance evaluation, and diagnostics. Workspace-integrated pack requiring setup.sh initialization. | [ `x5-accuracy-diagnostics`](skills/oe-skills-x5/x5-accuracy-diagnostics), [ `x5-board-monitor`](skills/oe-skills-x5/x5-board-monitor), [ `x5-bpu-python-api`](skills/oe-skills-x5/x5-bpu-python-api), [ `x5-calibration-data-prepare`](skills/oe-skills-x5/x5-calibration-data-prepare), [ `x5-consistency-diagnostics`](skills/oe-skills-x5/x5-consistency-diagnostics), [ `x5-environment-install`](skills/oe-skills-x5/x5-environment-install), [ `x5-environment-probe`](skills/oe-skills-x5/x5-environment-probe), [ `x5-environment-setup`](skills/oe-skills-x5/x5-environment-setup), [ `x5-model-diagnostics`](skills/oe-skills-x5/x5-model-diagnostics), [ `x5-model-preflight`](skills/oe-skills-x5/x5-model-preflight), [ `x5-performance-diagnostics`](skills/oe-skills-x5/x5-performance-diagnostics), [ `x5-ptq-compile`](skills/oe-skills-x5/x5-ptq-compile), [ `x5-ptq-config-authoring`](skills/oe-skills-x5/x5-ptq-config-authoring), [ `x5-ptq-deploy`](skills/oe-skills-x5/x5-ptq-deploy), [ `x5-qat-adaptation`](skills/oe-skills-x5/x5-qat-adaptation), [ `x5-qat-compile`](skills/oe-skills-x5/x5-qat-compile), [ `x5-qat-deploy`](skills/oe-skills-x5/x5-qat-deploy), [ `x5-qat-training`](skills/oe-skills-x5/x5-qat-training), [ `x5-router`](skills/oe-skills-x5/x5-router), [ `x5-runtime-cpp-infer`](skills/oe-skills-x5/x5-runtime-cpp-infer), [ `x5-runtime-deploy`](skills/oe-skills-x5/x5-runtime-deploy), [ `x5-runtime-perf-eval`](skills/oe-skills-x5/x5-runtime-perf-eval) |
| **RDK Device Skills** | Device-side skills for RDK boards — diagnostics, memory audit, headless mode, camera, vision pipeline, model deploy & benchmarking, GPIO, TROS, doc search, hardware specs, board selection, model zoo, peripherals, accessories, LLM/VLM deployment, embodied AI, S-series delegate, command manual, source map. | [ `rdk-diagnostic`](skills/rdk-diagnostic), [ `rdk-memory-audit`](skills/rdk-memory-audit), [ `rdk-headless-mode`](skills/rdk-headless-mode), [ `rdk-camera-setup`](skills/rdk-camera-setup), [ `rdk-vision-pipeline`](skills/rdk-vision-pipeline), [ `rdk-model-deploy`](skills/rdk-model-deploy), [ `rdk-model-benchmark`](skills/rdk-model-benchmark), [ `rdk-docs-reference`](skills/rdk-docs-reference), [ `rdk-system-config`](skills/rdk-system-config), [ `rdk-network-remote`](skills/rdk-network-remote), [ `rdk-system-maintain`](skills/rdk-system-maintain), [ `rdk-log-forensics`](skills/rdk-log-forensics), [ `rdk-gpio-40pin`](skills/rdk-gpio-40pin), [ `rdk-tros-setup`](skills/rdk-tros-setup), [ `rdk-ecosystem`](skills/rdk-ecosystem), [ `rdk-hardware`](skills/rdk-hardware), [ `rdk-board-knowledge`](skills/rdk-board-knowledge), [ `rdk-model-zoo`](skills/rdk-model-zoo), [ `rdk-multimedia`](skills/rdk-multimedia), [ `rdk-peripheral-cookbook`](skills/rdk-peripheral-cookbook), [ `rdk-accessories`](skills/rdk-accessories), [ `rdk-llm-deployment`](skills/rdk-llm-deployment), [ `rdk-embodied-lerobot`](skills/rdk-embodied-lerobot), [ `rdk-board-delegate`](skills/rdk-board-delegate), [ `rdk-command-manual`](skills/rdk-command-manual), [ `rdk-source-map`](skills/rdk-source-map) |
<!-- skills-table-end -->

---

## Feedback and Contributing

**Issue routing:**

- **Skill content issues** (a skill has a bug or missing feature) — file in the source repo for that product, see table below
- **Catalog repo issues** (README errors, sync pipeline failures, distribution channels) — [open an issue here](../../issues/new/choose)
- **Questions or discussion** — [GitHub Discussions](../../discussions)
- **Security vulnerabilities** — follow the disclosure process in [SECURITY.md](SECURITY.md); do not open a public issue

**Guides:**
- End-user install & usage — [docs/SKILL-USAGE.md](docs/SKILL-USAGE.md)
- Registering a new pack / PR rules — [docs/PR-SUBMISSION.md](docs/PR-SUBMISSION.md) and [CONTRIBUTING.md](CONTRIBUTING.md)

Product source repos:

<!-- help-table-start -->
| Product | Issues | Discussions | Contributing |
|---------|--------|-------------|--------------|
| **BSP Skills** | [Issues](https://github.com/D-Robotics/bsp-skills/issues) | — | [Contributing](https://github.com/D-Robotics/bsp-skills/blob/main/CONTRIBUTING.md) |
| **OE Tool Chain (S)** | [Issues](https://github.com/D-Robotics/oe-skills-s/issues) | — | — |
| **OE Tool Chain (X5)** | [Issues](https://github.com/D-Robotics/oe-skills-x5/issues) | — | [Contributing](https://github.com/D-Robotics/oe-skills-x5/blob/main/CONTRIBUTING.md) |
| **RDK Device Skills** | [Issues](https://github.com/D-Robotics/rdk-device-skills/issues) | [Discussions](https://github.com/D-Robotics/rdk-device-skills/discussions) | [Contributing](https://github.com/D-Robotics/rdk-device-skills/blob/main/CONTRIBUTING.md) |
<!-- help-table-end -->

---

## Skill Structure

Each skill is a self-contained directory:

```
skills/<skill-name>/
├── SKILL.md          # entry point: YAML frontmatter + agent instructions
├── skill-card.md     # governance card: owner, license, use case, known risks
├── scripts/          # helper scripts (bash), read-only by default, --apply for writes
├── references/       # reference material with documentation provenance
└── evals/            # evaluation task definitions (5 dimensions: security/correctness/discoverability/effectiveness/efficiency)
```

Follows the [Agent Skills specification](https://agentskills.io/specification):
- Each skill is a directory with a `SKILL.md` at its root
- YAML frontmatter with required `name` and `description` fields
- Progressive disclosure: lightweight metadata loads at startup, full instructions load on activation

---

## Repository Structure

```
D-Robotics/rdk-skills/
├── skills/                      # mirror directory (written by sync pipeline, read-only)
│   ├── README.md                 # install guidance
│   ├── rdk-pack-installer/        # hub-native installer skill (catalog exception)
│   ├── <skill-name>/             # flat-layout skills (RDK Device Skills)
│   ├── oe-skills-x5/             # workspace pack mirror (bulk layout, X5 tool chain)
│   └── oe-skills-s/              # workspace pack mirror (bulk layout, S-series tool chain)
├── components.d/                # Pack registry (one YAML per product)
│   ├── README.md                 # registration schema
│   ├── rdk-device.yml
│   ├── oe-tool-chain.yml
│   └── oe-tool-chain-s.yml
├── plugins.d/                   # plugin build configuration
│   ├── README.md
│   ├── _defaults.yml
│   └── d-robotics-skills.yml
├── plugins/                     # built plugin distributions
├── .claude-plugin/              # Claude Code marketplace
├── .agents/plugins/             # Codex marketplace
├── .cursor-plugin/              # Cursor marketplace
├── .dsh-plugin/                 # DeepSeek Harness (DSH) bundle marketplace
├── docs/                        # PR submission rules + skill usage guide
├── .github/
│   ├── workflows/                # sync pipeline, DCO check
│   └── scripts/                  # sync, validate, regenerate-readme, prune-orphans
├── skills.sh.json               # Skills.sh grouping config
├── catalog-exceptions.yml       # skills/ dirs allowed without registration
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── LICENSE-APACHE               # source code license
└── LICENSE-CC-BY-4.0            # documentation/skills license
```

---

## License

Per ADR 0004, this repository uses a dual license by file type: code and scripts
are licensed under [Apache-2.0](LICENSE-APACHE), while `SKILL.md`,
`skill-card.md`, `references`, and other documentation content are licensed under
[CC-BY-4.0](LICENSE-CC-BY-4.0). For compatibility with the current Skill
ecosystem, top-level Skill frontmatter continues to use `license: Apache-2.0`.
New or substantively modified Skills are recommended to declare
`metadata.content-license: CC-BY-4.0` as well. This is a clarification of future
contribution rules; it does not retroactively relicense existing content.
