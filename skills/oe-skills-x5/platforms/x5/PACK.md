# D-Robotics X5 平台 Pack

## 范围

- **完成**：围绕 X5 建立可复现的环境探测、ONNX/Caffe PTQ、`horizon_plugin_pytorch` QAT、Runtime C/C++、板端 Python 推理、精度与性能诊断闭环。
- **PTQ 主路径**：`hb_mapper checker` → X5 YAML → `hb_mapper makertbin` → `bayes-e` `.bin` → Runtime/板端验证。
- **QAT 主路径**：`March.BAYES_E` → calibration/QAT/convert → `check_model` → Plugin `compile_model`/`export_hbir`。QAT 产物与 PTQ `.bin` 是不同合同，禁止未经手册和实际环境验证就互相转换或替代。
- **不处理**：HAT（Horizon Torch Samples）框架、HAT config、HAT Trainer、HAT Model Zoo、`tools/compile_perf.py`；S100/S100P/S600 的 `nash-*`、HBDK4、HMCT、UCP；X3 或其他 X 芯片。
- **入口**：`x5-router`。端到端请求只选择一个主 Workflow，并通过显式 handoff 串联原子 Skill。

## 兼容性与资料

- **Pack 版本**：`2.0.0`。
- **工具链基线**：X5 `OE Mapper v1.2.8 / Python 3.10` 与匹配的 Runtime SDK。
- **PTQ march**：CLI/YAML 必须是 `bayes-e`。
- **QAT march**：Python API 必须是 `March.BAYES_E`。`March.BAYES` 对应 J5，不得用于 X5。
- **本地手册**：`OE_DROBOTICS_DOC_ROOT` → `OE_X_SERIES_DOC_ROOT` → Pack/工作区相对发现。禁止把维护者机器的绝对路径作为发布后的唯一默认值。
- **固定发布物**：SDK、文档、Docker 镜像和离线制品以 [离线制品交付指南](../../../docs/offline-artifact-delivery.md) 为准。下载、镜像导入和在线拉取前必须取得明确确认。
- **详细兼容矩阵**：执行前读取 [compatibility.md](policies/compatibility.md)。

## 输入资产与前置

| 阶段 | 必需输入 | 前置检查 | 缺失时处理 |
| --- | --- | --- | --- |
| 环境探测 | 发布包/容器位置、Python、目标工作流 | 真实命令、包版本、文档根 | 输出 `degraded` 或 `blocked`，不安装 |
| 环境安装 | 已审阅安装计划、制品来源、目标环境 | 环境快照、风险与回滚 | 未确认时只输出计划 |
| PTQ | ONNX 或 Caffe + `.prototxt`、输入合同、校准数据或 `skip`、输出目录 | `hb_mapper checker`、`march=bayes-e` | 停在预检，不生成猜测配置 |
| QAT | 可训练模型、训练/验证数据、浮点基线、Plugin/PyTorch 版本 | `March.BAYES_E`、可复现训练环境 | 不满足时保持 `blocked` |
| Runtime C/C++ | 已验证的目标 Runtime 模型、I/O 合同、开发板/SDK 信息 | 模型格式与 Runtime 兼容性、板端可达性 | 不上传、不覆盖板端文件 |
| Runtime Python | X5 `.bin`、`/etc/version >= 3.5.0`、匹配 wheel/DEB | Python ABI、包来源、`libdnn` | 不混装 S 系列包 |
| 诊断 | 环境快照、失败收据、模型/配置、完整日志、可复现输入 | 证据完整性与失败阶段 | 只读分析并列出最小补充项 |

## 全局完成标准

- 实际执行使用 `<working_dir>/.drobotics/x5-runs/<run-id>/` 或用户认可的运行目录。
- 每次运行至少产生 `input.json`、`environment.json`、`route.json`、`plan.json`、`run-state.json`、`events.ndjson`、`artifacts.json`、`verification.json` 和 `receipt.json`。
- PTQ 成功必须有 checker 证据、通过 schema 校验的 YAML、`.bin`、`hb_model_info` 中的 `BPU march: bayes-e` 和后续 Runtime 验证结论。
- QAT 成功必须有浮点/calibration/QAT/quantized 指标、`March.BAYES_E` 证据、模型检查和编译产物；不得把 Generic/J5 示例中的 `March.BAYES` 当成 X5 成功路径。
- Runtime 成功必须有可复现输入、模型 I/O、板端回读、输出正确性结论和必要的性能结果。
- 命令返回码、文件存在或手册检索命中均不能单独构成完成。

## 全局风险策略

- **low**：只读探测、手册检索、模型信息和日志分析、生成新报告。
- **medium**：创建配置、生成模型、长时间训练、安装用户级依赖、上传到新板端目录。
- **high**：覆盖模型/检查点、修改共享环境、替换 Runtime、停止业务进程、清理已有板端目录。
- **critical**：烧录、分区、量产发布和不可逆设备操作；当前 Pack 不执行。
- 详细规则见 [risk-policy.md](policies/risk-policy.md)。

## 状态与恢复

1. 状态机：`created → preflight → planned → awaiting_approval? → running → verifying → succeeded | failed | blocked | cancelled`。
2. 使用 `scripts/run_contract.py` 初始化和更新运行记录；已验证产物默认不可覆盖。
3. 同一策略最多尝试两次。第二次失败后保存日志和中间产物，交接专项 Diagnose Skill。
4. Diagnose Skill 默认只读；没有新计划和确认时不得自动重跑编译、训练、上传或环境修改。

## Skill 架构

### Router

- `x5-router`：唯一 Pack 入口；选择一个主 Workflow，记录候选、拒绝理由和有序 handoff。

### Environment

- `x5-environment-setup`：兼容入口与环境流程编排。
- `x5-environment-probe`：只读生成环境事实和 `ready/degraded/blocked` 结论。
- `x5-environment-install`：经确认后安装或配置 X5 工具链环境。

### PTQ

- `x5-ptq-deploy`：端到端 PTQ Workflow。
- `x5-model-preflight`：模型格式、输入合同和 checker 预检。
- `x5-calibration-data-prepare`：校准数据合同、预处理和样本审计。
- `x5-ptq-config-authoring`：生成并验证 X5 YAML。
- `x5-ptq-compile`：执行 checker/makertbin、收集并验证 `.bin` 产物。

### QAT

- `x5-qat-deploy`：Plugin QAT Workflow；明确排除 HAT。
- `x5-qat-adaptation`：设置 `March.BAYES_E`、模型边界、prepare 和 fake-quant 状态。
- `x5-qat-training`：calibration、QAT 训练、quantized 指标和检查点合同。
- `x5-qat-compile`：Plugin `check_model`、`compile_model`/`export_hbir` 与编译证据。

### Runtime

- `x5-runtime-deploy`：Runtime 总工作流。
- `x5-runtime-cpp-infer`：生成/审查 BPU SDK C/C++ 推理代码。
- `x5-runtime-perf-eval`：`hrt_model_exec`/`ai_benchmark` 性能评测。
- `x5-board-monitor`：`hrut_somstatus`、内核日志和资源快照。
- `x5-bpu-python-api`：板端 `hbm_runtime.HB_HBMRuntime` Python API。

### Diagnose

- `x5-model-diagnostics`：诊断路由与证据治理。
- `x5-accuracy-diagnostics`：校准、量化、仿真和板端精度问题。
- `x5-consistency-diagnostics`：浮点/quantized/编译/Runtime 分段一致性。
- `x5-performance-diagnostics`：静态性能、板端性能和资源瓶颈分析。

## Pack 资产

- `skill-index.json`：X5 V2 唯一合同；全局索引是兼容聚合视图。
- `schemas/`：8 个 JSON Schema，覆盖环境、路由、计划、运行状态、产物、验证、收据和 PTQ 配置。
- `references/`：运行合同、手册映射与能力边界。
- `scripts/`：7 个可执行脚本，覆盖状态收据、环境探测、PTQ 配置与执行、QAT 目标检查和板端状态解析。
- `assets/`：ONNX/Caffe PTQ YAML 模板和单输入 raw tensor 的 Runtime C++ 工程模板。
- `evals/cases.yaml`：22 个 Skill 的路由、成功、预检失败、风险确认，以及 HAT/J5/S/X3 隔离用例。

## 验收

~~~bash
python .drobotics/scripts/validate_x5_skills.py
python .drobotics/scripts/validate_bpu_python_api_skills.py
python .drobotics/scripts/validate_release_artifacts.py
~~~

验证器会执行假工具链 PTQ、QAT 目标检查、运行合同和板端状态解析 smoke；这仍不等于真实工具链/开发板通过。发布前还必须在匹配的 X5 SDK 中运行 PTQ smoke，并在可用开发板上运行带标签的 Runtime smoke。
