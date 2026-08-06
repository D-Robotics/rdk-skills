<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# `plugins.d/` — 插件构建配置

每个 `<name>.yml` 定义一个插件。构建脚本 [`.github/scripts/build-plugins.sh`](../.github/scripts/build-plugins.sh) 解析这些文件，生成：

- `plugins/<name>/.claude-plugin/plugin.json`
- `plugins/<name>/.codex-plugin/plugin.json`
- `plugins/<name>/.cursor-plugin/plugin.json`
- `plugins/<name>/skills/<skill-basename>/` —— 指向 `skills/` 目录的 symlink 或 copy
- `.claude-plugin/marketplace.json`（顶层 Claude marketplace）
- `.agents/plugins/marketplace.json`（顶层 Codex marketplace）
- `.cursor-plugin/marketplace.json`（顶层 Cursor marketplace）

以 `_` 开头的文件视为 include，不会被构建为插件。`_defaults.yml` 提供共享默认值（author、license、capabilities），各插件 YAML 中的字段覆盖默认值（浅合并）。

## 单一数据源

`skills/` 目录是唯一数据源——每个 `SKILL.md` 在那里只存在一份。`plugins/` 下的目录树每次构建都从 YAML 文件重建，所以增删 Skill 只需改 `include_skills:` 列表然后重新构建：

```sh
.github/scripts/build-plugins.sh
```

## `skill_files:` — copy 还是 symlink

| 模式 | 磁盘上的内容 | 适用场景 |
|------|-------------|----------|
| `copy`（默认） | 真实文件（rsync） | 发布到 Codex / Anthropic；`codex plugin add` 要求真实文件 |
| `symlink` | 相对 symlink → `../../../skills/<skill>` | 只发 Claude 或 `npx skills add`；避免重复 |

默认值在 [`_defaults.yml`](./_defaults.yml) 中，可在 `plugins.d/<name>.yml` 中逐插件覆盖。

## 添加插件

1. 创建 `plugins.d/<name>.yml`，至少包含：

   ```yaml
   name: <name>           # 小写 kebab-case，必须和文件名一致
   description: ...        # 一行说明
   display_name: ...
   short_description: ...
   long_description: ...
   category: Coding
   include_skills:
     - skills/<skill>/
   ```

2. 运行 `.github/scripts/build-plugins.sh`
3. 提交重新生成的 `plugins/<name>/` 目录树和更新后的 `marketplace.json`

## 插件重命名

构建脚本不会自动检测重命名——它只看到新名字，构建新目录，旧目录留在原地。手动删除旧目录：

```sh
git mv plugins.d/old.yml plugins.d/new.yml
# 改文件里 name: old 为 name: new
git rm -r plugins/old
.github/scripts/build-plugins.sh
```

重建会重新生成两个 `marketplace.json`。`git add` 所有变更（重命名的 YAML、新的 `plugins/new/`、删除的 `plugins/old/`、两个 `marketplace.json`）一起提交。

注意：插件名是用户安装时输入的（`claude plugin install <name>`），如果旧名已发布过，重命名对用户是 breaking change。
