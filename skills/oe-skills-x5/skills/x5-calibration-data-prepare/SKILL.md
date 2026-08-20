---
name: x5-calibration-data-prepare
description: 为 X5 OE Mapper PTQ 准备和审计校准数据；当用户需要选择代表性样本、复现训练前处理、生成二进制/数组数据与 manifest 时使用。只处理 PTQ 数据，不处理 HAT Dataset/Trainer 或 QAT 训练管线。
---

# X5 校准数据准备

## 目标与边界

生成与浮点模型输入合同一致、可追溯的 PTQ 校准目录。默认参考手册选择约 100 份代表性样本，可根据数据分布调整，但不盲目追求数量。

## 输入合同

- 原始样本集合及抽样规则。
- 每个输入的名称、shape、dtype、layout、色彩空间和训练前处理。
- YAML 中计划承担的 `mean_value/scale_value` 等预处理责任。
- 输出目录和随机种子。

## 前置检查

1. 排除纯色、损坏、无目标等非代表性异常样本，除非它们属于真实业务分布。
2. 多输入样本必须一一配对并保持 `input_name` 顺序。
3. 校准数据输出应保持 `input_type_train`、`input_layout_train` 和 `input_shape`。
4. 若 YAML 已执行归一化，数据脚本不得重复 mean/scale。

## 执行步骤

1. 固定抽样种子和数据版本，保存原始样本相对路径与哈希。
2. 复用生产/浮点评测前处理，禁止另写“差不多”的 resize、色彩或归一化。
3. 对每个产物记录 shape、dtype、最小/最大/均值、非有限值数量和来源样本。
4. 随机回读若干文件送入浮点模型，确认输出可复现。
5. 生成 `calibration-manifest.json` 和 `preprocess-report.md`。

## 产物与完成标准

- 校准目录、manifest、抽样规则、前处理版本和统计报告齐全。
- 文件数量、输入配对、shape/dtype/layout 与合同一致；无 NaN/Inf。
- 用同一数据做浮点回读时结果在定义容差内一致。

## 风险与确认

写入新数据目录为中风险。默认不删除旧校准集、不覆盖同名文件、不复制隐私数据到未确认位置。

## 失败与交接

发现精度掉点或数据分布异常时交接 `x5-accuracy-diagnostics`；不要一边换校准样本一边改 YAML 算法。

## 按需参考

- `_sources/oe_mapper/source/ptq/ptq_usage/prepare_calibration_data.rst.txt`
- `_sources/oe_mapper/source/faststart/quickstart.rst.txt`
