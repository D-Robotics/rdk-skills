<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# Skill 使用文档

本文档面向**使用方**：想把 D-Robotics Agent Skills 装进自己工作流的开发者与 Agent 运维者。贡献与注册请看 [PR 提交规范](./PR-SUBMISSION.md)。

---

## 一、安装

### 方式 1：skills CLI（推荐）

```bash
npx skills add d-robotics/rdk-skills
```

CLI 会列出全部可用 skill，交互式选择后安装到对应 Agent 的技能目录。

### 方式 2：Claude Code 插件市场

```
/plugin marketplace add D-Robotics/rdk-skills
```

然后 `/plugin` → Discover 标签页浏览安装。

### 方式 3：直接克隆 Pack 仓库

各 Pack 仓库自带 `install.sh`（如适用），支持 symlink/copy 两种模式：

```bash
git clone https://github.com/D-Robotics/rdk-device-skills.git
cd rdk-device-skills
./install.sh                          # 默认 symlink 到 ~/.claude/skills 等
./install.sh --copy                   # 复制而非软链
./install.sh --targets claude,cursor  # 只装指定 Agent
```

安装完成后**重启 Agent 会话**使新技能生效。

---

## 二、支持的 Agent 运行时

| Agent | 技能目录 |
|---|---|
| Claude Code | `~/.claude/skills` 或项目 `.claude/skills/` |
| OpenAI Codex | `~/.codex/skills` |
| 通用（agents CLI） | `~/.agents/skills` |
| Cursor | `~/.cursor/skills` |
| Qoder | `~/.qoder/skills` |

---

## 三、Skill 是怎么被发现的

Agent **不会**一次性加载所有 skill 内容，而是分三层渐进披露：

1. **启动时**：只有每个 skill 的 `name` + `description` 进入上下文（约 100 tokens/个）
2. **触发时**：Agent 判断相关后，才读取该 skill 的 `SKILL.md` 正文（<5k tokens）
3. **按需**：正文引用的 `references/`、`scripts/` 由 Agent 在执行时读取或调用

所以——**用户只需正常提问**，不需要指定用哪个 skill。Agent 根据 description 自动匹配。例如：

| 你说 | Agent 会加载 |
|---|---|
| "这块板什么型号、多少内存" | `rdk-diagnostic` |
| "帮我把 YOLO 部署到 X5" | `rdk-model-deploy` |
| "X5 能跑多大的 LLM" | `rdk-ecosystem` |
| "摄像头不出图" | `rdk-camera-setup` |

---

## 四、当前目录内容（v1.1.0 首发）

首批 25 个设备侧 skill：

| 分组 | Skill |
|---|---|
| 诊断与观测 | rdk-diagnostic、rdk-memory-audit、rdk-log-forensics、rdk-network-remote |
| 系统配置 | rdk-system-config、rdk-headless-mode、rdk-system-maintain |
| 摄像头与视觉 | rdk-camera-setup、rdk-vision-pipeline |
| 模型部署与评测 | rdk-model-deploy、rdk-model-benchmark |
| 外设与 ROS | rdk-gpio-40pin、rdk-tros-setup |
| 文档与知识 | rdk-docs-reference、rdk-board-knowledge、rdk-hardware、rdk-command-manual、rdk-source-map |
| 选型与生态 | rdk-ecosystem、rdk-accessories |
| 高级部署 | rdk-llm-deployment、rdk-embodied-lerobot、rdk-board-delegate、rdk-model-zoo、rdk-multimedia、rdk-peripheral-cookbook |

支持的板卡：RDK X3 / X5 / Ultra / S100 / S100P / S600（X 系列模型格式 `.bin`，S 系列 `.hbm`）。

---

## 五、设计保证

- **官方文档是唯一事实来源**：skill 中的命令、路径、参数均出自 D-Robotics 官方文档，references/ 中标注出处
- **不编造**：脚本探测不到的信号报告 `null`/`false` 并说明原因；无法回答的问题回答"未覆盖"
- **观测/行动分离**：诊断类 skill 严格只读；写操作需显式参数（如 `--apply`）与用户确认
- **平台隔离**：X 系列与 S 系列知识严格隔离，不跨平台外推

---

## 六、反馈

- Skill 内容问题 → 到对应源头仓库提 Issue
- 目录/安装问题 → 本仓库提 Issue
- 安全漏洞 → 按 SECURITY.md 私下报告
