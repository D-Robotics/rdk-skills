---
name: x5-consistency-diagnostics
description: 比较 X5 浮点、calibration/QAT、定点、编译和 Runtime 的固定输入输出，定位首个数值或 I/O 不一致阶段；当 Plugin 编译后掉点、仿真与板端不同或 C++/Python 输出不一致时使用。默认只读。
version: 1.0.0
license: Apache-2.0
---

# X5 一致性诊断

## 目标与边界

建立同一输入跨阶段的证据链，优先排除输入打包、layout、dtype、量化参数和输出解析错误，再怀疑编译器或 Runtime。

## 输入合同

- 固定输入文件及哈希、每阶段模型/产物哈希。
- 各阶段原始输出、shape/dtype/layout、量化 scale/shift 和后处理代码。
- 编译日志、Runtime 日志、板端版本和允许误差。

## 前置检查

1. 每个阶段接收的逻辑输入相同；图像解码/resize/色彩变换只执行一次。
2. 比较 raw tensor 前先按各自量化参数、对齐和 layout 还原。
3. 不把任务指标一致当作数值一致，也不要求伪量化与定点逐 bit 一致。

## 执行步骤

1. 建表记录 float、fake-quant、quantized、compiled、Runtime 的 I/O 元数据。
2. 对同一输出计算 shape/dtype、有限值、范围、cosine、最大/平均误差。
3. 找第一个异常阶段，并检查其输入是否已不同。
4. 对 Runtime 优先验证 `alignedByteSize`、cache flush、输入顺序、NV12 padding 和输出对齐解析。
5. 只设计一个最小实验，例如绕过后处理、固定单输入或导出中间层。

## 产物与完成标准

- `consistency-report` 包含首次分歧边界、输入证据、误差指标和最小复现。
- 每个阶段都关联模型/输入哈希；无法对齐的阶段明确标记不可比较。
- 恢复计划指向具体 Workflow，而非泛化“重新编译”。

## 风险与确认

分析和生成新报告为低风险。重新导出、编译或板端运行必须交接并取得对应确认。

## 失败与交接

Plugin 编译问题 → `x5-qat-compile`；C++ I/O → `x5-runtime-cpp-infer`；板端加载 → `x5-runtime-deploy`。

## 按需参考

- `_sources/oe_mapper/source/ptq/ptq_tool/hb_verifier.rst.txt`
- `_sources/runtime/source/runtime_dev.rst.txt`
