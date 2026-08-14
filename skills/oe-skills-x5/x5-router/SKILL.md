---
name: x5-router
description: 路由 X5 环境、OE Mapper PTQ、Plugin QAT、Runtime、板端 Python 和诊断请求；当目标芯片明确为 X5 或请求包含 bayes-e、hb_mapper、X5 .bin、March.BAYES_E 时使用。只选择一个主 Skill 并生成 route.json；不执行 HAT、X3 或 S 系列工作流。
---

# X5 路由

## 目标与边界

- 读取 `.drobotics/platforms/x5/skill-index.json`，以输入、产物、环境和风险选择一个主 Skill。
- 用户只说“X 系列”时先确认 X5/X3；X3 和其他 X 芯片在专属 Pack 可用前返回 `blocked`。
- HAT、HAT config、Trainer、Model Zoo 和 `tools/compile_perf.py` 不在范围内。
- 不调用 `s-*`、HBDK4、HMCT、UCP、`nash-*` 或 `March.BAYES`。

## 输入合同

- 用户结果目标、目标芯片、模型/代码路径和期望产物。
- 已知模型格式、输入输出合同、板端信息和失败收据。
- 是否允许安装、训练、生成模型、上传或覆盖文件。

## 前置检查

1. 用芯片型号、模型后缀和工具名确认平台；`.bin` 不能单独证明 X5，仍需 `hb_model_info` 或来源证据。
2. 区分 PTQ 与 QAT：ONNX/Caffe 浮点模型走 PTQ；可训练 PyTorch + Plugin 走 QAT。
3. 区分 Runtime：`.bin` C/C++/命令行走 Runtime；板端 `HB_HBMRuntime` Python 走 Python API。
4. 环境未知时先选 `x5-environment-probe`，不要直接选安装或执行 Skill。

## 执行步骤

| 目标 | 主 Skill | 典型后续交接 |
| --- | --- | --- |
| 检查/准备环境 | `x5-environment-setup` | probe → install（如获确认） |
| ONNX/Caffe 到 X5 `.bin` | `x5-ptq-deploy` | preflight → data → config → compile → Runtime |
| Plugin calibration/QAT | `x5-qat-deploy` | adaptation → training → compile |
| `.bin` C/C++/上板/性能 | `x5-runtime-deploy` | C++ → perf → monitor |
| X5 板端 Python | `x5-bpu-python-api` | environment/diagnostics |
| 已有失败证据 | `x5-model-diagnostics` | accuracy/consistency/performance |

将候选、拒绝理由、主 Skill 和有序 handoff 写入运行目录的 `route.json`。多个关键词命中时也只保留一个主 Skill。

## 产物与完成标准

- `route.json` 符合 Pack 的 route schema，且 `selected_skill` 在 X5 注册表中。
- 明确说明拒绝 S、X3、HAT 或格式不兼容候选的理由。
- 环境、输入或授权不足时只路由到预检/探测，不生成执行成功结论。

## 风险与确认

路由本身为低风险。不得把用户对“分析”的同意解释为对安装、训练、覆盖、上传或停止进程的授权。

## 失败与交接

- 芯片不明：只问一个最小问题“目标板卡是 X5、X3 还是其他型号？”
- HAT 请求：说明当前 Pack 明确排除 HAT，不迁移配置。
- 无合法候选：保存拒绝理由并以 `blocked` 结束。

## 按需参考

- `.drobotics/platforms/x5/policies/compatibility.md`
- `.drobotics/platforms/x5/policies/risk-policy.md`
- `.drobotics/platforms/x5/references/run-contract.md`
