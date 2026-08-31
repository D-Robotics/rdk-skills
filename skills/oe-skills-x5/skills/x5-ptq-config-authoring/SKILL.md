---
name: x5-ptq-config-authoring
description: 生成并机器校验 X5 OE Mapper PTQ YAML；当模型预检通过、输入和校准合同已明确，需要得到 march=bayes-e 的可审阅配置时使用。拒绝 Plugin load/QAT 混用、HAT 和 S 系列字段。
version: 1.0.0
license: Apache-2.0
---

# X5 PTQ 配置编写

## 目标与边界

从已验证输入合同生成最小 YAML，再按手册需要增加高级参数。当前 PTQ 合同不支持 `calibration_type: load` 的 Plugin 串接；QAT 使用独立 Skill。

## 输入合同

- 模型、input contract、校准目录或明确 `skip`。
- 输出前缀、全新 `working_dir`、编译模式、core 和 input source。
- 已通过的模型预检证据。

## 前置检查

- `march` 固定为 `bayes-e`，不是 `March.BAYES_E`、`bayes` 或 `nash-*`。
- ONNX 与 Caffe+prototxt 二选一。
- 多输入字段使用同一顺序和相同数量；配置中的路径可从 YAML 所在目录解析。

## 执行步骤

~~~bash
python .drobotics/platforms/x5/scripts/generate_ptq_config.py \
  --model <model.onnx> --output <x5.yaml> --working-dir <new-output-dir> \
  --input-name <name> --input-shape <1x3xHxW> \
  --input-type-train rgb --input-layout-train NCHW \
  --input-type-rt nv12 --cal-data-dir <calib-dir> \
  --input-source <name>=pyramid --check-paths

python .drobotics/platforms/x5/scripts/validate_ptq_config.py \
  <x5.yaml> --check-paths --report <config-report.json>
~~~

以 `assets/ptq/` 模板审阅参数组，但不要直接使用占位路径。高级字段必须能追溯到本地手册。

## 产物与完成标准

- YAML 包含四个必需参数组，通过 JSON Schema 与语义校验。
- `config-report.json` 无 error；所有 warning 已解释。
- 输入顺序、校准责任、输出目录和覆盖策略可由他人复现。

## 风险与确认

生成新配置为中风险；`--overwrite` 只在用户审阅旧文件、差异和恢复方式后使用。

## 失败与交接

验证失败时只修一个合同问题并重跑。两次仍失败，保留报告并交接 `x5-model-diagnostics`。

## 按需参考

- `.drobotics/platforms/x5/schemas/ptq-config.schema.json`
- `_sources/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_makertbin.rst.txt`
