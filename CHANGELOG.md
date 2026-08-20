<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# Changelog

本文件记录本项目的所有重要变更。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.1.0] - 2026-08-20

> 首个发布 tag。此前 CHANGELOG 中的 0.1.0~0.3.0 编号从未打过 git tag，仅作文档编号；版本序列自本版起正式重启，历史条目见文末「0.x 历史（未打 tag）」。

### 新增

- 为 workspace Pack 提供随分发包提交的确定性注册表，并新增 `rdk-skill-finder`，可发现扁平 Skill 或将 workspace Skill 交接给安装器。
- OE workspace Pack 在 Hub 镜像为完整安装源：`skills/oe-skills-x5/`、`skills/oe-skills-s/` 包含完整资源树 + `setup.sh` 覆盖层，克隆 Hub 目录即可整包安装；`rdk-pack-installer` 主路径改为 Hub 镜像，Pack 仓库保留为降级源。
- `setup.sh` 升级机制：`--update`（先比已装 `VERSION` 与镜像 `VERSION`，相同即跳过，不同则删除重建 workspace 不残留旧文件）、`--force`（忽略比较强制重建）、`--ref <tag>`（把安装来源 tag 写入 `<workspace_dir>/INSTALLED_REF`）。`rdk-pack-installer` 将项目侧 `INSTALLED_REF`（缺失回退 `VERSION`）与注册表 `ref` 归一化比对（去前导 `v`），相同报已最新，不同才执行 `--update --ref` 升级并要求显式确认。
- 新增 `tests/test_pack_upgrade.py`：bash 门控端到端测试，实跑两个 Pack 的镜像 `setup.sh`，覆盖安装锚点记录、同版本 no-op、跨版本重建清残留、`--force`、旧式单参与未知参数拒绝。

### 变更

- 将安装器统一为 `rdk-pack-installer`，使其从自身打包的注册表读取安装与验证契约；插件同时分发 finder、installer 和 `rdk-docs-reference`。
- workspace Pack 注册锁定不可变发布 tag：`components.d/oe-tool-chain.yml` 更名为 `oe-tool-chain-x5.yml`，ref 锁定 `v2.1.0`/`v0.3.0`（与 Pack 内 `VERSION` 一一对应；发布新版时需同时 bump VERSION 并打新 tag，tag 只增不改）。
- 在设备 Skill 源头及 Hub 镜像中移除失效路由，替换为现有能力或明确的 `rdk-docs-reference` 文档检索交接。
- 统一公开许可证说明：代码与脚本采用 Apache-2.0，文档内容采用 CC-BY-4.0；Skill 顶层 frontmatter 继续遵循 ADR 0004 使用 `license: Apache-2.0`。
- 同步工作流从每日 2:00 UTC 改为每小时运行（仍保留手动 dispatch 与 components.d 变更触发）。

## 0.x 历史（未打 tag，编号已作废）

以下版本号仅存在于旧 CHANGELOG 条目中，从未打过 git tag，仅作历史存档。

### [0.3.0] - 2026-08-04

#### 变更

- `components.d/rdk-device.yml` 的 `repo` 从 `D-Robotics/rdk-device-skills` 修正为 `D-Robotics/device-knowledge`
- `validate.py` 与 device-knowledge 的 `sandbox.py` 约定对齐：
  - `license` 从推荐改为必填（`REQUIRED_FRONTMATTER` 加入 `license`）
  - 新增 4 个必填 section 检查：`## Purpose`、`## When to use`、`## Instructions`、`## Safety`
  - 新增 `scripts/*.sh` 的 `bash -n` 语法检查
  - 新增 `references/*.md` 引用存在性检查
- `CONTRIBUTING.md` 重写，与 device-knowledge 的标准统一：
  - frontmatter 表补 `metadata.data-classification`，`license` 从推荐改为必填
  - 新增 SKILL.md 必填 section 说明（Purpose / When to use / Instructions / Safety）
  - 新增 evals/tasks.yaml 格式规范（id / dimension / prompt / expect.skill / expect.behavior）
  - 新增五维评测说明（Security / Correctness / Discoverability / Effectiveness / Efficiency）
  - 新增设计原则（官方文档为真相源、观察/行动分离、不编造、自包含、description 为路由信号）
  - 新增 Pack 级推荐基础设施（Makefile / install.sh / sandbox.py），参考 device-knowledge

### [0.2.0] - 2026-07-28

#### 新增

- 中央目录仓库架构升级，补齐完整的 Pack 注册与同步体系：
  - `components.d/README.md` — Pack 注册规范文档
  - `plugins.d/` — 插件构建配置（`README.md`、`_defaults.yml`、`d-robotics-skills.yml`）
  - `catalog-exceptions.yml` — orphan 清理白名单
  - `skills.sh.json` — Skills.sh marketplace 分组配置
  - `.cursor-plugin/marketplace.json` — Cursor marketplace 元数据
  - `SECURITY.md` — 安全漏洞报告流程
  - `CODE_OF_CONDUCT.md` — 社区行为准则
  - `LICENSE-APACHE` + `LICENSE-CC-BY-4.0` — 双许可，替代原先的单一 LICENSE
- 同步流水线从 Python 脚本迁移到 bash + yq：
  - `.github/workflows/sync-skills.yml` — 每日 2:00 UTC + `components.d/` 变更触发
  - `.github/scripts/regenerate-readme.sh` — 从 `components.d/*.yml` 自动重生成 README 表格
  - `.github/scripts/prune-orphans.sh` — 清理未注册的 `skills/` 目录（5 目录安全阈值）
  - `.github/scripts/build-plugins.sh` — 从 `plugins.d/*.yml` 构建插件分发包
  - `.github/scripts/validate.py` — Skill 结构校验（frontmatter、name 格式、description 长度、evals 完整性）
- `.github/workflows/dco.yml` — DCO 签名检查
- 注册两个 Skill Pack：
  - `components.d/rdk-device.yml` — 14 个板端设备 Skill（诊断、内存、无头模式、摄像头、模型部署/基准、GPIO、TogetheROS.Bot、文档检索）
  - `components.d/oe-tool-chain.yml` — 60+ 个 OE 工具链 Skill（量化、编译、推理、评测、诊断）
- 中英双语 README（`README.md` 英文、`README_cn.md` 中文，顶部互相跳转）

#### 变更

- `README.md` 重写：硬件优先，中文为主，调整章节顺序为「板卡 → 安装 → 目录 → 反馈 → 结构 → 仓库结构 → 路线图 → 许可证」
- `components.d/` 字段格式统一为 `name`/`repo`/`description`/`skills[]`（`path` + `catalog_dir`），替代原先的非标准字段
- `CONTRIBUTING.md` 重写，改为 D-Robotics 实际流程导向

#### 移除

- `sync.py`（Python）— 由 bash + yq 同步流水线替代
- 旧版 `validate.py` — 由增强版替代
- `skill-index.json` — 由同步流水线按需生成
- 旧版 `sync.yml` — 由 `sync-skills.yml` 替代
- 单一 `LICENSE` — 由双许可（`LICENSE-APACHE` + `LICENSE-CC-BY-4.0`）替代
- 旧版 `components.d/oe-skills.yml`（非标准字段）— 由标准格式替代

### [0.1.0] - 2026-07-27

#### 新增

- 初始中央目录仓库骨架
- `components.d/oe-skills.yml` — 首个 Pack 注册（OE 工具链）
- `sync.py` — Python 同步脚本
- `validate.py` — 基础 Skill 校验器
- `.claude-plugin/marketplace.json` — Claude Code marketplace 入口
- `.agents/plugins/marketplace.json` — Codex marketplace 入口
- `CONTRIBUTING.md`、`LICENSE`、`.gitignore`
- `README.md` — Pack 列表与安装指引
