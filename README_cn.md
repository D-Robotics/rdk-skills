<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# D-Robotics Agent Skills

[![License](https://img.shields.io/badge/license-Apache--2.0%20%2F%20CC--BY--4.0-green.svg)](#许可证)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Specification-blue)](https://agentskills.io)
[![Sync](https://github.com/D-Robotics/rdk-skills/actions/workflows/sync-skills.yml/badge.svg)](https://github.com/D-Robotics/rdk-skills/actions/workflows/sync-skills.yml)

> 中文 | [English](README.md)

面向 D-Robotics RDK 开发者套件的官方 Agent Skills 目录。每个 Skill 是一组可移植的指令文件，让 AI 编程助手（Claude Code、Codex、Cursor 等）能够诊断板卡、量化编译模型、跑通推理流水线、配置板端系统、部署到 RDK 板卡——所有能力都基于 D-Robotics 官方文档，而非模型记忆。

本仓库是**中央目录（Hub）**：各 Skill Pack 在独立的产品仓库中维护源头，本仓库负责镜像同步、统一索引和安装入口。用户只需跟这一个仓库打交道。

---

## 支持的板卡

| 板卡 | BPU 架构 | 算力 |
|------|----------|------|
| RDK X3 / X3 Module | Bernoulli | 5 TOPS |
| RDK X5 / X5 Module | Bayes-e | 10 TOPS |
| RDK Ultra | Bayes | 96 TOPS |
| RDK S100 / S100P | Nash-e | 80 / 128 TOPS |
| RDK S600 | Nash-p（4× Nash core） | 最高 560 TOPS |

板卡参数取自官方文档仓库 [rdk_x_doc](https://github.com/D-Robotics/rdk_x_doc) 和 [rdk_s_doc](https://github.com/D-Robotics/rdk_s_doc)。X 系列模型格式为 `.bin`，S 系列为 `.hbm`。

---

## 安装

### 方式一：让 AI 帮你装（推荐）

把下面这句 prompt 复制给你的 AI 编程助手（Claude Code、Codex、Cursor 等）：

```
Install D-Robotics RDK skills from the marketplace: run `npx skills add d-robotics/rdk-skills` and follow the interactive prompts to install the skills you need.
```

### 方式二：skills CLI

```bash
npx skills add d-robotics/rdk-skills
```

CLI 会列出所有可用 Skill，选择后自动安装到对应 Agent 的 skills 目录。

> CLI 覆盖扁平布局的 Skill（RDK Device Skills）。Workspace 集成型 Pack（OE 工具链）不支持逐个安装——请整包安装，见[方式五](#方式五workspace-集成型-packoe-工具链-x5--s)。

### 方式三：Claude Code 插件市场

```
/plugin marketplace add D-Robotics/rdk-skills
```

运行 `/plugin`，在 Discover 标签页浏览安装。

Hub 插件通过 `rdk-skill-finder` 搜索目录：扁平 Skill 会返回对应安装命令；workspace 集成型 Skill 会交给 `rdk-pack-installer` 处理。

### 方式四：直接克隆 Pack 仓库

每个 Pack 仓库自带 `install.sh`，支持 symlink 和 copy 两种模式，可同时安装到多个 Agent 运行时：

```bash
git clone https://github.com/D-Robotics/rdk-device-skills.git
cd rdk-device-skills
./install.sh                          # 默认 symlink 到 ~/.claude/skills 等
./install.sh --copy                   # 复制而非 symlink
./install.sh --targets claude,cursor  # 只装到指定 Agent
```

### 方式五：Workspace 集成型 Pack（OE 工具链 X5 / S）

部分 Pack 需要 workspace 初始化——安装脚本会将脚本、文档、平台配置铺设到 `.drobotics/`，并注入路由规则到 `CLAUDE.md`。整包安装，不支持逐个 skill 安装：

```bash
# X5 工具链
git clone https://github.com/D-Robotics/oe-skills-x5.git
cd oe-skills-x5
bash setup.sh $PROJECT_ROOT

# S 系列工具链（Horizon OE）
git clone https://github.com/D-Robotics/oe-skills-s.git
cd oe-skills-s
bash setup.sh $PROJECT_ROOT
```

或者告诉你的 AI（需先按方式三装好 Hub 插件，插件内含 `rdk-pack-installer`）：

```
Install D-Robotics OE-Skills-X5 into this project.
```

`rdk-pack-installer` 会读取随包注册表、克隆 Pack 仓库、在你确认项目根目录后执行 `setup.sh` 并校验安装结果，支持所有 `install_type: workspace` 的 Pack（OE 工具链 X5 和 S）。

### 更新 Skill

- 扁平 Skill：`npx skills update`（或重新 `npx skills add d-robotics/rdk-skills` 选择）
- Hub 插件：`/plugin` 中管理 `d-robotics-skills` 插件即可更新 finder/installer
- 目录本身每小时自动同步一次；克隆安装的 Pack 用 `git pull` + 重新执行 `setup.sh` 更新

---

## Skill 目录

列在 Pack 目录（`oe-skills-x5/`、`oe-skills-s/`）下的 Skill 属于 workspace 集成型 Pack——可在此浏览，安装需整包走[方式五](#方式五workspace-集成型-packoe-工具链-x5--s)；其余 Skill 用方式一~四单独安装。

<!-- skills-table-start -->
| 产品 | 说明 | Skills |
|------|------|--------|
| **BSP Skills** | 板级支持包（BSP）开发技能——主机交叉编译环境、repo/manifest 源码同步、系统镜像构建、内核/设备树/驱动模块、hobot-* deb 包、bootloader/miniboot、X3/X5 Ubuntu 根文件系统定制，以及 S 系列源码获取。 | [ `bsp-env-setup`](skills/bsp-env-setup), [ `bsp-source-sync`](skills/bsp-source-sync), [ `bsp-image-build`](skills/bsp-image-build), [ `bsp-kernel-build`](skills/bsp-kernel-build), [ `bsp-deb-build`](skills/bsp-deb-build), [ `bsp-bootloader-build`](skills/bsp-bootloader-build), [ `bsp-rootfs-custom`](skills/bsp-rootfs-custom), [ `bsp-s-series`](skills/bsp-s-series) |
| **RDK Device Skills** | 设备侧技能：诊断快照、内存审计、无头模式、摄像头、视觉流水线、模型部署与基准测试、GPIO、TROS、文档检索、硬件规格、板卡选型、Model Zoo、外设驱动、官方配件、端侧 LLM/VLM 部署、具身智能、S 系列异构开发、命令手册、源码导航 | [ `rdk-diagnostic`](skills/rdk-diagnostic), [ `rdk-memory-audit`](skills/rdk-memory-audit), [ `rdk-headless-mode`](skills/rdk-headless-mode), [ `rdk-camera-setup`](skills/rdk-camera-setup), [ `rdk-vision-pipeline`](skills/rdk-vision-pipeline), [ `rdk-model-deploy`](skills/rdk-model-deploy), [ `rdk-model-benchmark`](skills/rdk-model-benchmark), [ `rdk-docs-reference`](skills/rdk-docs-reference), [ `rdk-system-config`](skills/rdk-system-config), [ `rdk-network-remote`](skills/rdk-network-remote), [ `rdk-system-maintain`](skills/rdk-system-maintain), [ `rdk-log-forensics`](skills/rdk-log-forensics), [ `rdk-gpio-40pin`](skills/rdk-gpio-40pin), [ `rdk-tros-setup`](skills/rdk-tros-setup), [ `rdk-ecosystem`](skills/rdk-ecosystem), [ `rdk-hardware`](skills/rdk-hardware), [ `rdk-board-knowledge`](skills/rdk-board-knowledge), [ `rdk-model-zoo`](skills/rdk-model-zoo), [ `rdk-multimedia`](skills/rdk-multimedia), [ `rdk-peripheral-cookbook`](skills/rdk-peripheral-cookbook), [ `rdk-accessories`](skills/rdk-accessories), [ `rdk-llm-deployment`](skills/rdk-llm-deployment), [ `rdk-embodied-lerobot`](skills/rdk-embodied-lerobot), [ `rdk-board-delegate`](skills/rdk-board-delegate), [ `rdk-command-manual`](skills/rdk-command-manual), [ `rdk-source-map`](skills/rdk-source-map) |
| **OE 工具链 (X5)** | OpenExplorer X5 工具链——模型量化（PTQ/QAT）、编译、推理、性能评测、诊断。Workspace 集成型 Pack，需 setup.sh 初始化。 | [ `x5-accuracy-diagnostics`](skills/oe-skills-x5/x5-accuracy-diagnostics), [ `x5-board-monitor`](skills/oe-skills-x5/x5-board-monitor), [ `x5-bpu-python-api`](skills/oe-skills-x5/x5-bpu-python-api), [ `x5-calibration-data-prepare`](skills/oe-skills-x5/x5-calibration-data-prepare), [ `x5-consistency-diagnostics`](skills/oe-skills-x5/x5-consistency-diagnostics), [ `x5-environment-install`](skills/oe-skills-x5/x5-environment-install), [ `x5-environment-probe`](skills/oe-skills-x5/x5-environment-probe), [ `x5-environment-setup`](skills/oe-skills-x5/x5-environment-setup), [ `x5-model-diagnostics`](skills/oe-skills-x5/x5-model-diagnostics), [ `x5-model-preflight`](skills/oe-skills-x5/x5-model-preflight), [ `x5-performance-diagnostics`](skills/oe-skills-x5/x5-performance-diagnostics), [ `x5-ptq-compile`](skills/oe-skills-x5/x5-ptq-compile), [ `x5-ptq-config-authoring`](skills/oe-skills-x5/x5-ptq-config-authoring), [ `x5-ptq-deploy`](skills/oe-skills-x5/x5-ptq-deploy), [ `x5-qat-adaptation`](skills/oe-skills-x5/x5-qat-adaptation), [ `x5-qat-compile`](skills/oe-skills-x5/x5-qat-compile), [ `x5-qat-deploy`](skills/oe-skills-x5/x5-qat-deploy), [ `x5-qat-training`](skills/oe-skills-x5/x5-qat-training), [ `x5-router`](skills/oe-skills-x5/x5-router), [ `x5-runtime-cpp-infer`](skills/oe-skills-x5/x5-runtime-cpp-infer), [ `x5-runtime-deploy`](skills/oe-skills-x5/x5-runtime-deploy), [ `x5-runtime-perf-eval`](skills/oe-skills-x5/x5-runtime-perf-eval) |
| **OE 工具链 (S)** | Horizon OpenExplorer（OE）工具链，面向 S 系列——PTQ/QAT 量化、HBDK 编译、UCP 板端推理、性能与精度评估、LLM 压缩。Workspace 集成型 Pack，需 setup.sh 初始化。 | [ `hbdk-manual`](skills/oe-skills-s/hbdk/hbdk-manual), [ `j6-hbdk-compile`](skills/oe-skills-s/hbdk/j6-hbdk-compile), [ `j6-hmct-cosine-similarity-tuning`](skills/oe-skills-s/hmct/j6-hmct-cosine-similarity-tuning), [ `hmct`](skills/oe-skills-s/hmct), [ `hb-analyzer-performance`](skills/oe-skills-s/horizon_tc_ui/hb-analyzer-performance), [ `horizon-tc-ui`](skills/oe-skills-s/horizon_tc_ui/horizon-tc-ui), [ `board-detection`](skills/oe-skills-s/horizon-router/board-detection), [ `oe-llm-package-detection`](skills/oe-skills-s/horizon-router/oe-llm-package-detection), [ `oe-llm-package-install`](skills/oe-skills-s/horizon-router/oe-llm-package-install), [ `oe-package-detection`](skills/oe-skills-s/horizon-router/oe-package-detection), [ `oe-package-install`](skills/oe-skills-s/horizon-router/oe-package-install), [ `horizon-router`](skills/oe-skills-s/horizon-router), [ `j6-plugin-dynamic-block`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-dynamic-block), [ `j6-plugin-insert-quant-dequant`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-insert-quant-dequant), [ `j6-plugin-prepare`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-prepare), [ `j6-plugin-set-fake-quantize`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-set-fake-quantize), [ `j6-plugin-set-march`](skills/oe-skills-s/plugin/j6-plugin-adaptation/j6-plugin-set-march), [ `j6-plugin-adaptation`](skills/oe-skills-s/plugin/j6-plugin-adaptation), [ `j6-plugin-consistency-debug`](skills/oe-skills-s/plugin/j6-plugin-consistency-debug), [ `j6-plugin-export`](skills/oe-skills-s/plugin/j6-plugin-export), [ `j6-plugin-graph-diff`](skills/oe-skills-s/plugin/j6-plugin-graph-diff), [ `j6-hbdk-export-compile`](skills/oe-skills-s/plugin/j6-plugin-hbdk-generating/j6-hbdk-export-compile), [ `j6-plugin-quantization`](skills/oe-skills-s/plugin/j6-plugin-hbdk-generating/j6-plugin-quantization), [ `j6-plugin-hbdk-generating`](skills/oe-skills-s/plugin/j6-plugin-hbdk-generating), [ `j6-plugin-model-check-result`](skills/oe-skills-s/plugin/j6-plugin-model-check-result), [ `j6-plugin-precision-tuning`](skills/oe-skills-s/plugin/j6-plugin-precision-tuning), [ `j6-board-monitor`](skills/oe-skills-s/ucp/j6-board-monitor), [ `j6-ucp-hbm-infer`](skills/oe-skills-s/ucp/j6-ucp-hbm-infer), [ `j6-ucp-infer-generating`](skills/oe-skills-s/ucp/j6-ucp-infer-generating), [ `j6-ucp-model-perf-eval`](skills/oe-skills-s/ucp/j6-ucp-model-perf-eval), [ `j6-ucp-perfetto-trace-analysis`](skills/oe-skills-s/ucp/j6-ucp-perfetto-trace-analysis), [ `j6-ucp-perfetto-trace-catcher`](skills/oe-skills-s/ucp/j6-ucp-perfetto-trace-catcher), [ `ucp`](skills/oe-skills-s/ucp) |
<!-- skills-table-end -->

---

## 反馈与贡献

**问题分类与对应渠道：**

- **Skill 内容问题**（某个 Skill 有 bug 或缺失功能）——到该产品的源头仓库提 Issue，见下表
- **目录仓库问题**（README 错误、同步流水线故障、分发渠道）——[在这里提 Issue](../../issues/new/choose)
- **提问或讨论**——[GitHub Discussions](../../discussions)
- **安全漏洞**——按 [SECURITY.md](SECURITY.md) 的流程私下报告，**不要**开公开 Issue

**指南文档：**
- 使用方安装与用法 — [docs/SKILL-USAGE.md](docs/SKILL-USAGE.md)
- 注册新 Pack / PR 规范 — [docs/PR-SUBMISSION.md](docs/PR-SUBMISSION.md) 与 [CONTRIBUTING.md](CONTRIBUTING.md)

各产品源头仓库：

<!-- help-table-start -->
| 产品 | Issues | Discussions | 贡献指南 |
|------|--------|-------------|----------|
| **BSP Skills** | [Issues](https://github.com/D-Robotics/bsp-skills/issues) | — | [贡献指南](https://github.com/D-Robotics/bsp-skills/blob/main/CONTRIBUTING.md) |
| **RDK Device Skills** | [Issues](https://github.com/D-Robotics/rdk-device-skills/issues) | [Discussions](https://github.com/D-Robotics/rdk-device-skills/discussions) | [贡献指南](https://github.com/D-Robotics/rdk-device-skills/blob/main/CONTRIBUTING.md) |
| **OE 工具链 (X5)** | [Issues](https://github.com/D-Robotics/oe-skills-x5/issues) | — | [贡献指南](https://github.com/D-Robotics/oe-skills-x5/blob/main/CONTRIBUTING.md) |
| **OE 工具链 (S)** | [Issues](https://github.com/D-Robotics/oe-skills-s/issues) | — | — |
<!-- help-table-end -->

---

## Skill 结构

每个 Skill 是一个自包含的目录：

```
skills/<skill-name>/
├── SKILL.md          # 入口：YAML frontmatter + Agent 指令
├── skill-card.md     # 治理卡片：owner、license、用例、已知风险
├── scripts/          # 辅助脚本（bash），默认只读，写操作需 --apply
├── references/       # 参考材料，标注官方文档出处
└── evals/            # 评测任务定义（五维度：安全/正确/发现/效果/效率）
```

遵循 [Agent Skills 开放规范](https://agentskills.io/specification)：
- 每个 Skill 是一个目录，根目录有 `SKILL.md`
- YAML frontmatter 必填 `name` 和 `description`
- 渐进式加载：启动时只载入轻量元数据，激活时才载入完整指令

---

## 仓库结构

```
D-Robotics/rdk-skills/
├── skills/                      # 镜像目录（同步流水线写入，只读）
│   ├── README.md                 # 安装指引
│   ├── rdk-pack-installer/        # Hub 内置安装器 skill（catalog 例外）
│   ├── <skill-name>/             # 扁平布局 Skill（RDK Device Skills）
│   ├── oe-skills-x5/             # workspace Pack 镜像（批量布局，X5 工具链）
│   └── oe-skills-s/              # workspace Pack 镜像（批量布局，S 系列工具链）
├── components.d/                # Pack 注册表（每个产品一个 YAML）
│   ├── README.md                 # 注册规范
│   ├── rdk-device.yml
│   ├── oe-tool-chain.yml
│   └── oe-tool-chain-s.yml
├── plugins.d/                   # 插件构建配置
│   ├── README.md
│   ├── _defaults.yml
│   └── d-robotics-skills.yml
├── plugins/                     # 构建后的插件分发包
├── .claude-plugin/              # Claude Code marketplace
├── .agents/plugins/             # Codex marketplace
├── .cursor-plugin/              # Cursor marketplace
├── docs/                        # PR 提交规范 + Skill 使用文档
├── .github/
│   ├── workflows/                # 同步流水线、DCO 检查
│   └── scripts/                  # 同步、校验、README 重生成、orphan 清理
├── skills.sh.json               # Skills.sh 分组配置
├── catalog-exceptions.yml       # 允许未注册的 skills/ 目录
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── LICENSE-APACHE               # 源码许可
└── LICENSE-CC-BY-4.0            # 文档/Skill 许可
```

---

## 许可证

源码采用 [Apache-2.0](LICENSE-APACHE)，文档和 Skill 内容采用 [CC-BY-4.0](LICENSE-CC-BY-4.0)。
