---
name: x5-model-diagnostics
description: 只读分诊 X5 环境、checker、PTQ、QAT、Runtime、精度、性能和日志问题；当已有 failure receipt、environment.json、日志或中间产物，需要定位首次失败阶段和下一 Skill 时使用。默认不重跑训练、编译、安装或上传。
version: 1.0.0
license: Apache-2.0
---

# X5 模型诊断路由

## 目标与边界

从失败收据和证据确定首次失败阶段，输出可证伪的根因假设和最小恢复实验。诊断不是“换参数再跑一次”的别名。

## 输入合同

- `receipt.json`、`environment.json`、`run-state.json`、相关日志和配置。
- 模型/数据/源码哈希、已验证中间产物和可复现输入。
- 用户观察到的期望与实际结果。

## 前置检查

1. 检查证据是否来自同一 run/attempt、模型哈希和环境。
2. 先区分环境、模型支持、校准/训练、编译、Runtime I/O、精度或性能。
3. 诊断期间不修改原始模型、配置、环境或板端状态。

## 执行步骤

1. 建立阶段时间线并找到第一个从 pass 变 fail 的边界。
2. 提取错误码、首个异常节点、输入合同差异和环境变化。
3. 选择专项 Skill：
   - 精度/量化掉点 → `x5-accuracy-diagnostics`
   - 阶段输出不一致 → `x5-consistency-diagnostics`
   - 延时/吞吐/资源 → `x5-performance-diagnostics`
   - 工具/版本/板端 → `x5-environment-probe`
4. 输出一个最小实验，只改变一个主变量，并说明成功/失败如何更新假设。

## 产物与完成标准

- `diagnosis-report.json/md` 包含首次失败阶段、证据、假设、反证、恢复路径和下一 Skill。
- 结论区分“已证明”“高概率”“缺证据”。
- 不以日志关键词或命令返回码单独认定根因。

## 风险与确认

默认只读，低风险。任何重跑、安装、覆盖、上传或设备修改都必须形成新计划并重新确认。

## 失败与交接

证据不足时列出最小补充项并保持 `blocked`；不得从不完整日志猜配置。专项诊断同一假设最多验证两次。

## 按需参考

- `.drobotics/platforms/x5/references/manual-map.md`
- `.drobotics/platforms/x5/references/run-contract.md`
