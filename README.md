<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# D-Robotics Agent Skills

[![License](https://img.shields.io/badge/license-Apache--2.0%20%2F%20CC--BY--4.0-green.svg)](#license)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Specification-blue)](https://agentskills.io)

> English | [中文](README_cn.md)

Official Agent Skills catalog for D-Robotics RDK developer kits. Each skill is a portable instruction set that teaches AI coding agents (Claude Code, Codex, Cursor, etc.) how to diagnose boards, run inference pipelines, customize BSP, and deploy models — grounded in official D-Robotics documentation, not model memory.

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

### Option 3: Claude Code plugin marketplace

```
/plugin marketplace add D-Robotics/rdk-skills
```

Run `/plugin`, browse the Discover tab, and install.

### Option 4: Clone a Pack repo directly

Each Pack repo ships an `install.sh` supporting both symlink and copy modes across multiple agent runtimes:

```bash
git clone https://github.com/D-Robotics/rdk-device-skills.git
cd rdk-device-skills
./install.sh                          # default: symlink into ~/.claude/skills etc.
./install.sh --copy                   # copy instead of symlink
./install.sh --targets claude,cursor  # specific agents only
```

### Option 5: Workspace-integrated packs (OE Tool Chain)

Some packs require workspace initialization — they install scripts, docs, and platform configs into `.drobotics/` and inject routing rules into `CLAUDE.md`. Install the whole pack, not individual skills:

```bash
git clone https://github.com/D-Robotics/oe-skills-x5.git
cd oe-skills-x5
bash setup.sh $PROJECT_ROOT
```

Or tell your AI:

```
Install D-Robotics OE-Skills-X5: clone https://github.com/D-Robotics/oe-skills-x5 and run bash setup.sh with my project root.
```

---

## Skill Catalog

<!-- skills-table-start -->
| Product | Description | Skills |
|---------|-------------|--------|
| **OE Tool Chain (X5)** | OpenExplorer X5 tool chain — model quantization (PTQ/QAT), compilation, inference, performance evaluation, and diagnostics. Workspace-integrated pack requiring setup.sh initialization. | [ `x5-router`](skills/x5-router), [ `x5-environment-setup`](skills/x5-environment-setup), [ `x5-environment-probe`](skills/x5-environment-probe), [ `x5-environment-install`](skills/x5-environment-install), [ `x5-ptq-deploy`](skills/x5-ptq-deploy), [ `x5-model-preflight`](skills/x5-model-preflight), [ `x5-calibration-data-prepare`](skills/x5-calibration-data-prepare), [ `x5-ptq-config-authoring`](skills/x5-ptq-config-authoring), [ `x5-ptq-compile`](skills/x5-ptq-compile), [ `x5-qat-deploy`](skills/x5-qat-deploy), [ `x5-qat-adaptation`](skills/x5-qat-adaptation), [ `x5-qat-training`](skills/x5-qat-training), [ `x5-qat-compile`](skills/x5-qat-compile), [ `x5-runtime-deploy`](skills/x5-runtime-deploy), [ `x5-runtime-cpp-infer`](skills/x5-runtime-cpp-infer), [ `x5-runtime-perf-eval`](skills/x5-runtime-perf-eval), [ `x5-board-monitor`](skills/x5-board-monitor), [ `x5-bpu-python-api`](skills/x5-bpu-python-api), [ `x5-model-diagnostics`](skills/x5-model-diagnostics), [ `x5-accuracy-diagnostics`](skills/x5-accuracy-diagnostics), [ `x5-consistency-diagnostics`](skills/x5-consistency-diagnostics), [ `x5-performance-diagnostics`](skills/x5-performance-diagnostics) |
| **RDK Device Skills** | Device-side skills for RDK boards — diagnostics, memory audit, headless mode, camera, vision pipeline, model deploy & benchmarking, GPIO, TROS, doc search, hardware specs, board selection, model zoo, peripherals, accessories, LLM/VLM deployment, embodied AI, S-series delegate, command manual, source map. | [ `rdk-diagnostic`](skills/rdk-diagnostic), [ `rdk-memory-audit`](skills/rdk-memory-audit), [ `rdk-headless-mode`](skills/rdk-headless-mode), [ `rdk-camera-setup`](skills/rdk-camera-setup), [ `rdk-vision-pipeline`](skills/rdk-vision-pipeline), [ `rdk-model-deploy`](skills/rdk-model-deploy), [ `rdk-model-benchmark`](skills/rdk-model-benchmark), [ `rdk-docs-reference`](skills/rdk-docs-reference), [ `rdk-system-config`](skills/rdk-system-config), [ `rdk-network-remote`](skills/rdk-network-remote), [ `rdk-system-maintain`](skills/rdk-system-maintain), [ `rdk-log-forensics`](skills/rdk-log-forensics), [ `rdk-gpio-40pin`](skills/rdk-gpio-40pin), [ `rdk-tros-setup`](skills/rdk-tros-setup), [ `rdk-ecosystem`](skills/rdk-ecosystem), [ `rdk-hardware`](skills/rdk-hardware), [ `rdk-board-knowledge`](skills/rdk-board-knowledge), [ `rdk-model-zoo`](skills/rdk-model-zoo), [ `rdk-multimedia`](skills/rdk-multimedia), [ `rdk-peripheral-cookbook`](skills/rdk-peripheral-cookbook), [ `rdk-accessories`](skills/rdk-accessories), [ `rdk-llm-deployment`](skills/rdk-llm-deployment), [ `rdk-embodied-lerobot`](skills/rdk-embodied-lerobot), [ `rdk-board-delegate`](skills/rdk-board-delegate), [ `rdk-command-manual`](skills/rdk-command-manual), [ `rdk-source-map`](skills/rdk-source-map) |
<!-- skills-table-end -->

---

## Feedback and Contributing

**Issue routing:**

- **Skill content issues** (a skill has a bug or missing feature) — file in the source repo for that product, see table below
- **Catalog repo issues** (README errors, sync pipeline failures, distribution channels) — [open an issue here](../../issues/new/choose)
- **Questions or discussion** — [GitHub Discussions](../../discussions)
- **Security vulnerabilities** — follow the disclosure process in [SECURITY.md](SECURITY.md); do not open a public issue

Product source repos:

<!-- help-table-start -->
| Product | Issues | Discussions | Contributing |
|---------|--------|-------------|--------------|
| **OE Tool Chain (X5)** | [Issues](https://github.com/D-Robotics/oe-skills-x5/issues) | [Discussions](https://github.com/D-Robotics/oe-skills-x5/discussions) | [Contributing](https://github.com/D-Robotics/oe-skills-x5/blob/main/CONTRIBUTING.md) |
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
│   └── <skill-name>/            # flat layout, one top-level dir per skill
├── components.d/                # Pack registry (one YAML per product)
│   ├── README.md                 # registration schema
│   ├── rdk-device.yml
│   └── oe-tool-chain.yml
├── plugins.d/                   # plugin build configuration
│   ├── README.md
│   ├── _defaults.yml
│   └── d-robotics-skills.yml
├── plugins/                     # built plugin distributions
├── .claude-plugin/              # Claude Code marketplace
├── .agents/plugins/             # Codex marketplace
├── .cursor-plugin/              # Cursor marketplace
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

Source code is licensed under [Apache-2.0](LICENSE-APACHE). Documentation and skill content is licensed under [CC-BY-4.0](LICENSE-CC-BY-4.0).
