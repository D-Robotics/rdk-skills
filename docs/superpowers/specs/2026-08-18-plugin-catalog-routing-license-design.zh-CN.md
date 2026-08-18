# 插件目录、路由与许可证一致性修复设计

> [English](2026-08-18-plugin-catalog-routing-license-design.md) | 中文版

## 状态

本设计已于 2026-08-18 在对话中确认，覆盖 D-Robotics Skills Hub 第一阶段修复。

## 目标

让 Hub 插件做到自包含且描述准确：插件必须携带安装器所消费的 Pack 数据，提供真正的目录查找器，不再把用户路由到不存在的 D-Robotics Skill，并在不改变既有决策的前提下说明清楚仓库的双许可证规则。

## 范围

本阶段包含四项交付：

1. 为 `rdk-pack-installer` 生成并打包 workspace Pack 注册表。
2. 新增 Hub 原生 `rdk-skill-finder`，并为其生成可搜索的 Skill 索引。
3. 在 `rdk-device-skills` 中删除或替换已知失效的 D-Robotics Skill 路由，再刷新 `rdk-skills` 中的镜像。
4. 按 ADR 0004 统一许可证说明。

本阶段不新增 `rdk-ros` 等领域 Skill，不重构完整同步流水线，不强制解决全部历史 L1/L2 问题，也不迁移 OE 存量 Skill 的元数据。

## 已确定的设计决策

### 目录数据在构建时生成并随插件打包

不采用运行时从 GitHub 拉取数据的方案，因为除真正执行安装外，Skill 发现与安装准备不应依赖额外网络请求。也不把原始 `components.d/` 整体复制进插件，因为这会把 Hub 内部注册目录结构暴露成插件接口。

构建工具生成两个精简 JSON 文件：

- `skills/rdk-pack-installer/references/pack-registry.json`
- `skills/rdk-skill-finder/references/skill-index.json`

这样每个 Hub 原生 Skill 均可独立安装。生成文件纳入版本管理，确保 marketplace 用户得到的目录数据与仓库中经过评审的数据一致。

### 失效路由只映射到现有能力

本阶段不创建新的领域 Skill。失效路由只有两种处理方式：

- 指向当前目录中确实覆盖该请求的 Skill。
- 明确说明当前没有专用 Skill，并把事实检索交给 `rdk-docs-reference`。

### ADR 0004 保持权威

本阶段不对任何内容重新授权。已接受的规则是：

- 代码和脚本：Apache-2.0。
- 文档、`SKILL.md`、`skill-card.md` 和 references：CC-BY-4.0。
- 顶层 Skill frontmatter 按 ADR 0004 的明确要求继续填写 `license: Apache-2.0`。

文档将解释许可范围，并建议新建或实质修改的 Skill 增加 `metadata.content-license: CC-BY-4.0`。本阶段不把该字段设为强制门禁，以免给 OE 存量 Pack 增加新的违规项。

## 架构

### 目录生成器

在 `.github/scripts/` 下新增一个职责单一的 Python 模块，负责生成目录数据。其命令行接口接收仓库根目录，并写出两个确定性的 JSON 文件。

输入：

- `components.d/*.yml`
- 所有已注册 Skill 的 `SKILL.md`
- 用于识别 Hub 原生 Skill 的 `catalog-exceptions.yml`

Pack 注册表只包含 workspace 集成型 Pack，字段如下：

```json
{
  "schema_version": 1,
  "packs": [
    {
      "name": "OE Tool Chain (X5)",
      "repo": "D-Robotics/oe-skills-x5",
      "ref": "main",
      "install_type": "workspace",
      "install_script": "setup.sh",
      "workspace_dir": ".drobotics",
      "verify_paths": [
        ".drobotics/X5.md",
        ".drobotics/VERSION",
        ".drobotics/skill-index.json",
        ".drobotics/skills/x5-router/SKILL.md"
      ]
    }
  ]
}
```

Skill 索引为每个已发现的 Skill 生成一条记录：

```json
{
  "schema_version": 1,
  "skills": [
    {
      "name": "rdk-diagnostic",
      "description": "...",
      "pack": "RDK Device Skills",
      "catalog_path": "skills/rdk-diagnostic",
      "install_type": "flat",
      "repo": "D-Robotics/rdk-device-skills"
    }
  ]
}
```

生成结果必须确定：记录按稳定键排序，JSON 使用 UTF-8 并以换行结尾，连续生成两次不得产生 Git 差异。

### Pack 安装契约

Workspace 注册条目新增两个必填字段：

- `workspace_dir`：Pack 在项目中写入的相对目录。
- `verify_paths`：用于证明安装成功的非空项目相对路径列表。

本阶段约定：

- OE X5 使用 `.drobotics`，验证 X5 规则、版本、索引和 router 文件。
- OE S 使用 `.horizon`，验证 HORIZON 规则、版本、索引和 router 文件。

`components.d/README.md` 负责说明这些字段。若 workspace 安装字段缺失或路径不安全，生成器必须失败，不得输出不完整注册表。

### Pack 安装器

`rdk-pack-installer` 从自身 Skill 目录读取 `references/pack-registry.json`，运行时不再依赖 `components.d`。

安装流程继续保留确认门：

1. 用用户请求匹配注册表中的 Pack。
2. 确认准确的项目根目录。
3. 展示声明的 workspace 目录及待验证文件。
4. 将声明的仓库 clone 到临时目录。
5. 若存在 `agent-setup.md` 则先读取；在用户最终确认后执行声明的安装脚本。
6. 验证全部声明路径。
7. 清理临时 clone 并汇报结果。

遇到未知 Pack 或畸形注册数据时必须停止。安装器不得猜测仓库名称或验证路径。

### Skill 查找器

新增只读 Hub 原生 Skill `rdk-skill-finder`，包含：

- `SKILL.md`
- `skill-card.md`
- `evals/tasks.yaml`
- `scripts/search_catalog.py`
- 自动生成的 `references/skill-index.json`

搜索脚本接收一个或多个查询词，并支持按 Pack、板卡/平台关键词和安装类型过滤。排序规则保持确定性：精确名称匹配优先，其次为触发词/description 的词项重合度，最后按 Skill 名称排序。

Finder 行为：

- 对扁平 Skill，返回 Skill 名称、简短说明以及 `npx skills add d-robotics/rdk-skills --skill <name>`。
- 对 workspace Skill，返回所属 Pack，并把安装交给 `rdk-pack-installer`。
- 如果没有结果达到确定性的最低重合阈值，明确返回无匹配，并建议使用 `rdk-docs-reference`；不得编造 Skill 名称。

插件包含 finder、installer 和文档检索 Skill。Marketplace 与 README 应描述为“发现并安装目标 Skill”，不能再描述成透明加载整个目录。

## 路由修复

路由编辑在源头仓库 `rdk-device-skills` 中完成，并在同一轮实现中刷新 Hub 镜像，确保本地验证覆盖源头和镜像。

已知映射如下：

| 失效路由 | 替代方式 |
|---|---|
| `rdk-doc-finder` | `rdk-docs-reference` |
| `rdk-mipi-camera-bringup` | `rdk-camera-setup` |
| 用于板端推理的 `rdk-device` | `rdk-model-deploy` |
| 用于自有模型转换的 `rdk-device` | X5 使用 `x5-router`，S 系列使用 `horizon-router`；缺失时说明需要安装 workspace Pack |
| 用于 TROS 安装/环境的 `rdk-ros` | `rdk-tros-setup` |
| 用于 ROS 节点/应用开发的 `rdk-ros` | 明确当前没有专用 Skill，使用 `rdk-docs-reference` 检索官方 TROS 文档 |
| `rdk-perf-investigator` | 删除不存在的 Skill 名称，保留一般性的诊断编排说明 |

任何替换都不得暗示一个较窄的 Skill 覆盖其文档范围之外的工作。

## 许可证一致性修复

以下文档必须同步更新：

- `README.md`
- `README_cn.md`
- `CONTRIBUTING.md`
- `docs/PR-SUBMISSION.md`
- 与镜像许可规则有关的 `components.d/README.md`

这些文档需要共同说明：仓库按文件类型使用双许可证，而顶层 frontmatter 必填值依据 ADR 0004 保持 `Apache-2.0`。新建或实质修改的 Skill 建议增加：

```yaml
metadata:
  content-license: CC-BY-4.0
```

本阶段该字段只用于解释，不作为强制门禁，因此不会给 OE 存量 Pack 增加新的失败项。

## 错误处理

- 已注册 Skill 的 frontmatter 缺失或无效时，目录生成失败并输出相对 catalog 路径。
- Skill 名称重复时生成失败，因为 finder 无法安全消歧。
- catalog 路径重复时生成失败。
- workspace 验证字段缺失时 Pack 注册表生成失败。
- `include_skills` 路径不存在时插件构建失败，不能静默遗漏。
- Finder 解析失败或无匹配时返回结构化错误，不得臆造后备结果。
- 路由校验必须报告源文件和失效路由名称。

## 测试

实现遵循 TDD。测试使用临时仓库 fixture，并通过公开命令行为进行验证。

必备测试：

1. 目录生成器输出包含 X5 和 S workspace 记录，并带正确 workspace 目录和验证路径。
2. 目录生成器同时输出 flat 与 workspace Skill 索引记录，且结果逐字节确定。
3. 生成器拒绝重复 Skill 名称、不安全验证路径和缺失 workspace 字段。
4. Finder 将精确名称匹配排在首位，并能按 flat/workspace 过滤。
5. Finder 为 flat Skill 返回安装命令，为 workspace Skill 返回安装器交接信息。
6. 插件构建在 include Skill 缺失时失败，并正确打包三个 Hub 原生 Skill。
7. Pack 安装器说明只引用随包注册表，不再要求运行时访问 `components.d`。
8. 路由完整性测试确认 `rdk-device-skills/skills/*/SKILL.md` 中不存在五个废弃路由名称。
9. 文档测试确认 ADR 0004 的代码/内容许可划分与 frontmatter 规则表述一致。
10. 现有 Hub 与源头 Pack 校验继续运行，本阶段不得新增 L1/L2 违规。

## 仓库变更范围

### `rdk-skills`

- 新增生成器及测试。
- 新增 `rdk-skill-finder` 及其测试/evals。
- 新增自动生成的注册表和索引。
- 扩展 workspace 组件注册信息。
- 更新安装器说明和插件组成。
- 重建已提交的插件产物与 marketplace 文件。
- 源头路由修改后刷新 RDK Device Skills 镜像。
- 统一文档中的许可证说明与插件能力描述。

### `rdk-device-skills`

- 替换已知失效路由。
- 在现有校验/测试入口中增加路由完整性回归测试。
- 如果 eval 期望中出现旧路由名称，同步更新。

## 验收条件

- 独立安装的 Hub 插件在无法访问 Hub `components.d` 时仍能发现 Skill 和识别 workspace Pack。
- Pack 安装器从随包注册表解析 X5 与 S 的安装及验证信息。
- 插件包含 `rdk-skill-finder`、`rdk-pack-installer` 和 `rdk-docs-reference`。
- RDK Device Skill 源头和 Hub 镜像中均不再存在已知失效的 D-Robotics 路由名称。
- 许可证文档与 ADR 0004 一致，且不改变既有内容的授权方式。
- 所有新测试均完成红—绿验证；在声明完成前，完整验证套件必须通过。
