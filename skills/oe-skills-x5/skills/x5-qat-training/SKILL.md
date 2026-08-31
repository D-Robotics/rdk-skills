---
name: x5-qat-training
description: 执行 X5 Plugin calibration、量化感知训练、validation 和 convert 后定点评测；当适配模型已可运行，需要生成可比较指标与检查点时使用。要求 March.BAYES_E 和可复现训练，不使用 HAT Trainer。
version: 1.0.0
license: Apache-2.0
---

# X5 QAT 训练与定点验证

## 目标与边界

用同一数据和评价代码记录 `float → calibration → QAT → quantized` 的首个掉点阶段。训练循环由用户项目/PyTorch 实现，不引入 HAT Engine、config 或 callback。

## 输入合同

- 已适配模型、浮点 checkpoint、训练/校准/验证 DataLoader。
- 评价函数、浮点基线、目标阈值、随机种子、设备和预算。
- 新检查点目录及覆盖策略。

## 前置检查

1. 固定 `March.BAYES_E`，记录 Plugin/PyTorch/CUDA 版本。
2. 先在当前环境复现浮点指标。
3. calibration、QAT validation 和 quantized validation 必须共享前处理与评价口径。
4. 数据加载器不得隐式读取 HAT registry/config。

## 执行步骤

1. Calibration：模型 `eval()`，设置 calibration 状态，运行代表性数据并保存指标/observer 摘要。
2. QAT：模型 `train()`，设置 QAT 状态，以较小学习率训练；每轮保存 loss、指标和配置哈希。
3. Validation：模型 `eval()` 后设置 validation 状态，保存最好 checkpoint，不覆盖历史最好结果。
4. Convert：将 calibration 或最佳 QAT 模型转为定点模型，使用同一验证集重新评测。
5. 运行：

~~~bash
python .drobotics/platforms/x5/scripts/check_qat_target.py \
  --source <training.py> --stage training --report <training-check.json>
~~~

## 产物与完成标准

- 浮点、calibration、每轮 QAT、最佳 QAT 和 quantized 指标可追溯。
- 最佳 checkpoint、optimizer/scheduler 状态、随机种子和数据版本完整。
- 定点指标达到用户阈值；否则明确首个掉点阶段，不进入“成功”状态。

## 风险与确认

训练耗时、GPU 资源和检查点写入为中风险；长训练或覆盖已有 checkpoint 前必须确认预算和目标路径。

## 失败与交接

精度不达标时交接 `x5-accuracy-diagnostics`。不得同时更换 qconfig、数据、学习率和预处理；每次实验只改变一个主变量。

## 按需参考

- `_sources/plugin/source/user_guide/calibration.md.txt`
- `_sources/plugin/source/user_guide/qat.md.txt`
