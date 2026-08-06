<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# `components.d/` — Pack 注册表

每个 YAML 文件注册一个 Skill Pack（产品线）。一个文件对应一个产品线，互不干扰——不同团队的 onboarding PR 永远不会碰同一个文件。

## 注册一个新 Pack

1. 创建 `components.d/<slug>.yml`，`<slug>` 用产品名的小写加连字符（如 `RDK Device` → `rdk-device.yml`）
2. 填写字段（见下）
3. 提交 PR——同步流水线自动拉取，README 表格在下一次同步后更新

## 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | README 中显示的产品名（如 `RDK Device Skills`） |
| `repo` | string | GitHub 仓库（`owner/repo`） |
| `description` | string | README 技能表中的一行说明 |
| `skills` | list | Skill 源头位置列表，每个 entry 指向一个含 `SKILL.md` 的目录 |

`skills:` 下每个 entry 的字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `path` | string | 源头仓库中包含 `SKILL.md` 的目录路径 |
| `catalog_dir` | string | 本目录 `skills/` 下的顶层目录名（全局唯一） |

## 选填字段

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `ref` | `main` | 同步分支 |
| `links.contributing` | `CONTRIBUTING.md` | 源头仓库的贡献指南路径，设为 `false` 表示无 |
| `links.discussions` | `true` | 设为 `false` 表示仓库无 Discussions |

## 示例

```yaml
# components.d/your-product.yml
name: Your Product
repo: D-Robotics/your-product-skills
description: 一句话说明这组 Skill 做什么。
skills:
  - path: skills/your-product-install/
    catalog_dir: your-product-install
  - path: skills/your-product-deploy/
    catalog_dir: your-product-deploy
```

每个 entry 在本目录的 `skills/` 下创建一个顶层目录。目录名与源头 1:1 对应——便于浏览和发现，而不是按产品嵌套。

## 批量布局（不推荐新 Pack 使用）

> 批量布局是指一个 entry 的 `path` 指向一个**包含多个 Skill 的父目录**，所有 Skill 落到同一个 `catalog_dir` 下。新 Pack 请用上面的扁平布局。

已有的批量布局继续工作，同步流水线对两种布局的处理方式相同（目录到目录的 `rsync`）。区别只在于产出的目录形状。

不推荐的写法：

```yaml
# 不推荐 — 新 Pack 不要这样写
skills:
  - path: skills/
    catalog_dir: your-product
```

这会产出 `skills/your-product/<skill-name>/` 这样的嵌套路径。扁平布局更好，因为：

- 每个 Skill 有独立的顶层目录，和其他 Pack 的 Skill 并列可扫
- `catalog_dir` 在注册时就明确了目录名，不依赖源头 `skills/` 下碰巧有什么子目录
- 源头增删改 Skill 不影响目录顶层形状

## 同步流程

同步流水线执行：

```bash
yq ea '[.] | {"components": .}' components.d/*.yml > /tmp/components.aggregated.yml
```

然后遍历 `components` 列表。文件按字母序读取，README 重生成时按产品名排序。

## Orphan 清理

从 YAML 删除一个 skill entry，下次同步时对应的 `skills/<catalog_dir>/` 会被删除——同步流水线的 orphan 清理步骤（`.github/scripts/prune-orphans.sh`）会删掉所有没有 `components.d` 注册的顶层 `skills/` 目录。

如果有需要故意保留但不想注册的目录（如面向贡献者的内部 Skill），在仓库根目录的 `catalog-exceptions.yml` 中列出，附上原因和 owner。

清理的安全机制：
- 任何 component 文件解析失败 → 跳过整个清理
- 一次删除超过 5 个目录 → 拒绝执行，标记人工处理
