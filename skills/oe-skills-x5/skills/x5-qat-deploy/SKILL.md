---
name: x5-qat-deploy
description: 编排 X5 horizon_plugin_pytorch calibration、QAT、定点转换与 Plugin 编译；当用户有可训练 PyTorch 模型、数据和浮点基线，希望得到 March.BAYES_E 的 .hbm/.hbir 及指标闭环时使用。明确排除 HAT，且不把 QAT 自动交给 hb_mapper makertbin。
version: 1.1.1
license: Apache-2.0
---

# X5 Plugin QAT 工作流

## 目标与边界

QAT 合同固定为 `March.BAYES_E → adaptation → calibration/QAT → convert → check_model → compile_model/export_hbir`。Plugin `.hbm/.hbir` 与 OE Mapper PTQ `.bin` 是不同产物，不改后缀、不自动互转。

## 输入合同

- 可训练 PyTorch 模型和可复现构建入口。
- 训练/校准/验证数据、浮点权重、浮点指标和评价代码。
- Plugin/PyTorch/Python/GPU 环境快照、example inputs、输出目录和预算。Docker 模式需确认 `execution.docker_image.tools` 包含 `cuda`；host 模式需确认 `toolchain.cuda.available` 为 `true`。
- 目标指标、最大训练成本和检查点覆盖策略。

## 前置检查

1. 目标芯片是 X5，源码明确使用 `March.BAYES_E`；手册 quick start 中的 `March.BAYES` 示例必须替换并验证。
2. HAT package、config、Trainer、registry、Model Zoo 与 `tools/compile_perf.py` 均不得进入流程。
3. 确认目标环境能看到 CUDA。Docker 探测通过 `--gpus all` 和 `torch.cuda.is_available()` 验证设备可见性；这不等于训练脚本或收敛验证通过。
4. 先复现浮点基线；无法复现时不得用 QAT 指标宣称改善。
5. 训练环境、数据版本和随机种子可记录；输出使用新 attempt 目录。

## 执行步骤

1. `x5-qat-adaptation`：设置 march、量化边界、算子适配和 prepare。
2. `x5-qat-training`：记录 calibration、QAT 和 quantized 各阶段指标与检查点。
3. `x5-qat-compile`：`check_model` 后生成 `.hbm` 或 `.hbir`，保存编译证据。
4. 仅在实际 Runtime/模型信息证明兼容后交接 `x5-runtime-deploy`；证据不足保持 `blocked`。

## 产物与完成标准

- 浮点、calibration、QAT、quantized 指标来自同一评测合同。
- 源码检查证明 `March.BAYES_E`，且无 HAT/`hb_mapper makertbin` 混用。
- 检查点、定点模型、`check_model` 日志和 `.hbm/.hbir` 哈希完整。
- 编译成功不等于 Runtime 成功；部署兼容性和板端正确性必须单独验证。

## 风险与确认

训练、生成模型和安装用户依赖为中风险；覆盖检查点、共享环境或长时间训练前必须展示成本与恢复方式并确认。

## 失败与交接

- 精度掉点 → `x5-accuracy-diagnostics`。
- 定点/编译不一致 → `x5-consistency-diagnostics`。
- 环境问题 → `x5-environment-setup`。
- 同一训练/编译策略最多两次；第二次失败后停止自动试参。

## 按需参考

- `.drobotics-x5/platforms/x5/references/manual-map.md`
- 官方资料查询：`mcp__rdk_docs__search_docs(manual="oe-x5", source="docs", query="X5 Plugin QAT quickstart compile flow")`，再用 `mcp__rdk_docs__get_page` 读取匹配官方页面正文。
- 不使用本地 `_sources` 副本替代 MCP 证据；无法从官方正文确认具体命令/API/版本时报告阻塞。
