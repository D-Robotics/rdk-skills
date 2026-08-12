---
name: x5-model-preflight
description: 对 X5 PTQ 的 ONNX/Caffe 模型执行格式、输入合同、浮点参考运行和 hb_mapper checker 预检；当尚未生成正式 YAML、需要判断模型能否进入 bayes-e PTQ 时使用。只做预检，不生成部署成功结论。
---

# X5 模型预检

## 目标与边界

在校准和编译前发现模型格式、动态 shape、输入顺序、预处理和算子支持问题。checker 是快速支持性检查，不等于最终 YAML 配置下的 makertbin 结果。

## 输入合同

- ONNX，或 Caffe model + prototxt。
- 所有输入名称和静态 shape；动态维必须给出实际部署 shape。
- 可运行的浮点参考输入/输出或评测入口。
- PTQ `environment.json` 与新预检输出目录。

## 前置检查

- 文件后缀、模型配对和哈希可读。
- 输入不是 Plugin QAT 或 Runtime 产物。
- 对多输入模型，名称与 shape 顺序必须显式记录。

## 执行步骤

1. 用原框架/ONNX Runtime 执行一份固定输入，保存输入哈希、输出 shape/dtype 和摘要。
2. 生成 `calibration_type: skip` 的预检 YAML；它只用于驱动统一 checker 脚本，不作为正式精度配置。
3. 执行：

~~~bash
python .drobotics/platforms/x5/scripts/run_ptq.py checker \
  --config <preflight.yaml> \
  --output-dir <run-root>/checker \
  --report <run-root>/checker-report.json
~~~

4. 审阅 CPU/BPU 节点分配、unsupported/unknown 算子、输入改写和 checker 日志。

## 产物与完成标准

- 浮点参考证据、模型哈希、I/O 合同、checker 日志和结构化报告。
- checker 返回成功且没有未解释的模型输入/输出变化。
- 预检配置与正式 YAML 的差异被记录；后续仍需在最终配置下重新验证。

## 风险与确认

只读模型与生成新报告为低风险。不得覆盖模型或把 checker 临时输出混入正式工作目录。

## 失败与交接

保存首次失败节点、日志和最小复现，交接 `x5-model-diagnostics`。不要在同一次预检中同时改 shape、节点和预处理。

## 按需参考

- `_sources/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_checker.rst.txt`
