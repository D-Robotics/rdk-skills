# RDK BPU sysfs 节点参考

BPU（Brain Processing Unit）是地瓜机器人 SoC 上的 NPU。RDK OS 通过 sysfs 暴露其运行状态，
本参考描述 rdk-device-skills 各脚本读取的节点及其含义。

## 节点一览

| 路径 | 含义 | 权限 |
| --- | --- | --- |
| `/sys/devices/system/bpu/bpu<N>/ratio` | 核 N 的瞬时占用率（0–100） | 普通用户可读 |
| `/sys/devices/system/bpu/bpu<N>/power_enable` | 核 N 电源开关状态 | 普通用户可读，写需 root |
| `/sys/devices/system/bpu/bpu<N>/devfreq/*/cur_freq` | 核 N 当前频率 | 普通用户可读（部分版本） |
| `/sys/devices/system/bpu/bpu<N>/users` | 占用该核的进程/模型句柄 | 部分 RDK OS 版本提供 |

## 各板卡 BPU 核数

| 板卡 | BPU 架构 | 核数 |
| --- | --- | --- |
| RDK X3 | Bernoulli | 2（bpu0 / bpu1） |
| RDK X5 | Bayes-e | 1（bpu0） |
| RDK Ultra | Bayes | 2（bpu0 / bpu1） |
| RDK S100 / S100P | Nash-e | 依产品配置（80 / 128 TOPS） |
| RDK S600 | Nash-p | 4x Nash core（最高 560 TOPS） |

## 注意事项

- `ratio` 是瞬时值，单次读取有抖动；判断负载趋势应间隔采样多次（snapshot.sh 只做单次读取，
  报告时应注明这一点）。
- 节点缺失不代表 BPU 故障：老版本 RDK OS 的节点布局不同。此时脚本报告
  `bpu.readable: false`，Agent 应说明信号受限而不是编造数值。
- 双核板卡上模型默认可能只绑定单核（`HB_BPU_CORE` 环境变量或推理 API 的 core_id 参数
  控制）；一核饱和另一核空闲属于常见现象，可作为优化建议报告。
