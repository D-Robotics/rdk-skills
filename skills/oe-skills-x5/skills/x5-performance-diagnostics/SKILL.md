---
name: x5-performance-diagnostics
description: 关联 X5 hb_perf 静态估计、Runtime 实测、BPU ratio、温度频率和 CPU/I/O 开销以定位性能瓶颈；当模型太慢、静态与板端差异大或 BPU 利用率异常时使用。默认只读，不自动改 O3、core、频率或系统进程。
version: 1.0.0
license: Apache-2.0
---

# X5 性能诊断

## 目标与边界

区分模型图/编译、Runtime 调度、CPU 前后处理、数据搬运、系统负载和热/频率限制。单一平均延时或 BPU ratio 不能独立证明根因。

## 输入合同

- `hb_perf`/编译静态报告、板端原始延时、测试矩阵和模型哈希。
- `board-resource.json`、温度/频率、Runtime/镜像版本和后台负载。
- 输入准备、后处理和计时边界说明。

## 前置检查

1. 功能正确性已通过，测试输入和 warmup/重复次数一致。
2. 静态估计与实测使用同一模型版本、core/batch 和输入 shape。
3. 性能日志没有把上传、解码、后处理或日志打印混进 BPU 时间而未说明。

## 执行步骤

1. 分解总延时：输入准备 → Runtime submit/wait → 输出回读 → 后处理。
2. 对比静态 BPU 估计与实测 BPU 段；检查 CPU fallback、图切分和频繁小 function call。
3. 关联 BPU ratio、温度、当前频率、DDR/内存和后台负载。
4. 选一个受控实验：编译选项、core/batch、输入 source、前处理位置或 Runtime 调度，仅改变一项。
5. 定义改善阈值、回归正确性检查和停止条件。

## 产物与完成标准

- `bottleneck-report` 将证据归类为模型/编译、Runtime、CPU/I/O 或系统资源。
- 指标带命令、版本、模型哈希和测试口径。
- 给出一个优先实验及预期效果；没有证据时不建议盲目 O3/fast-perf。

## 风险与确认

分析为低风险。重新编译/长压测为中风险；调频、停止进程、修改电源策略为高风险并需明确确认。

## 失败与交接

编译配置 → `x5-ptq-config-authoring`；实测 → `x5-runtime-perf-eval`；资源采样 → `x5-board-monitor`。

## 按需参考

- `_sources/oe_mapper/source/tune_content/performance_tune.rst.txt`
- `_sources/oe_mapper/source/ptq/ptq_tool/hb_perf.rst.txt`
