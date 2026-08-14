---
name: x5-ptq-compile
description: 执行已验证 X5 YAML 的 hb_mapper checker/makertbin 并验证唯一 .bin 与 BPU march；当配置和环境已就绪、需要生成 bayes-e PTQ 产物时使用。不得处理 QAT .hbm/.hbir，也不得复用非空输出目录而未确认。
---

# X5 PTQ 编译

## 目标与边界

执行确定的 PTQ 配置并收集证据，不在编译过程中自动改 YAML、校准数据或目标 march。

## 输入合同

- 通过 `validate_ptq_config.py --check-paths` 的 YAML 和报告。
- PTQ `environment.json`、新 working/checker 目录和磁盘预算。
- 如需复用非空目录，必须有审批和原始产物备份。

## 前置检查

1. 重新验证 YAML 哈希和 `march: bayes-e`。
2. 确认 model/calibration 输入与报告一致。
3. 检查输出目录为空；不把旧 `.bin` 当成本次产物。

## 执行步骤

~~~bash
python .drobotics/platforms/x5/scripts/run_ptq.py full \
  --config <x5.yaml> \
  --report <run-root>/ptq-report.json
~~~

脚本依次运行 checker、`hb_mapper makertbin` 和 `hb_model_info`。只有审阅并确认非空目录后才允许追加 `--allow-nonempty-working-dir`。

## 产物与完成标准

- checker 与 makertbin 返回成功，日志完整。
- working_dir 中恰有一个本次 `.bin`；产物哈希已记录。
- `hb_model_info` 解析到 `BPU march: bayes-e`。
- 量化 ONNX、静态性能文件和 warning 被登记；Runtime 正确性仍需后续验证。

## 风险与确认

模型生成和长时间编译为中风险；覆盖/复用输出为高风险。不得把文件重命名为 `.bin` 绕过验证。

## 失败与交接

- 编译/算子问题 → `x5-model-diagnostics`。
- 编译后精度问题 → `x5-accuracy-diagnostics`。
- 静态性能问题 → `x5-performance-diagnostics`。
- 同一 YAML 最多两次；第二次失败不自动切换 fast-perf 或 O3。

## 按需参考

- `_sources/oe_mapper/source/ptq/ptq_usage/quantize_compile.rst.txt`
- `_sources/oe_mapper/source/ptq/ptq_tool/hb_model_info.rst.txt`
