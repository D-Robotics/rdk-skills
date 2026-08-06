<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# Skills 目录

本目录包含从各产品仓库同步而来的 D-Robotics Agent Skills。每个子目录是一个自包含的 Skill，根目录有 `SKILL.md`。

## 安装某个 Skill

### 用 skills CLI（推荐）

```bash
npx skills add d-robotics/rdk-skills
```

CLI 会列出所有可用 Skill，选择后自动安装。

### 手动安装

如果已经克隆了本仓库，复制或 symlink 某个 Skill 目录到 Agent 的 skills 发现路径：

```bash
# Claude Code
cp -r skills/rdk-diagnostic ~/.claude/skills/

# Codex
cp -r skills/rdk-diagnostic ~/.codex/skills/

# Cursor
cp -r skills/rdk-diagnostic ~/.cursor/skills/
```

或者直接克隆源头 Pack 仓库，用它的 `install.sh` 一次装到多个 Agent（支持 symlink）。

## Skill 结构

```
skills/<skill-name>/
├── SKILL.md          # 入口：YAML frontmatter + Agent 指令
├── skill-card.md     # 治理卡片：owner、license、用例、已知风险
├── scripts/          # 辅助脚本（bash），默认只读
├── references/       # 参考材料，标注官方文档出处
└── evals/            # 评测任务定义
```

完整目录和贡献指南见[主 README](../README.md)。
