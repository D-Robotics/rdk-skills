# D Robotics 工作区

## 1. 工作区概览

当前项目由 `oe-cli init` 初始化生成。

- 工作区根目录：`.drobotics-s/`
- 版本文件：`.drobotics-s/VERSION`
- Skill 索引：`.drobotics-s/skill-index.json`
- 文档目录：`.drobotics-s/docs/`
- Skill 目录：`.drobotics-s/skills/`
- 当前 release 版本：`1.1.0`

## 2. 使用规则

- 遇到 D Robotics 相关请求时，优先遵循本文件。
- 当请求属于 D Robotics 范畴，但还不能明确落到某个具体 skill 时，先使用 `.drobotics-s/skills/drobotics-router/SKILL.md` 作为顶层路由 skill。
- 业务 skill 按模块放在 `.drobotics-s/skills/<module>/<slug>/`；具体路径以 `.drobotics-s/skill-index.json` 和下方模块清单为准。
- 未经检索，不要猜测 D Robotics 工具链命令、参数或流程细节。
- 普通浮点模型部署优先尝试 PTQ：Caffe 可直接走 PTQ；PyTorch 等框架先导出满足当前 OE 版本要求的 ONNX。只有用户明确要求 QAT，或 PTQ 经支持性检查与精度调优仍无法满足目标并获用户确认后，才走 `horizon_plugin_pytorch` 流程。依据见 `.drobotics-s/skills/drobotics-router/references/oe-s-official-docs.md`。
- S100/S100P/S600 产品名称用于用户文档；工具实际要求的 `nash-*` march、Python 包名和 Docker 镜像标识保持其真实名称，不要把产品名硬替换进命令或配置。
- 本地文档统一放在 `.drobotics-s/docs/` 下，文档目录名固定不带版本号。

## 3. 执行前检查

- 开始 D Robotics 工具链任务前，先检查用户是否提供了可用板卡信息。
- 板卡类型按工具链 march 标识处理：`nash-e/m`、`nash-p`、`nash-b`。`nash-e/m/p` 对应 RDK S100/S100P/S600；`nash-b` 为 QNX 平台标识，不据此推断旭日芯片型号。
- 优先从环境变量中查找板卡信息，例如 `HORIZON_BOARD_TYPE`、`OE_BOARD_TYPE`、`BOARD_TYPE`、`BOARD`、`NASH_BOARD`。
- 如果环境变量没有提供，再检查项目内相关配置文件，例如 `.env`、`.env.local`、`.drobotics-s/board.env`、`.drobotics-s/board.json`、`AGENTS.md`、`CLAUDE.md`。
- 如果任务涉及板端运行、板端推理、远端 HBM、性能压测或 BPU 实测，但没有找到板卡信息，必须先向用户确认是否有可用板卡。
- 如果用户明确没有可用板卡，涉及板端的任务应回退到 X86 评测、仿真、静态检查或可离线执行的分析工具，并说明该结果不能替代真实板端验证。

## 4. 配置与验证规则

- 修改模型相关配置后，必须使用对应工具做最小可运行验证；模型相关配置包括量化配置、编译配置、导出配置、推理配置、输入预处理配置和精度/性能评测配置。
- 验证失败时，先说明失败命令、关键报错和判断出的原因，再基于错误原因修改配置并重试。**同一方法最多重试 1 次**（总计 2 次尝试）。第 2 次仍失败则必须切换策略（换工具、查文档、检查环境）或向用户报告阻塞，禁止继续用相同方法重试。
- 不要在未验证的情况下声称配置可用；如果环境、数据或板卡缺失导致无法验证，必须明确说明缺失项和剩余风险。
- 默认量化配置按目标平台选择：`nash-p` / RDK S600 使用 `fp16+int8`，`nash-e/m` / RDK S100/S100P 使用 `int8`。`nash-b` 的产品型号映射未在本 Skill 中定义，先确认目标平台配置。

## 5. MCP 规则

- 处理 D Robotics 相关请求时，先根据 `.drobotics-s/skill-index.json` 和下方模块清单找到对应 skill。
- 进入对应 skill 后，优先阅读该 skill 的 `SKILL.md`、本地 references、examples 或 scripts。
- 只要模型相关参数、函数、API、配置项、命令参数、流程顺序或默认行为存在不确定性，必须使用 `oe-mcp` 检索对应文档，直到弄懂后再继续。
- 如果查询对应 skill 后仍有不理解的问题，或者需要进一步确认官方流程、参数说明、API 行为、版本差异或报错含义，必须使用 `oe-mcp` 做文档检索。
- `oe-mcp` 用于补充和确认，不替代当前 release 包内的 skill 路由；最终回答应尽量基于已查看的 skill 内容、MCP 文档或代码证据。
- 当本地 skill 与 `oe-mcp` 检索结果不一致时，先说明差异，再给出保守建议。
- 优先按 D-Robotics 官方建议在 Docker 中运行 OE。镜像标签必须与 `OE_VERSION` 匹配；旧 `j6` 镜像只用于识别已有环境，不作为新环境默认值。

## 6. 内置 Skills

- `drobotics-router@1.1.0` -> `.drobotics-s/skills/drobotics-router/SKILL.md`: D Robotics 顶层路由 skill，用于在具体 skill 之间做渐进式任务分流。

### OE 包环境

- `oe-package-detection@1.1.0` -> `.drobotics-s/skills/drobotics-router/oe-package-detection/SKILL.md`
- `oe-package-install@1.1.0` -> `.drobotics-s/skills/drobotics-router/oe-package-install/SKILL.md`
- `board-detection@1.1.0` -> `.drobotics-s/skills/drobotics-router/board-detection/SKILL.md`

### OE-LLM 包环境

- `oe-llm-package-detection@1.1.0` -> `.drobotics-s/skills/drobotics-router/oe-llm-package-detection/SKILL.md`
- `oe-llm-package-install@1.1.0` -> `.drobotics-s/skills/drobotics-router/oe-llm-package-install/SKILL.md`

### HBDK (hbdk)

- `s-hbdk-compile@1.1.0` -> `.drobotics-s/skills/hbdk/s-hbdk-compile/SKILL.md`
- `hbdk-manual@1.1.0` -> `.drobotics-s/skills/hbdk/hbdk-manual/SKILL.md`

### D Robotics Plugin (plugin)

- `s-plugin-adaptation@1.1.0` -> `.drobotics-s/skills/plugin/s-plugin-adaptation/SKILL.md`
- `s-plugin-export@1.1.0` -> `.drobotics-s/skills/plugin/s-plugin-export/SKILL.md`
- `s-plugin-model-check-result@1.1.0` -> `.drobotics-s/skills/plugin/s-plugin-model-check-result/SKILL.md`
- `s-plugin-graph-diff@1.1.0` -> `.drobotics-s/skills/plugin/s-plugin-graph-diff/SKILL.md`
- `s-plugin-hbdk-generating@1.1.0` -> `.drobotics-s/skills/plugin/s-plugin-hbdk-generating/SKILL.md`
- `s-plugin-consistency-debug@1.1.0` -> `.drobotics-s/skills/plugin/s-plugin-consistency-debug/SKILL.md`
- `s-plugin-precision-tuning@1.1.0` -> `.drobotics-s/skills/plugin/s-plugin-precision-tuning/SKILL.md`

### HMCT / Quantization (hmct)

- `hmct-workflow@1.1.0` -> `.drobotics-s/skills/hmct/SKILL.md`

### UCP / Runtime (ucp)

- `s-ucp-infer-generating@1.1.0` -> `.drobotics-s/skills/ucp/s-ucp-infer-generating/SKILL.md`
- `s-ucp-hbm-infer@1.1.0` -> `.drobotics-s/skills/ucp/s-ucp-hbm-infer/SKILL.md`
- `s-ucp-model-perf-eval@1.1.0` -> `.drobotics-s/skills/ucp/s-ucp-model-perf-eval/SKILL.md`
- `s-ucp-perfetto-trace-analysis@1.1.0` -> `.drobotics-s/skills/ucp/s-ucp-perfetto-trace-analysis/SKILL.md`
- `s-ucp-perfetto-trace-catcher@1.1.0` -> `.drobotics-s/skills/ucp/s-ucp-perfetto-trace-catcher/SKILL.md`
- `s-board-monitor@1.1.0` -> `.drobotics-s/skills/ucp/s-board-monitor/SKILL.md`

### D Robotics TC UI / Analyzer (tc_ui)

- `hb-analyzer-performance@1.1.0` -> `.drobotics-s/skills/tc_ui/hb-analyzer-performance/SKILL.md`
- `s-tc-ui@1.1.0` -> `.drobotics-s/skills/tc_ui/s-tc-ui/SKILL.md`
