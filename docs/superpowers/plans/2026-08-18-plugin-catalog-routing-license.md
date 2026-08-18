# Plugin Catalog、路由与许可证修复实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 Hub 插件自带 workspace Pack 注册表和真实 Skill finder，修复 RDK Device Pack 中的失效路由，并使许可证文档与 ADR 0004 一致。

**Architecture:** 使用一个 Python 目录生成模块把 `components.d`、Skill frontmatter 和 `catalog-exceptions.yml` 规范化为两个确定性 JSON 文件；`rdk-pack-installer` 与 `rdk-skill-finder` 分别把所需 JSON 放在自身 `references/` 内，因此可独立安装。路由内容只在 `rdk-device-skills` 源头编辑，验证后机械同步到 Hub 镜像。

**Tech Stack:** Python 3.10+、标准库 `unittest`、PyYAML 6.0.2、Bash、Mike Farah yq v4、GitHub Actions。

**Spec:** `docs/superpowers/specs/2026-08-18-plugin-catalog-routing-license-design.zh-CN.md`

## Global Constraints

- Hub 原生 Skill 名称固定为 `rdk-pack-installer` 与 `rdk-skill-finder`。
- 不新增 `rdk-ros`、`rdk-device`、`rdk-doc-finder` 等领域 Skill。
- 失效路由只能指向现有 Skill，或明确说明当前未覆盖并交给 `rdk-docs-reference` 做事实检索。
- workspace 注册路径必须是安全的项目相对路径，禁止绝对路径和 `..`。
- 生成 JSON 必须使用 UTF-8、两空格缩进、稳定排序并以换行结尾。
- 顶层 frontmatter 保持 `license: Apache-2.0`；内容许可范围按 ADR 0004 解释为 CC-BY-4.0，不对既有内容重新授权。
- 所有生产行为先写失败测试并观察预期失败，再写最小实现。
- `rdk-device-skills` 是设备 Skill 内容源头；`rdk-skills/skills/rdk-*` 只接收源头镜像。

## File Map

- `.github/scripts/generate_plugin_catalog.py`：解析注册表和 Skill 元数据，生成 Pack 注册表与 Skill 索引。
- `.github/requirements.txt`：固定目录生成器的 PyYAML 版本。
- `tests/test_generate_plugin_catalog.py`：目录生成、确定性、重复项和路径安全测试。
- `tests/test_plugin_contract.py`：Hub 原生 Skill、插件 include 和安装器自包含契约测试。
- `tests/test_license_contract.py`：ADR 0004 与公开文档表述一致性测试。
- `skills/rdk-pack-installer/`：由旧安装器重命名并改为读取随包注册表。
- `skills/rdk-skill-finder/`：新的目录发现 Skill 和只读搜索脚本。
- `plugins.d/d-robotics-skills.yml`：声明三个 Hub 插件 Skill。
- `.github/scripts/build-plugins.sh`：构建前生成目录数据并拒绝缺失 include。
- `rdk-device-skills/tools/sandbox.py`：加入废弃路由完整性检查。
- `rdk-device-skills/skills/*/SKILL.md`：修复失效路由的唯一源头。

---

### Task 1: 生成 workspace Pack 注册表和 Skill 索引

**Files:**
- Create: `rdk-skills/.github/scripts/generate_plugin_catalog.py`
- Create: `rdk-skills/.github/requirements.txt`
- Modify: `rdk-skills/.github/workflows/sync-skills.yml`
- Create: `rdk-skills/tests/test_generate_plugin_catalog.py`
- Modify: `rdk-skills/components.d/oe-tool-chain.yml`
- Modify: `rdk-skills/components.d/oe-tool-chain-s.yml`
- Modify: `rdk-skills/components.d/README.md`

**Interfaces:**
- Produces: `load_components(repo_root: Path) -> list[dict]`
- Produces: `build_pack_registry(repo_root: Path, components: list[dict]) -> dict`
- Produces: `build_skill_index(repo_root: Path, components: list[dict], exceptions: list[dict]) -> dict`
- Produces: `validate_plugin_includes(repo_root: Path) -> None`
- Produces: `generate(repo_root: Path, target: Literal["pack", "skills", "all"] = "all") -> list[Path]`
- Produces CLI: `python .github/scripts/generate_plugin_catalog.py --repo-root . --target pack|skills|all`
- Produces CLI check: `python .github/scripts/generate_plugin_catalog.py --repo-root . --check-plugin-includes`
- Writes: `skills/rdk-pack-installer/references/pack-registry.json`
- Writes: `skills/rdk-skill-finder/references/skill-index.json`

目录解析规则固定如下：flat 条目从组件的每个 `skills[].catalog_dir` 读取
`skills/<catalog_dir>/SKILL.md`；workspace 条目递归读取
`skills/<catalog_dir>/**/SKILL.md`；Hub 原生条目读取
`catalog-exceptions.yml` 中每个 `exceptions[].dir` 对应的
`skills/<dir>/SKILL.md`。输出中的 `catalog_path` 一律相对于 Hub 根目录，
并使用 POSIX 分隔符。Pack 注册表只收录 `install_type: workspace` 的组件；
组件未声明 `ref` 时输出 `main`。

- [ ] **Step 1: 添加 workspace 安装契约的失败测试**

在 `tests/test_generate_plugin_catalog.py` 创建临时 Hub fixture，写入 X5/S 两个组件，断言输出字段完整：

```python
def test_pack_registry_contains_declared_workspace_contracts(self):
    registry = catalog.build_pack_registry(self.repo, catalog.load_components(self.repo))
    packs = {item["repo"]: item for item in registry["packs"]}
    self.assertEqual(packs["D-Robotics/oe-skills-x5"]["workspace_dir"], ".drobotics")
    self.assertIn(".drobotics/skills/x5-router/SKILL.md",
                  packs["D-Robotics/oe-skills-x5"]["verify_paths"])
    self.assertEqual(packs["D-Robotics/oe-skills-s"]["workspace_dir"], ".horizon")
    self.assertIn(".horizon/skills/horizon-router/SKILL.md",
                  packs["D-Robotics/oe-skills-s"]["verify_paths"])
```

- [ ] **Step 2: 运行测试并确认因生成模块不存在而失败**

Run: `python -m unittest tests.test_generate_plugin_catalog -v`

Expected: `ModuleNotFoundError` 或找不到 `.github/scripts/generate_plugin_catalog.py`。

- [ ] **Step 3: 添加组件字段和最小 Pack 注册表实现**

在 X5 注册条目加入：

```yaml
workspace_dir: .drobotics
verify_paths:
  - .drobotics/X5.md
  - .drobotics/VERSION
  - .drobotics/skill-index.json
  - .drobotics/skills/x5-router/SKILL.md
```

在 S 注册条目加入：

```yaml
workspace_dir: .horizon
verify_paths:
  - .horizon/HORIZON.md
  - .horizon/VERSION
  - .horizon/skill-index.json
  - .horizon/skills/horizon-router/SKILL.md
```

生成模块使用 `yaml.safe_load`，并实现安全路径校验：

```python
def require_safe_relative(value: str, field: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or "\\" in value:
        raise CatalogError(f"{field} must be a safe POSIX relative path: {value!r}")
    return value
```

在 `sync-skills.yml` 的 checkout 之后安装固定依赖：

```yaml
- name: Install catalog generator dependencies
  run: python3 -m pip install -r .github/requirements.txt
```

- [ ] **Step 4: 运行单测确认 Pack 注册表测试通过**

Run: `python -m unittest tests.test_generate_plugin_catalog -v`

Expected: workspace contract 测试 PASS。

- [ ] **Step 5: 添加 Skill 索引和确定性失败测试**

测试 fixture 同时包含一个 flat Skill、一个 bulk workspace Skill 和一个 Hub exception，断言：

```python
def test_skill_index_contains_flat_workspace_and_hub_records(self):
    index = catalog.build_skill_index(self.repo, self.components, self.exceptions)
    records = {item["name"]: item for item in index["skills"]}
    self.assertEqual(records["rdk-diagnostic"]["install_type"], "flat")
    self.assertEqual(records["x5-router"]["install_type"], "workspace")
    self.assertEqual(records["rdk-pack-installer"]["repo"], "D-Robotics/rdk-skills")

def test_generated_json_is_byte_for_byte_deterministic(self):
    first = catalog.render_json(self.index)
    second = catalog.render_json(self.index)
    self.assertEqual(first, second)
    self.assertTrue(first.endswith("\n"))
```

- [ ] **Step 6: 运行测试并确认 Skill 索引行为尚未实现**

Run: `python -m unittest tests.test_generate_plugin_catalog -v`

Expected: `build_skill_index` 或 `render_json` 相关断言 FAIL。

- [ ] **Step 7: 实现索引生成、重复检查和错误路径检查**

实现以下失败条件：

```python
if name in seen_names:
    raise CatalogError(f"duplicate skill name: {name}")
if catalog_path in seen_paths:
    raise CatalogError(f"duplicate catalog path: {catalog_path}")
```

补充测试覆盖无效 frontmatter、重复名称、重复 catalog 路径、缺失 `workspace_dir`、空 `verify_paths`、绝对路径和 `..` 路径。再建立一个缺失 `include_skills` 目录的 fixture，断言 `validate_plugin_includes()` 抛出 `CatalogError("missing include_skills path: skills/not-present/")`。

- [ ] **Step 8: 运行目录生成测试并确认通过**

Run: `python -m unittest tests.test_generate_plugin_catalog -v`

Expected: 全部 PASS。

- [ ] **Step 9: 更新组件字段文档并提交**

在 `components.d/README.md` 说明 `workspace_dir`、`verify_paths` 的必填条件和安全路径约束。

```bash
git add .github/requirements.txt .github/scripts/generate_plugin_catalog.py .github/workflows/sync-skills.yml tests/test_generate_plugin_catalog.py components.d/README.md components.d/oe-tool-chain.yml components.d/oe-tool-chain-s.yml
git commit -s -m "feat: generate bundled plugin catalog data"
```

---

### Task 2: 将安装器重命名并改为随包注册表驱动

**Files:**
- Rename: `rdk-skills/skills/d-robotics-pack-installer/` → `rdk-skills/skills/rdk-pack-installer/`
- Modify: `rdk-skills/skills/rdk-pack-installer/SKILL.md`
- Modify: `rdk-skills/skills/rdk-pack-installer/skill-card.md`
- Modify: `rdk-skills/skills/rdk-pack-installer/evals/tasks.yaml`
- Modify: `rdk-skills/catalog-exceptions.yml`
- Create: `rdk-skills/tests/test_plugin_contract.py`

**Interfaces:**
- Consumes: `skills/rdk-pack-installer/references/pack-registry.json`
- Produces: self-contained Skill contract with no runtime dependency on `components.d`

- [ ] **Step 1: 写安装器自包含和命名失败测试**

```python
def test_installer_is_named_rdk_pack_installer(self):
    text = self.skill_md.read_text(encoding="utf-8")
    self.assertIn("name: rdk-pack-installer", text)
    self.assertFalse((self.repo / "skills/d-robotics-pack-installer").exists())

def test_installer_reads_bundled_registry_not_components_directory(self):
    text = self.skill_md.read_text(encoding="utf-8")
    self.assertIn("references/pack-registry.json", text)
    self.assertNotIn("components.d", text)
    self.assertTrue((self.skill_dir / "references/pack-registry.json").is_file())
```

- [ ] **Step 2: 运行测试并确认旧目录和旧说明导致失败**

Run: `python -m unittest tests.test_plugin_contract.PluginContractTests -v`

Expected: 目录名、frontmatter 名称和 `components.d` 依赖断言 FAIL。

- [ ] **Step 3: 重命名目录并更新 Skill 契约**

执行 `git mv skills/d-robotics-pack-installer skills/rdk-pack-installer`。将安装器第一步改为：

```markdown
1. **Locate the bundled registry.** Read `references/pack-registry.json`
   relative to this Skill directory. Match the request against `name`,
   `repo`, and Skill descriptions. Reject unknown packs; do not infer a repo.
```

验证步骤逐项读取 `verify_paths`，并在写操作前展示 `workspace_dir`。同步修改 skill-card、evals、`catalog-exceptions.yml` 中的名称和路径。

- [ ] **Step 4: 生成安装器注册表并运行契约测试与单 Skill 校验**

Run: `python .github/scripts/generate_plugin_catalog.py --repo-root . --target pack`

Expected: 生成 `skills/rdk-pack-installer/references/pack-registry.json`，且不要求 `rdk-skill-finder` 已存在。

Run: `python -m unittest tests.test_plugin_contract.PluginContractTests -v`

Expected: PASS。

Run: `python .github/scripts/validate.py --skill rdk-pack-installer --mode enforcing --strict-l2`

Expected: `OK rdk-pack-installer`，退出码 0。

- [ ] **Step 5: 提交安装器重命名**

```bash
git add skills/rdk-pack-installer catalog-exceptions.yml tests/test_plugin_contract.py
git add -u skills/d-robotics-pack-installer
git commit -s -m "feat: make pack installer self-contained"
```

---

### Task 3: 新增真实的 `rdk-skill-finder`

**Files:**
- Create: `rdk-skills/skills/rdk-skill-finder/SKILL.md`
- Create: `rdk-skills/skills/rdk-skill-finder/skill-card.md`
- Create: `rdk-skills/skills/rdk-skill-finder/evals/tasks.yaml`
- Create: `rdk-skills/skills/rdk-skill-finder/scripts/search_catalog.py`
- Generated: `rdk-skills/skills/rdk-skill-finder/references/skill-index.json`
- Modify: `rdk-skills/catalog-exceptions.yml`
- Create: `rdk-skills/tests/test_search_catalog.py`

**Interfaces:**
- Produces CLI: `python scripts/search_catalog.py QUERY [--pack NAME] [--platform TOKEN] [--install-type flat|workspace] [--limit N]`
- Produces JSON: `{"query": str, "matches": list[Match], "fallback": str | null}`
- Match fields: `name`, `description`, `pack`, `repo`, `catalog_path`, `install_type`, `score`, `action`
- Filtering: `--pack` 对 Pack 名称做大小写不敏感精确匹配；`--platform` 在
  `name`、`description`、`pack`、`catalog_path` 的规范化文本中做词项匹配。
- Errors: 索引缺失、JSON 无效或 schema 不受支持时输出
  `{"error": str, "matches": [], "fallback": null}` 并返回非零退出码。

- [ ] **Step 1: 写精确名称、过滤和无匹配失败测试**

```python
def test_exact_skill_name_ranks_first(self):
    result = finder.search(self.index, "rdk-diagnostic")
    self.assertEqual(result["matches"][0]["name"], "rdk-diagnostic")

def test_workspace_filter_returns_installer_handoff(self):
    result = finder.search(self.index, "模型量化", platform="X5", install_type="workspace")
    self.assertEqual(result["matches"][0]["install_type"], "workspace")
    self.assertEqual(result["matches"][0]["action"], "use rdk-pack-installer")

def test_no_match_uses_docs_fallback_without_inventing_skill(self):
    result = finder.search(self.index, "完全无关的诗歌创作")
    self.assertEqual(result["matches"], [])
    self.assertEqual(result["fallback"], "rdk-docs-reference")

def test_invalid_index_returns_structured_cli_error(self):
    completed = self.run_cli(index_text="{not-json")
    payload = json.loads(completed.stdout)
    self.assertNotEqual(completed.returncode, 0)
    self.assertEqual(payload["matches"], [])
    self.assertIsNone(payload["fallback"])
```

- [ ] **Step 2: 运行测试并确认搜索模块不存在**

Run: `python -m unittest tests.test_search_catalog -v`

Expected: 导入 `search_catalog.py` 失败。

- [ ] **Step 3: 实现最小确定性搜索**

分词规则固定为：ASCII 字母数字序列先 `casefold()`；连续汉字片段保留完整片段，
并生成相邻双字词，以支持“模型量化”等中文查询且避免单字造成大量误命中。
评分规则固定为：

```python
score = 0
if query_normalized == name_normalized:
    score += 100
score += 10 * len(query_tokens & name_tokens)
score += 3 * len(query_tokens & description_tokens)
```

结果按 `(-score, name)` 排序；`score == 0` 不返回。flat action 为：

```python
f"npx skills add d-robotics/rdk-skills --skill {record['name']}"
```

workspace action 固定为 `use rdk-pack-installer`。

- [ ] **Step 4: 运行搜索单测并确认通过**

Run: `python -m unittest tests.test_search_catalog -v`

Expected: 全部 PASS。

- [ ] **Step 5: 编写 Finder Skill、治理卡和五维 evals**

`SKILL.md` 必须包含 Purpose、When to use、Instructions、Safety，并规定先运行搜索脚本再推荐安装命令。`evals/tasks.yaml` 至少覆盖：精确名称、中文任务发现、workspace handoff、无关请求拒绝、只读安全。

- [ ] **Step 6: 生成真实索引并校验 Finder**

Run: `python .github/scripts/generate_plugin_catalog.py --repo-root . --target all`

Run: `python skills/rdk-skill-finder/scripts/search_catalog.py "X5 模型量化" --install-type workspace`

Expected: JSON 中包含 `x5-router` 或 X5 workspace Pack 记录，action 为 `use rdk-pack-installer`。

Run: `python .github/scripts/validate.py --skill rdk-skill-finder --mode enforcing --strict-l2`

Expected: 退出码 0。

- [ ] **Step 7: 提交 Finder**

```bash
git add skills/rdk-skill-finder catalog-exceptions.yml tests/test_search_catalog.py
git commit -s -m "feat: add RDK skill finder"
```

---

### Task 4: 把三个 Hub Skill 正确打包进插件

**Files:**
- Modify: `rdk-skills/plugins.d/d-robotics-skills.yml`
- Modify: `rdk-skills/.github/scripts/build-plugins.sh`
- Modify: `rdk-skills/.github/workflows/sync-skills.yml`
- Modify: `rdk-skills/tests/test_plugin_contract.py`
- Regenerate: `rdk-skills/plugins/d-robotics-skills/**`
- Regenerate: `rdk-skills/.claude-plugin/marketplace.json`
- Regenerate: `rdk-skills/.agents/plugins/marketplace.json`
- Regenerate: `rdk-skills/.cursor-plugin/marketplace.json`
- Regenerate: `rdk-skills/.dsh-plugin/marketplace.json`
- Modify: `rdk-skills/README.md`
- Modify: `rdk-skills/README_cn.md`
- Modify: `rdk-skills/docs/SKILL-USAGE.md`

**Interfaces:**
- Consumes: generated registry/index and `plugins.d/d-robotics-skills.yml`
- Produces: plugin tree containing exactly the three declared Hub Skill directories

- [ ] **Step 1: 扩展插件契约失败测试**

```python
def test_plugin_definition_includes_three_hub_skills(self):
    config = yaml.safe_load((self.repo / "plugins.d/d-robotics-skills.yml").read_text())
    self.assertEqual(config["include_skills"], [
        "skills/rdk-skill-finder/",
        "skills/rdk-pack-installer/",
        "skills/rdk-docs-reference/",
    ])

def test_generated_plugin_contains_three_hub_skills(self):
    names = {p.name for p in (self.repo / "plugins/d-robotics-skills/skills").iterdir()}
    self.assertEqual(names, {"rdk-skill-finder", "rdk-pack-installer", "rdk-docs-reference"})
    self.assertTrue((self.repo / "plugins/d-robotics-skills/skills/rdk-pack-installer/references/pack-registry.json").is_file())
    self.assertTrue((self.repo / "plugins/d-robotics-skills/skills/rdk-skill-finder/references/skill-index.json").is_file())
```

- [ ] **Step 2: 运行测试并确认旧插件组成导致失败**

Run: `python -m unittest tests.test_plugin_contract -v`

Expected: include 列表和生成插件目录断言 FAIL。

- [ ] **Step 3: 更新插件定义与构建前置检查**

将 `include_skills` 设置为测试中的固定顺序。`build-plugins.sh` 在任何删除操作前执行：

```bash
python3 .github/scripts/generate_plugin_catalog.py --repo-root .
python3 .github/scripts/generate_plugin_catalog.py --repo-root . --check-plugin-includes
```

删除当前对缺失目录的静默跳过逻辑。`validate_plugin_includes()` 的失败单测已在 Task 1 建立，因此这一步只连接经过测试的接口。

同时把 `sync-skills.yml` 的插件构建从“失败只警告”改为直接执行并传播非零退出码，
并在构建前运行 `python3 -m unittest discover -s tests -v`。这样缺失 include、
生成器错误或契约回归都能阻断同步提交。

- [ ] **Step 4: 重建插件并运行契约测试**

Run: `bash .github/scripts/build-plugins.sh`

Expected: 成功生成三个 Skill 目录；旧 `d-robotics-pack-installer` 目录消失。

Run: `python -m unittest tests.test_plugin_contract -v`

Expected: PASS。

- [ ] **Step 5: 修正文档中的插件能力描述**

README 中统一说明：插件通过 finder 搜索目录；flat Skill 返回安装命令；workspace Skill 交给 `rdk-pack-installer`。删除“完整目录可直接按需加载”以及旧安装器名称。

- [ ] **Step 6: 提交插件分发变更**

```bash
git add plugins.d/d-robotics-skills.yml .github/scripts/build-plugins.sh .github/workflows/sync-skills.yml plugins/d-robotics-skills .claude-plugin .agents/plugins .cursor-plugin .dsh-plugin README.md README_cn.md docs/SKILL-USAGE.md tests/test_plugin_contract.py
git add -u plugins/d-robotics-skills
git commit -s -m "feat: package finder and registry-backed installer"
```

---

### Task 5: 在 `rdk-device-skills` 源头修复失效路由

**Files:**
- Modify: `rdk-device-skills/tools/sandbox.py`
- Modify: `rdk-device-skills/skills/rdk-accessories/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-board-delegate/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-board-knowledge/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-command-manual/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-ecosystem/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-embodied-lerobot/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-hardware/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-llm-deployment/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-log-forensics/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-model-zoo/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-multimedia/SKILL.md`
- Modify: `rdk-device-skills/skills/rdk-source-map/SKILL.md`

**Interfaces:**
- Produces: `retired_route_problems(skills: dict) -> list[str]`
- Retired exact tokens: `rdk-device`, `rdk-doc-finder`, `rdk-ros`, `rdk-mipi-camera-bringup`, `rdk-perf-investigator`

- [ ] **Step 1: 添加废弃路由失败检查**

在 `tools/sandbox.py` 中加入：

```python
RETIRED_ROUTES = {
    "rdk-device",
    "rdk-doc-finder",
    "rdk-ros",
    "rdk-mipi-camera-bringup",
    "rdk-perf-investigator",
}

def retired_route_problems(skills):
    problems = []
    for name, skill in skills.items():
        for route in RETIRED_ROUTES:
            pattern = rf"(?<![a-z0-9-]){re.escape(route)}(?![a-z0-9-])"
            if re.search(pattern, skill["text"], re.I):
                problems.append(f"{name}: references retired route '{route}'")
    return problems
```

把结果加入现有 `validate()` 返回的问题列表。

- [ ] **Step 2: 运行源头校验并确认发现已知失效路由**

Workdir: `rdk-device-skills`

Run: `python tools/sandbox.py validate`

Expected: FAIL，并列出五个 retired route 中实际存在的引用。

- [ ] **Step 3: 按已批准映射修改所有源头 SKILL.md**

使用以下固定规则：

```text
rdk-doc-finder -> rdk-docs-reference
rdk-mipi-camera-bringup -> rdk-camera-setup
rdk-device（板端推理） -> rdk-model-deploy
rdk-device（自有模型转换） -> x5-router（X5）/ horizon-router（S 系列）
rdk-device（X3/Ultra 自有模型转换） -> 当前无专用 Skill；使用 rdk-docs-reference 检索对应板卡的官方工具链文档
rdk-ros（安装、环境、命令） -> rdk-tros-setup
rdk-ros（节点或应用开发） -> 当前无专用 Skill；使用 rdk-docs-reference 检索 tros_doc
rdk-perf-investigator -> 删除 Skill 名称，改为“上层诊断编排”
```

- [ ] **Step 4: 运行源头完整测试并确认通过**

Run: `python tools/sandbox.py validate`

Expected: 0 个 retired route 问题。

Run: `python tools/sandbox.py test`

Expected: `RESULT: PASS`。

- [ ] **Step 5: 提交源头路由修复**

```bash
git add tools/sandbox.py skills/*/SKILL.md
git commit -s -m "fix: replace retired skill routes"
```

---

### Task 6: 将源头路由修复同步到 Hub 镜像

**Files:**
- Modify: corresponding `rdk-skills/skills/rdk-*/SKILL.md` files from Task 5
- Modify: `rdk-skills/tests/test_plugin_contract.py`

**Interfaces:**
- Consumes: committed `rdk-device-skills` Skill files
- Produces: byte-identical Hub mirrors for every changed `SKILL.md`

- [ ] **Step 1: 添加 Hub 镜像路由完整性失败测试**

```python
def test_hub_device_mirror_has_no_retired_routes(self):
    retired = ("rdk-device", "rdk-doc-finder", "rdk-ros",
               "rdk-mipi-camera-bringup", "rdk-perf-investigator")
    for path in (self.repo / "skills").glob("rdk-*/SKILL.md"):
        text = path.read_text(encoding="utf-8")
        for route in retired:
            pattern = rf"(?<![a-z0-9-]){re.escape(route)}(?![a-z0-9-])"
            self.assertIsNone(re.search(pattern, text, re.I), f"{path}: {route}")
```

- [ ] **Step 2: 运行 Hub 测试并确认镜像仍包含旧路由**

Run: `python -m unittest tests.test_plugin_contract -v`

Expected: retired route 断言 FAIL。

- [ ] **Step 3: 从源头机械复制变更的 SKILL.md**

在 PowerShell 中对 Task 5 的十二个 Skill 名执行：

```powershell
$skillNames = @(
  'rdk-accessories','rdk-board-delegate','rdk-board-knowledge','rdk-command-manual',
  'rdk-ecosystem','rdk-embodied-lerobot','rdk-hardware','rdk-llm-deployment',
  'rdk-log-forensics','rdk-model-zoo','rdk-multimedia','rdk-source-map'
)
foreach ($name in $skillNames) {
  Copy-Item -LiteralPath "..\rdk-device-skills\skills\$name\SKILL.md" `
            -Destination "skills\$name\SKILL.md" -Force
}
```

- [ ] **Step 4: 验证源头和镜像逐字节相同**

```powershell
foreach ($name in $skillNames) {
  $source = (Get-FileHash "..\rdk-device-skills\skills\$name\SKILL.md" -Algorithm SHA256).Hash
  $mirror = (Get-FileHash "skills\$name\SKILL.md" -Algorithm SHA256).Hash
  if ($source -ne $mirror) { throw "mirror mismatch: $name" }
}
```

Run: `python -m unittest tests.test_plugin_contract -v`

Expected: PASS。

- [ ] **Step 5: 提交 Hub 镜像更新**

```bash
git add skills/rdk-*/SKILL.md tests/test_plugin_contract.py
git commit -s -m "chore: sync repaired RDK device routes"
```

---

### Task 7: 统一许可证规范文本

**Files:**
- Create: `rdk-skills/tests/test_license_contract.py`
- Modify: `rdk-skills/README.md`
- Modify: `rdk-skills/README_cn.md`
- Modify: `rdk-skills/CONTRIBUTING.md`
- Modify: `rdk-skills/docs/PR-SUBMISSION.md`
- Modify: `rdk-skills/components.d/README.md`

**Interfaces:**
- Consumes: workspace ADR `docs/adr/0004-license-apache-cc-by.md`
- Produces: identical policy meaning across all public Hub governance documents

- [ ] **Step 1: 写许可证契约失败测试**

```python
POLICY_FILES = (
    "README.md", "README_cn.md", "CONTRIBUTING.md",
    "docs/PR-SUBMISSION.md", "components.d/README.md",
)

def test_policy_docs_explain_frontmatter_and_content_license(self):
    for relative in POLICY_FILES:
        text = (self.repo / relative).read_text(encoding="utf-8")
        self.assertIn("Apache-2.0", text, relative)
        self.assertIn("CC-BY-4.0", text, relative)
        self.assertIn("metadata.content-license", text, relative)
```

- [ ] **Step 2: 运行测试并确认现有文档表述不完整**

Run: `python -m unittest tests.test_license_contract -v`

Expected: 至少 `PR-SUBMISSION.md` 或 `components.d/README.md` 缺少许可范围说明而 FAIL。

- [ ] **Step 3: 按 ADR 0004 更新中英文文本**

中文标准表述：

```text
仓库按文件类型双许可：代码和脚本采用 Apache-2.0；SKILL.md、skill-card.md、
references 和其他文档内容采用 CC-BY-4.0。为兼容当前 Skill 生态并遵循 ADR 0004，
顶层 frontmatter 仍填写 license: Apache-2.0；新建或实质修改的 Skill 建议同时声明
metadata.content-license: CC-BY-4.0。该元数据不改变文件已有授权。
```

英文文档表达同一含义，不引入第三种许可证或声称重新授权。

- [ ] **Step 4: 运行许可证测试并校验文档链接**

Run: `python -m unittest tests.test_license_contract -v`

Expected: PASS。

Run: `git diff --check`

Expected: 退出码 0。

- [ ] **Step 5: 提交许可证文档修复**

```bash
git add README.md README_cn.md CONTRIBUTING.md docs/PR-SUBMISSION.md components.d/README.md tests/test_license_contract.py
git commit -s -m "docs: reconcile dual-license guidance"
```

---

### Task 8: 全量回归、生成产物一致性与交付检查

**Files:**
- Regenerate: `rdk-skills/skills/rdk-pack-installer/references/pack-registry.json`
- Regenerate: `rdk-skills/skills/rdk-skill-finder/references/skill-index.json`
- Regenerate: `rdk-skills/plugins/d-robotics-skills/**`
- Modify: `rdk-skills/CHANGELOG.md`

**Interfaces:**
- Verifies every acceptance criterion from the approved design

- [ ] **Step 1: 运行 Hub 单元测试全集**

Run: `python -m unittest discover -s tests -v`

Expected: 所有测试 PASS，0 failures，0 errors。

- [ ] **Step 2: 重新生成目录两次并验证确定性**

Run: `python .github/scripts/generate_plugin_catalog.py --repo-root .`

Run again: `python .github/scripts/generate_plugin_catalog.py --repo-root .`

Run: `git diff --check`

Expected: 第二次生成不产生额外差异，diff check 退出码 0。

- [ ] **Step 3: 重建插件并验证 JSON**

Run: `bash .github/scripts/build-plugins.sh`

Run:

```powershell
Get-ChildItem -Recurse -Filter *.json | ForEach-Object {
  Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null
}
```

Expected: 插件构建退出码 0，全部 JSON 可解析。

- [ ] **Step 4: 运行 Hub 合规校验并比较已知基线**

Run: `python .github/scripts/validate.py --mode advisory`

Expected: 新增的 `rdk-pack-installer`、`rdk-skill-finder` 和既有 `rdk-docs-reference` 均显示 `OK`；总计不超过已记录基线 L1=139、L2=367，且新增或修改的 Skill 不产生新错误。

- [ ] **Step 5: 运行源头 Pack 完整验证**

Workdir: `rdk-device-skills`

Run: `python tools/sandbox.py test`

Expected: `RESULT: PASS`。

- [ ] **Step 6: 检查两个仓库的目标差异和无关改动**

Run in each repository:

```bash
git status --short
git diff --check
git log --oneline -8
```

Expected: 只有本计划声明的文件发生变化；没有临时文件、缓存或无关用户改动。

- [ ] **Step 7: 更新 CHANGELOG 并提交最终生成差异**

在 `CHANGELOG.md` 增加本阶段条目：自包含 Pack 注册表、`rdk-skill-finder`、安装器重命名、路由修复和许可证说明统一。

```bash
git add CHANGELOG.md skills/rdk-pack-installer/references/pack-registry.json skills/rdk-skill-finder/references/skill-index.json plugins/d-robotics-skills .claude-plugin .agents/plugins .cursor-plugin .dsh-plugin
git commit -s -m "chore: finalize plugin catalog remediation"
```

- [ ] **Step 8: 最终验证提交后的干净状态**

Run: `python -m unittest discover -s tests -v`

Run: `python .github/scripts/validate.py --mode advisory`

Run in `rdk-device-skills`: `python tools/sandbox.py test`

Run in both repositories: `git status --short`

Expected: 测试全部通过；新 Hub Skill 为 `OK`；源头 Pack 显示 `RESULT: PASS`；两个工作区均无未提交改动。
