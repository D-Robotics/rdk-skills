<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# PR 提交规范

本仓库（`D-Robotics/rdk-skills`）是中央目录。**Skill 内容不在这里改**——内容 PR 提到各产品的源头仓库。本仓库的 PR 只处理三类事：

| PR 类型 | 内容 |
|---|---|
| 注册新 Pack / 新增 skill | 修改 `components.d/<slug>.yml` |
| 目录本身的修复 | README、结构、同步脚本、插件配置 |
| 配置与治理 | catalog-exceptions、CHANGELOG、流程文档 |

---

## 一、提交前检查

1. **DCO 签名**（强制）。所有 commit 必须 sign-off，否则被 DCO 检查拦截：

   ```bash
   git commit -s -m "Register bsp-skills pack"
   ```

2. **确认 skill 满足 L1 准入**（见下）。同步流水线镜像后，Hub 校验会检查。

3. **`components.d/` 一个文件一个 Pack**。新 Pack 新建文件，不要改别人的文件。

---

## 二、L1 准入门槛（同步门禁会查）

每个进入 `skills/` 的 skill 必须满足：

- `SKILL.md` 存在，带 YAML frontmatter
- frontmatter 四必填字段：`name` / `description` / `version` / `license`
- `name` 小写 + 连字符，≤64 字符，且与目录名一致
- `description` ≤1024 字符
- `SKILL.md` 正文 ≤500 行

L2 治理要求（`skill-card.md` + `evals/` + 四章节）对新增 skill 强制、对存量 skill 有过渡期。完整分级规则见仓库根 `CONTRIBUTING.md` 与《组织规范》。

## 许可证规则

ADR 0004 是本仓库许可证规则的权威依据。仓库按文件类型双许可。
许可证映射：代码和脚本 = Apache-2.0；SKILL.md、skill-card.md、references 和其他文档内容 = CC-BY-4.0。
代码和脚本采用
Apache-2.0；`SKILL.md`、`skill-card.md`、`references` 和其他文档内容采用
CC-BY-4.0。为兼容当前 Skill 生态，顶层 Skill frontmatter 仍填写
`license: Apache-2.0`；新建或实质修改的 Skill 建议同时声明
`metadata.content-license: CC-BY-4.0`。这是对未来贡献规则的澄清，不对既有
内容追溯性重新授权。

---

## 三、注册一个新 Pack

在 `components.d/` 下新建 `<slug>.yml`：

```yaml
# components.d/bsp-skills.yml
name: BSP Skills
repo: D-Robotics/bsp-skills
description: 一句话说明这组 Skill 做什么。
skills:
  - path: skills/board-flash/
    catalog_dir: board-flash
  - path: skills/driver-config/
    catalog_dir: driver-config
```

字段说明：

| 字段 | 说明 |
|---|---|
| `name` | README 中显示的产品名 |
| `repo` | GitHub 仓库（`owner/repo`） |
| `description` | README 技能表中的一行说明 |
| `skills[].path` | 源头仓库中含 `SKILL.md` 的目录路径 |
| `skills[].catalog_dir` | 本仓库 `skills/` 下的顶层目录名（全局唯一） |

选填：`ref`（同步分支，默认 main）、`links.contributing`、`links.discussions`。

提交 PR 后，同步流水线在合并到 main 时自动拉取。

---

## 四、同步流水线做了什么

PR 合并后，`sync-skills.yml` 会：

1. 读 `components.d/*.yml` 汇总全部 Pack
2. clone 各源头仓库，按 `path` → `catalog_dir` rsync skill 目录
3. 清理未注册的孤儿目录（`prune-orphans.sh`）
4. 重生成 README 技能表（`regenerate-readme.sh`）
5. 重建插件清单（`build-plugins.sh`）
6. 提交并推送

**观察期内**门禁只报告不拦截；收紧后 L1 不过的 skill 会被拒收。

---

## 五、PR 描述模板

```
## 变更类型
[ ] 注册新 Pack    [ ] 新增/移除 skill    [ ] 目录修复    [ ] 配置/治理

## 说明
（改了什么、为什么）

## 影响范围
（涉及哪些 Pack / skill）

## 检查
- [ ] commit 已 DCO 签名（git commit -s）
- [ ] 涉及 skill 满足 L1 准入门槛
- [ ] catalog_dir 全局唯一，无撞名
```
