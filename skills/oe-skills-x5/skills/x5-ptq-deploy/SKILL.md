---
name: x5-ptq-deploy
description: 编排 ONNX/Caffe 到 X5 bayes-e .bin 的 OE Mapper PTQ 全流程；当用户要求 checker、校准、YAML、makertbin、模型信息和 Runtime 验证形成闭环时使用。通过原子 Skills 执行，不接受 Plugin QAT .hbm/.hbir、HAT 或 S 系列流程。
version: 1.0.0
license: Apache-2.0
---

# X5 PTQ 部署工作流

## 目标与边界

主路径固定为 `checker → 校准数据 → 配置 → makertbin → hb_model_info → Runtime 正确性`。编译返回 0 不是完成；QAT 产物不得改后缀或自动交给本流程。

## 输入合同

- ONNX，或 Caffe `.caffemodel + .prototxt`。
- 每个输入的名称、shape、训练 dtype/layout、Runtime dtype/layout、预处理责任。
- 校准数据与预处理代码；仅性能预估时可明确选择 `skip`。
- `environment.json`、输出根、浮点基线和可复现验证输入。

## 前置检查

1. 环境对 PTQ 为 `ready`，且 `hb_mapper`、`hb_model_info` 可用。
2. 目标 march 只能是 CLI/YAML `bayes-e`。
3. 输入不是 `.hbm/.hbir/.bin`，配置不引用 HAT、HBDK4、HMCT、UCP 或 `nash-*`。
4. 为每次尝试创建新 run/working 目录；已有输出不得默认覆盖。

## 执行步骤

1. `x5-model-preflight`：格式、I/O、参考运行和 checker。
2. `x5-calibration-data-prepare`：生成样本清单和预处理证据；`skip` 时记录精度未验证风险。
3. `x5-ptq-config-authoring`：生成并通过 schema/语义校验的 YAML。
4. `x5-ptq-compile`：运行 checker/makertbin、定位唯一 `.bin`、验证 `BPU march: bayes-e`。
5. `x5-runtime-deploy`：在板端或等价 Runtime 上做 I/O 与正确性验证；需要时做性能评测。
6. 将阶段产物、哈希、日志和验证写入运行收据。

## 产物与完成标准

- checker 支持性证据、校准 manifest、验证通过的 YAML。
- 唯一 X5 `.bin`、量化 ONNX（若工具生成）、完整日志和哈希。
- `hb_model_info` 明确显示 `BPU march: bayes-e`。
- Runtime 输出与参考结果的可解释比对；若板端不可用，只能标为未完成/受限，不能宣称部署成功。

## 风险与确认

生成新配置/模型为中风险；复用非空工作目录、覆盖模型或长时间批量编译前必须确认。不得用 `--allow-nonempty-working-dir` 代替审批。

## 失败与交接

- checker/格式失败 → `x5-model-diagnostics`。
- 精度失败 → `x5-accuracy-diagnostics`。
- 性能失败 → `x5-performance-diagnostics`。
- 同一配置最多两次；第二次失败后保留 attempt 目录，不自动换一批参数继续试。

## 按需参考

- `.drobotics/platforms/x5/policies/compatibility.md`
- `.drobotics/platforms/x5/references/run-contract.md`
