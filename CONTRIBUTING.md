<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# 贡献指南

本仓库是 D-Robotics Agent Skills 的中央目录。各产品的 Skill 在各自的产品仓库中维护。

## 你要贡献什么？

| 贡献类型 | 去哪里 |
|----------|--------|
| 修改某个 Skill 的内容 | 到该产品的源头仓库提 PR（见 [README 技能表](README.md#skill-目录)） |
| 修改目录仓库本身（README、结构、新 Pack 注册） | 在本仓库提 [PR](../../pulls) |
| 目录仓库的 bug 或功能建议 | 在本仓库提 [Issue](../../issues/new/choose) |
| 提问或讨论 | [GitHub Discussions](../../discussions) |
| 安全漏洞 | 按 [SECURITY.md](SECURITY.md) 流程私下报告 |

## 注册新 Pack

1. 在 `D-Robotics` 组织下创建仓库
2. 在 Pack 仓库中按标准 Skill 结构创建 Skill（见下）
3. 在本仓库 `components.d/` 下创建 YAML 文件（规范见 [`components.d/README.md`](components.d/README.md)）
4. 提交 PR——同步流水线自动拉取

## 发布维护

正式版本、Git tag 与 GitHub Release 的维护流程见 [docs/RELEASING.md](docs/RELEASING.md)。发布说明使用英文模板 [`.github/RELEASE_TEMPLATE.md`](.github/RELEASE_TEMPLATE.md)；已公开的 tag 不得重写，修复必须发布新的补丁版本。

## Skill 目录规范

源头仓库的 Skill 放在 `skills/` 目录下，每个 Skill 一个子目录。不要用 `.claude/skills/`、`.codex/skills/` 这类 Agent 专属路径——那些是安装时的目标路径，不是源头的存放路径。安装工具会从 `skills/` 复制或 symlink 到各 Agent 的发现路径。

## 标准 Skill 结构

```
skills/<skill-name>/
├── SKILL.md          # 入口：YAML frontmatter + Agent 指令
├── skill-card.md     # 治理卡片：owner、license、用例、已知风险
├── scripts/          # 辅助脚本（bash），默认只读，写操作需 --apply
├── references/       # 参考材料，标注官方文档出处
└── evals/            # 评测任务定义
```

## SKILL.md frontmatter 要求

| 字段 | 必填 | 规则 |
|------|------|------|
| `name` | 是 | 小写加连字符，≤64 字符，必须和目录名一致 |
| `description` | 是 | ≤1024 字符；包含触发词和负向触发词（"Do not use for..."） |
| `version` | 是 | 语义版本号（如 `0.1.0`） |
| `license` | 是 | `Apache-2.0` |
| `metadata.author` | 推荐 | 团队或个人名 |
| `metadata.tags` | 推荐 | 可搜索的标签 |
| `metadata.languages` | 可选 | 脚本语言（如 `[bash]`、`[bash, python]`） |
| `metadata.data-classification` | 推荐 | 数据分类，默认 `public` |

## 许可证规则

ADR 0004 是本仓库许可证规则的权威依据。仓库按文件类型双许可。
许可证映射：代码和脚本 = Apache-2.0；SKILL.md、skill-card.md、references 和其他文档内容 = CC-BY-4.0。
代码和脚本采用
Apache-2.0；`SKILL.md`、`skill-card.md`、`references` 和其他文档内容采用
CC-BY-4.0。为兼容当前 Skill 生态，顶层 Skill frontmatter 仍填写
`license: Apache-2.0`；新建或实质修改的 Skill 建议同时声明
`metadata.content-license: CC-BY-4.0`。这是对未来贡献规则的澄清，不对既有
内容追溯性重新授权。

## SKILL.md 必填 section

SKILL.md body 必须包含以下 4 个 section：

| Section | 用途 |
|---------|------|
| `## Purpose` | 这个 Skill 做什么，解决什么问题 |
| `## When to use` | 触发条件（正面触发 + 负面触发，"不要"段落） |
| `## Instructions` | Agent 执行步骤、脚本调用方式 |
| `## Safety` | 安全边界：只读 vs 写操作、需确认的操作 |

## evals/tasks.yaml 格式

每个 Skill 的 `evals/` 目录下必须有评测任务文件（`tasks.yaml`），格式如下：

```yaml
- id: <pack-prefix>-<NNN>     # 如 diag-001
  dimension: <维度>            # correctness / discoverability / security / effectiveness / efficiency
  prompt: "用户问题"
  expect:
    skill: <skill-name>       # 期望路由到的 skill（或 none 表示不应激活）
    behavior:                 # 期望行为列表
      - runs scripts/xxx.sh
      - quotes field X from output
      - does not fabricate data
```

五维评测说明：

| 维度 | 检查什么 |
|------|----------|
| Security | 不泄漏密钥、不执行破坏性命令、不越权访问 |
| Correctness | 遵循预期工作流，产出正确结果 |
| Discoverability | 相关时加载 skill，无关时不加载 |
| Effectiveness | 用 skill 后显著优于不用 |
| Efficiency | 消耗更少 token，避免冗余操作 |

## 设计原则

1. **官方文档是唯一真相源。** Skill 引用和引用它，不编造设备事实。
2. **观察/行动分离。** 诊断类 skill 严格只读，交接给行动类 skill；写操作需 `--apply` 和用户确认。
3. **不编造数据。** 不可用的信号报告为 `null`/`false` 并说明原因；回答不了的问题说"未覆盖"，不猜。
4. **Skill 自包含。** 每个 skill 目录可独立安装；共享的平台检测器在缺失时优雅降级。
5. **description 是路由信号。** frontmatter 的 description 携带完整触发面和负向触发词，因为只有 description 始终在 Agent 上下文中。

## Pack 级推荐基础设施

每个 Pack 仓库**推荐**（不强制）配备以下设施：

| 文件 | 用途 |
|------|------|
| `Makefile` | 统一入口：`make test` / `make validate` / `make lint` |
| `install.sh` | 安装脚本：symlink/copy 到多个 Agent 运行时 |
| `tools/sandbox.py` | 本地校验沙箱：frontmatter + section + 脚本 + 路由测试 |

参考实现见 [rdk-device-skills](https://github.com/D-Robotics/rdk-device-skills) 仓库。

## DCO 签名

所有提交必须 sign-off，证明你有权提交：

```bash
git commit -s -m "Add rdk-diagnostic skill"
```

会在 commit message 末尾追加：

```
Signed-off-by: Your Name <your@email.com>
```

未签名的提交不会被接受。
