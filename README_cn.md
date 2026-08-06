<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# D-Robotics Agent Skills

[![License](https://img.shields.io/badge/license-Apache--2.0%20%2F%20CC--BY--4.0-green.svg)](#许可证)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Specification-blue)](https://agentskills.io)

> 中文 | [English](README.md)

面向 D-Robotics RDK 开发者套件的官方 Agent Skills 目录。每个 Skill 是一组可移植的指令文件，让 AI 编程助手（Claude Code、Codex、Cursor 等）能够诊断板卡、跑通推理流水线、调校 BSP、部署模型——所有能力都基于 D-Robotics 官方文档，而非模型记忆。

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

### 方式三：Claude Code 插件市场

```
/plugin marketplace add D-Robotics/rdk-skills
```

运行 `/plugin`，在 Discover 标签页浏览安装。

### 方式四：直接克隆 Pack 仓库

每个 Pack 仓库自带 `install.sh`，支持 symlink 和 copy 两种模式，可同时安装到多个 Agent 运行时：

```bash
git clone https://github.com/D-Robotics/rdk-device-skills.git
cd rdk-device-skills
./install.sh                          # 默认 symlink 到 ~/.claude/skills 等
./install.sh --copy                   # 复制而非 symlink
./install.sh --targets claude,cursor  # 只装到指定 Agent
```

---

## Skill 目录

<!-- skills-table-start -->
| 产品 | 说明 | Skills |
|------|------|--------|
| **RDK Device Skills** | 板端设备技能：诊断快照、内存审计、无头模式、摄像头调试、视觉流水线、模型部署与基准测试、GPIO、TogetheROS.Bot、文档检索 | [`rdk-diagnostic`](skills/rdk-diagnostic), [`rdk-memory-audit`](skills/rdk-memory-audit), [`rdk-headless-mode`](skills/rdk-headless-mode), [`rdk-camera-setup`](skills/rdk-camera-setup), [`rdk-vision-pipeline`](skills/rdk-vision-pipeline), [`rdk-model-deploy`](skills/rdk-model-deploy), [`rdk-model-benchmark`](skills/rdk-model-benchmark), [`rdk-docs-reference`](skills/rdk-docs-reference), [`rdk-system-config`](skills/rdk-system-config), [`rdk-network-remote`](skills/rdk-network-remote), [`rdk-system-maintain`](skills/rdk-system-maintain), [`rdk-log-forensics`](skills/rdk-log-forensics), [`rdk-gpio-40pin`](skills/rdk-gpio-40pin), [`rdk-tros-setup`](skills/rdk-tros-setup) |
| **OE 工具链** | OpenExplorer 工具链：模型量化（PTQ/QAT）、编译、推理、性能评测、诊断。支持 S 系列（S100/S100P/S600）和 X 系列（X5） | 60+ skills，覆盖 7 个模块（router / hbdk / plugin / hmct / ucp / drobotics_tc_ui / llm） |
<!-- skills-table-end -->

---

## 反馈与贡献

**问题分类与对应渠道：**

- **Skill 内容问题**（某个 Skill 有 bug 或缺失功能）——到该产品的源头仓库提 Issue，见下表
- **目录仓库问题**（README 错误、同步流水线故障、分发渠道）——[在这里提 Issue](../../issues/new/choose)
- **提问或讨论**——[GitHub Discussions](../../discussions)
- **安全漏洞**——按 [SECURITY.md](SECURITY.md) 的流程私下报告，**不要**开公开 Issue

各产品源头仓库：

<!-- help-table-start -->
| 产品 | Issues | Discussions | 贡献指南 |
|------|--------|-------------|----------|
| **RDK Device Skills** | [Issues](https://github.com/D-Robotics/rdk-device-skills/issues) | [Discussions](https://github.com/D-Robotics/rdk-device-skills/discussions) | [贡献指南](https://github.com/D-Robotics/rdk-device-skills/blob/main/CONTRIBUTING.md) |
| **OE 工具链** | [Issues](https://github.com/D-Robotics/oe-skills/issues) | [Discussions](https://github.com/D-Robotics/oe-skills/discussions) | [贡献指南](https://github.com/D-Robotics/oe-skills/blob/main/CONTRIBUTING.md) |
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
│   └── <skill-name>/            # 扁平结构，每个 Skill 一个顶层目录
├── components.d/                # Pack 注册表（每个产品一个 YAML）
│   ├── README.md                 # 注册规范
│   ├── rdk-device.yml
│   └── oe-tool-chain.yml
├── plugins.d/                   # 插件构建配置
│   ├── README.md
│   ├── _defaults.yml
│   └── d-robotics-skills.yml
├── plugins/                     # 构建后的插件分发包
├── .claude-plugin/              # Claude Code marketplace
├── .agents/plugins/             # Codex marketplace
├── .cursor-plugin/              # Cursor marketplace
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
