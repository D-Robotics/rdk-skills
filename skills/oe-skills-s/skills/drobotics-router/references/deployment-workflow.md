# 量化部署全流程与全链路部署规范

> 本文档从 drobotics-router SKILL.md 拆出，按需加载。当用户需求涉及量化、编译、部署完整链路时阅读本文件。
>
> **使用边界**：本文档是项目工作流与交付检查清单，不是 OE 官方手册。文中校准选项、精度类型、`march`、CLI、API、配置字段等技术事实和版本默认值，都必须在执行前通过 RDK 文档 MCP 核对；MCP 官方页面优先于本文档及任何子 Skill。若 MCP 不可用或资料不足，报告阻塞，不以本文档兜底。

## PTQ 链路

普通浮点模型部署默认先评估 PTQ。Caffe 可直接进入 PTQ；ONNX 按当前 OE 版本要求检查后进入 PTQ。PyTorch、TensorFlow 等模型可先导出 ONNX，再按 PTQ 流程处理。官方手册当前列出的 ONNX 范围为 opset 10–19、ir_version ≤ 9，实际执行仍需核对已安装 OE 版本。

```
浮点模型校验 → 校准数据准备 → 量化（含精度调优） → 编译 → [数学等价性能优化] → HBM 精度验证 → UCP 部署代码生成
```

## QAT 链路

用户明确要求 QAT、插件适配或 `horizon_plugin_pytorch` API 时走此链路。若 PTQ 经支持性检查和精度调优仍达不到目标，可向用户说明差距并确认是否转 QAT。

- "量化适配"在 D Robotics 工具链中特指 QAT 适配（horizon_plugin_pytorch），不等同于 PTQ
- `.pt` / `.pth` 后缀本身不是选择 QAT 的依据。若项目中有模型定义、权重和导出所需输入信息，先评估导出 ONNX 并使用 PTQ。
- 用户明确选择 QAT 时遵循该选择；普通部署中不得因模型复杂、GPU 情况或单次转换错误直接改为 QAT。
- 若 PTQ 暂不可行，先核对 ONNX 导出条件、算子约束、预处理和校准集；缺少必要信息时询问用户。只有在说明 PTQ 失败或不适用的证据后，才提出 QAT 作为下一方案。

```
浮点模型校验 → QAT 适配 → 导出 HBIR/BC → 编译 → [数学等价性能优化] → HBM 精度验证 → UCP 部署代码生成
```

## 全链路部署规范

当用户需求覆盖「量化 → 编译 → 部署」完整链路时，以下规则**必须逐条执行**，不可跳过：

### 1. "部署"必须生成 UCP 推理代码
- `hbm_perf` / `hbm_infer` 仅用于**性能验证**和**精度对比**，不等同于部署
- 部署的交付物是 `s-ucp-infer-generating` 生成的 C++ 推理代码（或 `s-ucp-hbm-infer` 的 Python SDK 代码）
- 必须在开发板上通过 UCP 代码运行推理，验证输出与浮点模型一致
- **⛔ 禁止将 `hbm_infer` / `hbrt4-run-model` / 自定义 shell 脚本作为"部署完成"的标志**——这些仅可作为部署前的快速验证手段，最终交付物必须是 UCP 推理代码

**UCP 部署闭环验证检查表（必须全部完成才算"部署完成"）**：

```
□ 1. UCP 推理代码已生成（C++ 或 Python SDK）
□ 2. 推理代码已在开发板上编译成功（C++ 交叉编译 + scp 上传）
□ 3. 推理代码已在开发板上运行，并输出了推理结果
□ 4. 推理结果与浮点模型输出对比，精度在可接受范围内
□ 5. 板端推理延时已实测并记录
```

**⛔ 以下情况不算"部署完成"**：
- 仅生成了代码但未在板端编译运行
- 仅用 `hrt_model_exec perf` 测试了性能但未运行推理验证输出正确性
- 仅用 `hbm_infer` Python SDK 做了精度对比但未生成 UCP 推理代码
- Agent 自己声称代码正确但未经板端实测

### 2. PTQ 校准方法和量化精度默认值
- `calibration_type` 必须设为 `"histogram"`（直方图），不要用 `"max"`
- `"max"` 仅用于快速验证，生产部署必须用 `"histogram"`
- 量化配置中 `all_node_type` 的选取需根据用户要求和目标平台：
  - **nash-p / nash-h**：用户未指定时默认 `float16`，conv 类单独设 `int8`
  - **nash-e / nash-m / nash-b**：用户未指定时默认 `int8`
- **⛔ 禁止在用户未要求的情况下使用 `all_node_type: int8` 对 nash-p/nash-h 平台做全局 INT8 量化**——这会浪费 nash-p 的 fp16 能力

### 3. 编译配置：删除反量化节点
- `remove_node_type` 必须同时包含 `["Quantize", "Dequantize"]`，仅删 Quantize 会遗留 Dequantize 算子，导致板端推理输出仍为量化值而非 float32
- pyramid 输入格式需在 `input_sources` 中配置 `source_type: pyramid`，并设置 `mean_value` / `scale_value`

### 4. 预处理配置必须从用户代码提取
- 阅读用户提供的预处理代码（如 `get_data_loaders()`），提取 `mean_value`、`scale_value`、`input_type_rt` 等参数
- 在编译 YAML 的 `input_sources` 中配置板端预处理节点（NV12 → RGB、mean/scale 归一化），不要跳过此步骤选择 DDR 模式

### 5. QAT 链路必须检查所选环境
- 先运行 `python3 .drobotics-s/scripts/probe_environment.py --workflow qat`，只使用结果中已验证的 `image`。GPU 镜像必须有 `qat_cuda.ok=true` 才能按 GPU 路径运行；已验证的 CPU 镜像也可用于 CPU QAT，但训练可能较慢。
- GPU 探测失败时检查宿主机驱动、Docker GPU 支持及容器内 CUDA 可见性；不得把 CPU 镜像没有 CUDA 误判为故障。运行时只挂载本次需要的数据与工作目录；仅在确实读取 OE 包内部资产时才挂载 `OE_DIR`。
- 镜像、依赖及 QAT 命令仍需用当前官方文档 MCP 页面核对。环境阻塞时报告探测结果，不可静默跳过校准、导出或编译步骤。

### 6. 部署后可选：板端资源验证
- 当用户提到目标帧率、实车设计帧率、资源预算等关键词时，部署完成后应使用 `s-board-monitor` 验证模型在目标帧率下的 BPU/DDR/内存消耗
- 这不是强制步骤，但在实车场景中很常见——确认模型不仅功能正确，且资源消耗在可接受范围内
- 路由到 `s-board-monitor` skill（Scenario A：受控推理 + 同步监控）

### 7. 部署报告必须包含延时与精度对比
- 任何端到端部署任务的**最终报告**都必须包含以下字段，缺一不可：
  - **板端推理延时**（ms）：使用 `hbm_perf(remote_ip=...)` 或 `s-ucp-model-perf-eval` 实测
  - **精度对比**：HBM 推理输出与浮点模型输出的 cosine similarity / Top-K 匹配率
  - **CPU 算子检查结果**：编译后是否存在 CPU fallback 算子
- 仅输出精度对比而缺少延时数据，或仅输出延时而缺少精度对比，均视为报告不完整
- 延时数据应标注测量方式（hbm_perf 静态分析 vs 板端实测）

### 8. QAT 链路：`.bc` 为必检中间产物
- QAT 链路（PyTorch 代码 → horizon_plugin_pytorch）的产物链为：`.pt/.pth` → `.bc` → `.hbm`
- `.bc` 文件是 QAT 适配完成的唯一标志物，必须在 outputs 中交付
- 如果 `.bc` 未生成，说明 QAT 适配流程未完成，不应跳过直接进入 HMCT PTQ 路径
- Agent 应在报告中明确记录 `.bc` 的生成状态

### 9. 延时不达标的降级策略
- 当板端实测延时超过用户目标时，按以下顺序尝试优化：
  1. **检查编译配置**：确认 `debug: false`、`opt_level: 2`、`core_num` 合理
  2. **检查 CPU 算子**：CPU fallback 算子是常见延时瓶颈，列出具体算子名
  3. **后处理迁移 C++**：将 Python 后处理逻辑（NMS、decode、sigmoid 等）改为 C++ 实现，路由到 `s-ucp-infer-generating`
  4. **混合精度调整**：对延时敏感的层使用 int8，精度敏感的层使用 int16/fp16
- 在报告中明确说明延时是否达标，若不达标需列出已尝试的优化措施和当前瓶颈

### 10. QAT 链路：关闭伪量化精度验证（_float 验证）
- QAT 适配完成后、导出 `.bc` 之前，应验证**关闭伪量化**（`_float` 模式）下的推理精度与原始浮点模型对齐
- 方法：在 `set_fake_quantize(model, FakeQuantState.VALIDATION)` 后，额外运行一次不带伪量化的推理，对比输出
- 如果 `_float` 精度与浮点差异过大（cosine < 0.999），说明 QAT 适配本身引入了精度损失，应先修复适配问题再进入编译流程
- 这是 QAT 链路中"量化适配完成"的验证门槛，不通过则不应继续后续步骤
