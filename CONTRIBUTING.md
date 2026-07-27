# 贡献指南

## 新增 Skill Pack

1. 在 `D-Robotics` 组织下创建仓库，命名 `<domain>-skills`
2. 在 Pack 仓库内创建 Skill（见[组织指南](../D-Robotics_Skills_组织指南.md)）
3. 在本仓库 `components.d/` 下添加一个 YAML 文件：

```yaml
name: my-pack
title: My Pack
source: D-Robotics/my-pack-skills
sourcePath: drobotics/skills/
platforms:
  - s-series
skillCount: 0
```

4. 同步流水线会自动拉取并合并到中央索引

## 新增 Skill（到已有 Pack）

1. 在对应 Pack 仓库的 `skills/` 目录下创建 Skill 文件夹 + `SKILL.md`
2. 确保 frontmatter 包含 `name`、`description`、`version`
3. 在 Pack 仓库的 `skill-index.json` 中注册
4. 提交 PR 到 Pack 仓库
5. 合并后同步流水线自动镜像到中央仓库

## SKILL.md 格式要求

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 小写 + 连字符 |
| `description` | ✅ | 说清做什么 + 何时触发，至少 20 字符 |
| `version` | ✅ | 语义化版本号 |

详见[组织指南](../D-Robotics_Skills_组织指南.md)。
