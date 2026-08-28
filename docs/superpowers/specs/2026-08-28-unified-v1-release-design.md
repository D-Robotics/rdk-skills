# 统一 v1.0.0 发布设计

## 目标

把 BSP、设备、X5、S 与 Hub 五个仓库的**当前发布版本**强制统一为
`1.0.0`，完成 BSP Skill 的最终可用性优化，并以五个不可变 `v1.0.0`
annotated tag 发布。

## 范围

| 仓库 | 发布内容 | 发布 tag |
| --- | --- | --- |
| `bsp-skills` | 8 个 BSP Skill 的版本、说明、路由边界、风险确认与 evals | `v1.0.0` |
| `rdk-device-skills` | 合并既有路由修复并把全部当前 Skill frontmatter 统一到 `1.0.0` | `v1.0.0` |
| `oe-skills-x5` | 所有当前 Skill frontmatter、`x5/VERSION`、setup 文案与资源版本统一到 `1.0.0` | `v1.0.0` |
| `oe-skills-s` | 所有当前 Skill frontmatter、`horizon/VERSION`、setup 文案与资源版本统一到 `1.0.0` | `v1.0.0` |
| `rdk-skills` | Hub Skill frontmatter、组件注册、镜像、目录、插件、文档、测试与 CHANGELOG | `v1.0.0` |

“统一”指每个当前对外版本字段、Pack `VERSION`、Hub 组件 `ref`、安装器
升级锚点和发布文档都指向 `1.0.0` / `v1.0.0`。旧 tag（例如 `v2.1.0`
与 `v0.3.0`）保留为历史快照，不删除、不移动、不 force-push。

## 非目标

- 不修复与本次发布无关的历史 L2 治理缺口。
- 不重写任何既有 Git 历史、既有 tag 或远端分支。
- 不新增跨仓自动发布器；本次以可验证的现有脚本和明确顺序完成发布。

## 发布契约

### 统一版本源

1. 每个 `SKILL.md` 的 frontmatter 使用 `version: 1.0.0`。缺失该字段的
   当前 Skill 补齐；不保留任何当前 `version` 的其它数值。
2. X5 的 `x5/VERSION` 与 S 的 `horizon/VERSION` 均为 `1.0.0`。
3. Hub 的 `components.d/bsp-skills.yml`、`rdk-device.yml`、
   `oe-tool-chain-x5.yml` 与 `oe-tool-chain-s.yml` 都显式使用
   `ref: v1.0.0`。所有四个来源都由不可变发布 tag 固定。
4. 生成的 pack registry、skill index、插件内副本和 Hub 镜像必须由上述
   组件声明生成，不能手工编辑后绕过生成器。
5. 安装器继续比较 `INSTALLED_REF`（缺失时回退 `VERSION`）与组件 ref；
   新发布时比较结果必须把 `v1.0.0` 与 `1.0.0` 判为同一版本。

### BSP 最终优化

每个 BSP Skill 必须在不改变其专业边界的前提下满足下列行为质量：

- description 能区分环境准备、源码同步、镜像、内核、deb、bootloader、
  rootfs 和 S 系列，不让路由到相邻 Skill。
- instructions 先判断 host/target、板型、分支/manifest、磁盘空间和所需
  权限，再给出可执行命令。
- `repo sync`、大体积下载、镜像构建、rootfs 修改、bootloader/刷写相关动作
  先说明影响、预计成本、备份或中止点，并在不可逆动作前请求确认。
- evals 对每个 Skill 至少覆盖成功路径、相邻 Skill 分流或前置条件失败、
  安全确认之一；评测断言行为而非仅匹配文档文本。
- `skill-card.md` 与 `SKILL.md` 不重复且反映同一触发边界。

若优化发现现有 `setup.sh` 或安装/升级流程会让用户收到错误版本、跳过需要
确认的破坏性动作、或无法诊断版本来源，允许以测试先行方式修改这些流程。

## 仓库与数据流

```text
bsp-skills ─┐
rdk-device-skills ─┼─(v1.0.0 source tags)─> rdk-skills components + sync mirrors
oe-skills-x5 ──────┤                                │
oe-skills-s ───────┘                                ├─> generated catalogs
                                                     └─> d-robotics-skills plugin
```

每个 source 仓库先在 `release/v1.0.0` 分支完成版本和内容修改。X5/S 的
release branch 必须先产生本地 `v1.0.0` tag，Hub 才能以该 tag 同步完整
资源树。Hub 在本地完成镜像、生成和插件构建后再进入发布阶段。

`rdk-device-skills` 的既有 `fix/plugin-catalog-remediation` 三个提交先
进入其 release branch，作为 `v1.0.0` 的一部分；Hub 镜像必须与其发布
内容逐字节对应。

## 测试与门禁

### 测试先行

- 先为“所有当前版本字段为 1.0.0”“每个组件 ref 为 v1.0.0”“生成目录与
  插件副本一致”“安装器正确判定 v1.0.0 已安装/需升级”写失败测试。
- BSP 文档优化先进行无改动的压力任务基线；修改后以相同的真实 BSP 场景
  forward-test，确认路由、前置检查和确认点被遵循。
- 任何 setup/installer 行为改变都先用临时项目目录的端到端测试证明失败，
  再最小化实现到通过。

### 发布前验证

1. BSP 8 个 Skill 和 Hub 全部相关 Skill 的严格校验为 L1=0、L2=0。
2. BSP、device、X5、S 的各自测试和 Hub `python -B -m unittest discover
   -s tests -v` 通过；仅记录并单独复测环境导致的 skip。
3. X5/S `setup.sh` 覆盖 fresh install、same-version no-op、upgrade、
   `--force`、未知参数与 `--ref v1.0.0`。
4. Hub 目录连续生成两次结果相同；全部 JSON 可解析；plugin build 成功；
   canonical/Hub/plugin 与 source/Hub 的要求镜像哈希一致。
5. Source 的退休路由与 workspace-router 契约问题均为 0；其既有完整
   sandbox 失败按已记录基线报告，不被伪装为通过。
6. 每个待发布仓库 `git diff --check` 通过，工作树干净，且远端不存在
   `refs/tags/v1.0.0`。

## 发布顺序与失败处理

1. `bsp-skills`：推送 release commit 到 `main`，再推 annotated `v1.0.0`。
2. `oe-skills-x5`：同样推送 commit 与 tag。
3. `oe-skills-s`：同样推送 commit 与 tag。
4. `rdk-device-skills`：合入 release 内容，推送 `main` 与 tag。
5. `rdk-skills`：合入 Hub release 内容，推送 `main` 与 tag。

任何仓库的 push 或 tag push 失败即停止后续发布。已经公开的 tag 不删除；
修复只能以新提交和新的补丁版本发布。Hub 仅在其四个上游 tag 都可解析后
发布，以避免 registry 指向不可用来源。

## 文档与发布记录

- 每个仓库的 CHANGELOG 或 release note 记录“统一 v1.0.0 基线”的范围与
  兼容性影响。
- Hub CHANGELOG 将当前首发 `0.1.0` 重新表达为历史本地标签，并新增
  `[1.0.0]` 正式发布条目；所有用户可复制的升级示例改用 `v1.0.0`。
- 用户在升级 X5/S workspace 前仍必须确认：版本变化会重建 workspace，
  清除其中的本地修改。
