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
| `skills` | list | Skill 源头位置列表，每个 entry 指向一个含 `SKILL.md` 的目录（workspace Pack 指向整个资源树根目录） |

`skills:` 下每个 entry 的字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `path` | string | 源头仓库中需要镜像的目录路径（扁平布局：含 `SKILL.md` 的目录；workspace 布局：资源树根目录，如 `x5/`、`horizon/`） |
| `catalog_dir` | string | 本目录 `skills/` 下的顶层目录名（全局唯一） |

## 选填字段

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `ref` | `main` | 同步分支或发布 tag；**workspace 集成型 Pack 必须显式 pin 到不可变 tag**（如 `v2.1.0`），发新版时打新 tag 并移动 ref |
| `links.contributing` | `CONTRIBUTING.md` | 源头仓库的贡献指南路径，设为 `false` 表示无 |
| `links.discussions` | `true` | 设为 `false` 表示仓库无 Discussions |

## Workspace Pack 安装契约

`install_type: workspace` 的 Pack 必须额外声明以下字段，目录生成器会将它们写入 Pack 注册表；字段缺失会导致生成失败。

| 字段 | 类型 | 说明 |
|------|------|------|
| `install_script` | string | 安装脚本名（位于源头仓库根目录，如 `setup.sh`） |
| `install_type` | string | 固定为 `workspace` |
| `workspace_dir` | string | 安装脚本在用户项目中写入的相对目录 |
| `verify_paths` | non-empty list[string] | 用于确认安装成功的项目相对文件或目录路径 |

### workspace 镜像形态：完整资源树 + setup.sh（可自安装）

workspace Pack 的 `skills` 必须有且只有一个 entry，其 `path` 指向源头仓库的资源树根目录（如 `x5/`、`horizon/`），`catalog_dir` 即该 Pack 在本目录的顶层目录名。同步流水线会将：

1. **完整资源树**（`docs/`、`platforms/`、`scripts/`、`skill-index.json`、`VERSION` 以及 `skills/` 子树）rsync 到 `skills/<catalog_dir>/`；
2. Pack 根目录的 `install_script`（`setup.sh`）**覆盖层**到同一目录（rsync 看不到仓库根级文件，故用稀疏检出的附加文件单独覆盖）。

此外 workspace Pack 必须把 `ref` 显式 pin 到不可变 tag：Pack 仓库打 tag → 本条目 `ref` 移至新 tag → 合并触发同步在该 tag 处快照。tag 只增不改、不 force-move，回滚即把 `ref` 改回旧 tag。

因此只需 clone 一次 Hub 目录，`bash skills/<catalog_dir>/setup.sh <project-root>` 即可完整安装该 Pack；Pack 自有的 `setup.sh` 需要同时兼容两种资源位置（仓库根布局 `./x5/` 与 Hub 平铺布局），Hub 镜像检测不到 `<资源根>/*` 子目录时自行平铺。Pack 仓库仍保留为权威上游与降级安装源。

**升级契约（P1）**：`setup.sh` 支持 `--update`（先比已装 `VERSION` 与资源 `VERSION`，相同则直接跳过，不同则删除重建 workspace 目录，不残留旧文件）、`--force`（忽略版本比较强制重建）与 `--ref <tag>`（把安装来源 tag 记录进 `<workspace_dir>/INSTALLED_REF`，省略时回退为 VERSION 值）。三个能力是注册表 `ref` 锚点的下游：installer 把项目侧 `INSTALLED_REF`（缺失时回退 `VERSION`）与注册表 `ref` 归一化比对（去掉前导 `v`，`v2.1.0` 与 `2.1.0` 等价），相同报告已是最新，不同才执行 `setup.sh --update --ref <ref>`。发布新版时 Pack 必须同步 bump 资源 `VERSION` 并打新 tag（VERSION 与 tag 一一对应，二者同时移动，Hub `ref` 跟进）——否则 `--update` 无法感知新内容。

`skills` entry 的 `catalog_dir`、`install_script`、`workspace_dir` 与每条 `verify_paths` 必须是非空 POSIX 相对路径：不能是绝对路径、不能包含 `..`，也不能使用反斜杠 `\\`。例如 X5 Pack 使用 `.drobotics`，并验证 `.drobotics/skills/x5-router/SKILL.md`。

## 许可证规则

ADR 0004 是本仓库许可证规则的权威依据。仓库按文件类型双许可。
许可证映射：代码和脚本 = Apache-2.0；SKILL.md、skill-card.md、references 和其他文档内容 = CC-BY-4.0。
代码和脚本采用
Apache-2.0；`SKILL.md`、`skill-card.md`、`references` 和其他文档内容采用
CC-BY-4.0。为兼容当前 Skill 生态，顶层 Skill frontmatter 仍填写
`license: Apache-2.0`；新建或实质修改的 Skill 建议同时声明
`metadata.content-license: CC-BY-4.0`。这是对未来贡献规则的澄清，不对既有
内容追溯性重新授权。

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

**例外——workspace 集成型 Pack 必须用批量布局**：`install_type: workspace` 的 Pack 的 `path` 指向整个资源树根目录（不止 `skills/`），配合 `setup.sh` 覆盖层形成可自安装镜像（见上文「Workspace Pack 安装契约」）。

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
