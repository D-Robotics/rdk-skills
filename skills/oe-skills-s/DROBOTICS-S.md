# D Robotics 工作区

## 1. 工作区概览

当前项目由 `oe-cli init` 初始化生成。

- 工作区根目录：`.drobotics-s/`
- 版本文件：`.drobotics-s/VERSION`
- Skill 索引：`.drobotics-s/skill-index.json`
- 文档目录：`.drobotics-s/docs/`
- Skill 目录：`.drobotics-s/skills/`
- 当前 release 版本：`1.1.1`

## 2. 使用规则

- 遇到 D Robotics 相关请求时，优先遵循本文件。
- 当请求属于 D Robotics 范畴，但还不能明确落到某个具体 skill 时，先使用 `.drobotics-s/skills/drobotics-router/SKILL.md` 作为顶层路由 skill。
- 业务 skill 按模块放在 `.drobotics-s/skills/<module>/<slug>/`；具体路径以 `.drobotics-s/skill-index.json` 和下方模块清单为准。
- 未经检索，不要猜测 D Robotics 工具链命令、参数或流程细节。
- 普通浮点模型部署的工作流优先评估 PTQ；ONNX 支持范围、工具参数及当前版本的适用条件，每次任务都必须通过 RDK 文档 MCP 核对。只有用户明确要求 QAT，或官方资料支持 PTQ 不适用且用户确认后，才路由到 `horizon_plugin_pytorch` 流程。
- S100/S100P/S600 产品名称用于用户文档；工具实际要求的 `nash-*` march、Python 包名和 Docker 镜像标识保持其真实名称，不要把产品名硬替换进命令或配置。
- 工作流辅助资料放在 `.drobotics-s/docs/` 下；它们不是 OE 官方手册，不作为命令、参数、API、芯片映射或版本行为的依据。

### 默认 Docker 与环境探测

- 普通 PTQ 默认使用 Docker。开始时从项目根目录运行 `python3 .drobotics-s/scripts/probe_environment.py --workflow ptq`；显式 QAT 请求运行 `--workflow qat`。若配置或用户明确选择 local，则传 `--execution-mode local`。
- Docker 默认流程先检查本机缓存镜像，并在网络隔离、只读容器中检查必要的工具可用性；不自动拉取镜像。此路径不要求 `.drobotics-s/.env.oe-package` 或 `OE_DIR`。
- 探测返回 `status=ready` 时，使用 JSON 中的 `image` 字段执行本任务；按需挂载项目输入和输出。只有任务确实要读取 OE 包内部资产，或用户明确选择 local 时，才需要 `OE_DIR`。仅为容器提供包内资产时仍保持 Docker 执行，不要因此改成本机 local。
- 探测返回 `status=blocked` 时，根据 `missing` 字段报告具体阻塞，不要假定在线镜像可用或静默改走 local。用户明确选择 local 后，使用 OE 包检测流程确认本地环境。

## 3. 执行前检查

- 开始 D Robotics 工具链任务前，先检查用户是否提供了可用板卡信息。
- 板卡平台到工具链 `march` 标识的映射，必须在每次相关任务中通过官方文档 MCP 核实；不能从旧配置、产品名或记忆推断。
- 优先从环境变量中查找板卡信息，例如 `HORIZON_BOARD_TYPE`、`OE_BOARD_TYPE`、`BOARD_TYPE`、`BOARD`、`NASH_BOARD`。
- 如果环境变量没有提供，再检查项目内相关配置文件，例如 `.env`、`.env.local`、`.drobotics-s/board.env`、`.drobotics-s/board.json`、`AGENTS.md`、`CLAUDE.md`。
- 如果任务涉及板端运行、板端推理、远端 HBM、性能压测或 BPU 实测，但没有找到板卡信息，必须先向用户确认是否有可用板卡。
- 如果用户明确没有可用板卡，涉及板端的任务应回退到 X86 评测、仿真、静态检查或可离线执行的分析工具，并说明该结果不能替代真实板端验证。

## 4. 配置与验证规则

- 修改模型相关配置后，必须使用对应工具做最小可运行验证；模型相关配置包括量化配置、编译配置、导出配置、推理配置、输入预处理配置和精度/性能评测配置。
- 验证失败时，先说明失败命令、关键报错和判断出的原因，再基于错误原因修改配置并重试。**同一方法最多重试 1 次**（总计 2 次尝试）。第 2 次仍失败则必须切换策略（换工具、查文档、检查环境）或向用户报告阻塞，禁止继续用相同方法重试。
- 不要在未验证的情况下声称配置可用；如果环境、数据或板卡缺失导致无法验证，必须明确说明缺失项和剩余风险。
- 默认量化配置及支持精度只能按当前官方 MCP 页面和已确认的目标平台选择；本地配置示例中的默认值不作为当前 OE 版本的依据。

## 5. MCP 规则

- `.drobotics-s/skill-index.json` 和各 Skill 只用于意图路由与任务流程；本地 references、examples、scripts、代码快照和摘要不能替代官方文档证据。
- 每次回答涉及 OE S 工具链行为、命令、参数、API、配置、芯片映射、流程要求或版本兼容性时，先调用 `mcp__rdk_docs__search_docs`，设置 `manual=oe-s`、`source=docs`；再用 `mcp__rdk_docs__get_page` 读取命中的官方页面。即使本地 Skill 已写有相同说法，也必须检索当前官方资料。
- 官方 MCP 结果优先于本地工作流参考。若当前版本或问题所需的资料没有被 MCP 页面证实，不得从旧文档、代码快照或记忆补全命令和结论。
- 如果 MCP 工具不可用、检索无结果或页面证据不足，明确报告阻塞和缺少的证据；不要以本地文档或模型记忆兜底，也不要声称结论已由官方资料确认。
- Docker 镜像标识与版本适用性以本次官方页面或用户明确提供的版本配置为依据；环境探测脚本只验证已选镜像符合白名单、存在于本机缓存并通过基础工具检查，不替代官方兼容性证据。默认 Docker 探测不要求实际 OE 包或 `OE_DIR`，也不得按产品名称推测镜像标识。

## 6. 内置 Skills

- `drobotics-router@1.1.1` -> `.drobotics-s/skills/drobotics-router/SKILL.md`: D Robotics 顶层路由 skill，用于在具体 skill 之间做渐进式任务分流。

### OE 包环境

- `oe-package-detection@1.1.1` -> `.drobotics-s/skills/drobotics-router/oe-package-detection/SKILL.md`
- `oe-package-install@1.1.1` -> `.drobotics-s/skills/drobotics-router/oe-package-install/SKILL.md`
- `board-detection@1.1.1` -> `.drobotics-s/skills/drobotics-router/board-detection/SKILL.md`

### OE-LLM 包环境

- `oe-llm-package-detection@1.1.1` -> `.drobotics-s/skills/drobotics-router/oe-llm-package-detection/SKILL.md`
- `oe-llm-package-install@1.1.1` -> `.drobotics-s/skills/drobotics-router/oe-llm-package-install/SKILL.md`

### HBDK (hbdk)

- `s-hbdk-compile@1.1.1` -> `.drobotics-s/skills/hbdk/s-hbdk-compile/SKILL.md`
- `hbdk-manual@1.1.1` -> `.drobotics-s/skills/hbdk/hbdk-manual/SKILL.md`

### D Robotics Plugin (plugin)

- `s-plugin-adaptation@1.1.1` -> `.drobotics-s/skills/plugin/s-plugin-adaptation/SKILL.md`
- `s-plugin-export@1.1.1` -> `.drobotics-s/skills/plugin/s-plugin-export/SKILL.md`
- `s-plugin-model-check-result@1.1.1` -> `.drobotics-s/skills/plugin/s-plugin-model-check-result/SKILL.md`
- `s-plugin-graph-diff@1.1.1` -> `.drobotics-s/skills/plugin/s-plugin-graph-diff/SKILL.md`
- `s-plugin-hbdk-generating@1.1.1` -> `.drobotics-s/skills/plugin/s-plugin-hbdk-generating/SKILL.md`
- `s-plugin-consistency-debug@1.1.1` -> `.drobotics-s/skills/plugin/s-plugin-consistency-debug/SKILL.md`
- `s-plugin-precision-tuning@1.1.1` -> `.drobotics-s/skills/plugin/s-plugin-precision-tuning/SKILL.md`

### HMCT / Quantization (hmct)

- `hmct-workflow@1.1.1` -> `.drobotics-s/skills/hmct/SKILL.md`

### UCP / Runtime (ucp)

- `s-ucp-infer-generating@1.1.1` -> `.drobotics-s/skills/ucp/s-ucp-infer-generating/SKILL.md`
- `s-ucp-hbm-infer@1.1.1` -> `.drobotics-s/skills/ucp/s-ucp-hbm-infer/SKILL.md`
- `s-ucp-model-perf-eval@1.1.1` -> `.drobotics-s/skills/ucp/s-ucp-model-perf-eval/SKILL.md`
- `s-ucp-perfetto-trace-analysis@1.1.1` -> `.drobotics-s/skills/ucp/s-ucp-perfetto-trace-analysis/SKILL.md`
- `s-ucp-perfetto-trace-catcher@1.1.1` -> `.drobotics-s/skills/ucp/s-ucp-perfetto-trace-catcher/SKILL.md`
- `s-board-monitor@1.1.1` -> `.drobotics-s/skills/ucp/s-board-monitor/SKILL.md`

### D Robotics TC UI / Analyzer (tc_ui)

- `hb-analyzer-performance@1.1.1` -> `.drobotics-s/skills/tc_ui/hb-analyzer-performance/SKILL.md`
- `s-tc-ui@1.1.1` -> `.drobotics-s/skills/tc_ui/s-tc-ui/SKILL.md`
