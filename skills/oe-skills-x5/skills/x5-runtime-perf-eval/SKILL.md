---
name: x5-runtime-perf-eval
description: 在 X5 板端评测模型延时、吞吐和稳定性；当功能正确性已通过，需要使用 hrt_model_exec 或 ai_benchmark 得到可复现性能报告时使用。先读本地工具参数，不猜命令；不修改频率或停止业务进程而未确认。
---

# X5 Runtime 性能评测

## 目标与边界

将静态估计、Runtime 实测和板端资源放到同一测试矩阵。性能评测不能替代正确性验证，也不能在热降频或后台负载未知时直接下结论。

## 输入合同

- 已通过功能验证的模型和输入。
- 板卡/Runtime 版本、测试次数、warmup、batch/core/线程等矩阵。
- 目标延时/吞吐和允许的设备影响。

## 前置检查

1. 确认板卡空闲程度、温度、频率和电源模式可记录。
2. 从 `_sources/runtime/source/tool_introduction/hrt_model_exec.rst.txt` 读取当前版本参数。
3. 固定输入、后处理范围和计时边界；不同方案必须使用同一口径。

## 执行步骤

1. 先 warmup，再进行有界次数的重复测量；禁止无界 `while true` 压测。
2. 保存原始工具日志、每轮延时和错误计数。
3. 同步或分阶段调用 `x5-board-monitor` 记录温度、频率和 BPU ratio。
4. 报告 p50/p95/平均/最小/最大、吞吐、测试次数和异常样本。
5. 与 `hb_perf` 静态估计比较，说明计时范围、I/O 和 CPU 前后处理差异。

## 产物与完成标准

- 测试矩阵、原始日志、统计报告和板端资源快照。
- 每个数字可追溯到命令、模型哈希、输入和板端版本。
- 性能结论区分 BPU 执行、CPU 前后处理、I/O 和系统负载。

## 风险与确认

短时只读评测为中风险；长时间压测、频率/电源修改、停止业务进程为高风险并需确认。

## 失败与交接

结果波动或不达标时交接 `x5-performance-diagnostics`；先保持测试条件不变，不自动改编译配置。

## 按需参考

- `_sources/runtime/source/tool_introduction/hrt_model_exec.rst.txt`
- `_sources/runtime/source/ai_benchmark/ai_benchmark.rst.txt`
