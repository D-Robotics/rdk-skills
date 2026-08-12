---
name: x5-accuracy-diagnostics
description: 定位 X5 PTQ 或 Plugin QAT 的首次精度掉点阶段；当有浮点、校准、QAT、定点、编译或板端指标及固定输入时使用。只读比较并设计单变量实验，不自动重训或重编译。
---

# X5 精度诊断

## 目标与边界

把精度问题拆成数据/前处理、校准、伪量化、定点转换、编译和 Runtime 输出阶段，先找首次分歧，再决定是否调整数据、qconfig 或 YAML。

## 输入合同

- 同一评测集上的浮点与各量化阶段指标。
- 固定样本、逐阶段输出或 dump、校准 manifest、YAML/QAT 源码和日志。
- 评价代码、阈值、模型/数据哈希和环境快照。

## 前置检查

1. 确认所有指标使用同一前处理、后处理、标签映射和评价口径。
2. 检查 dtype/layout/色彩、mean/scale 是否重复或遗漏。
3. 分开 PTQ `.bin` 与 QAT `.hbm/.hbir`，不跨合同比较工具参数。

## 执行步骤

1. 对固定样本建立阶段矩阵：float → calibration/fake-quant → quantized → compile/runtime。
2. 计算任务指标和数值差异（如 cosine、最大绝对误差、top-k/检测指标）。
3. 找首个超过阈值的层/输出/阶段，并关联校准分布、饱和、异常值和 CPU/BPU 分配。
4. 设计一个单变量实验：更换代表性校准集、修正前处理、调整一项校准/qconfig 或延长 QAT。
5. 明确预期变化、停止条件和回滚。

## 产物与完成标准

- 首次分歧阶段、受影响样本/节点、数值证据和根因置信度。
- `accuracy-report` 给出一个优先实验和一个备选，不给无序参数清单。
- 若无法定位，列出缺失的最小 dump/指标并保持 `blocked`。

## 风险与确认

分析为低风险。重新生成校准集、训练或编译必须交接对应 Workflow 并重新确认成本和输出目录。

## 失败与交接

数据问题 → `x5-calibration-data-prepare`；PTQ 参数 → `x5-ptq-config-authoring`；QAT → `x5-qat-training`。同一假设最多两次。

## 按需参考

- `_sources/oe_mapper/source/ptq/ptq_tool/accuracy_debug.rst.txt`
- `_sources/plugin/source/user_guide/quant_analysis.md.txt`
