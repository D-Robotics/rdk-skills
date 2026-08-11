# hrut_somstatus 字段参考

> 信息来源（官方文档）：
> - `rdk_x_doc/docs/09_Appendix/rdk-command-manual/cmd_hrut_somstatus.md`
> - `rdk_x_doc/docs/09_Appendix/rdk-command-manual/cmd_rdkos_info.md`

`hrut_somstatus` 是 RDK OS 自带的 SoM 状态查询工具，可获取温度传感器温度、CPU/BPU
的运行频率以及 BPU 负载。**需要以 sudo 运行**：`sudo hrut_somstatus`。
本参考用于解释用户粘贴的输出，Agent 不应凭记忆猜测字段含义。

## 典型输出（RDK X3，摘自官方命令手册）

```
=====================1=====================
temperature-->
        CPU      : 61.3 (C)
cpu frequency-->
              min       cur     max
        cpu0: 240000    240000  1800000
        cpu1: 240000    240000  1800000
        cpu2: 240000    240000  1800000
        cpu3: 240000    240000  1800000
bpu status information---->
             min        cur             max             ratio
        bpu0: 400000000 1000000000      1000000000      0
        bpu1: 400000000 1000000000      1000000000      0
```

## 字段说明

| 字段 | 含义 | 备注 |
| --- | --- | --- |
| `temperature → CPU` | SoC 温度（摄氏度） | X3 只有一个温区；X5/Ultra 可能有 CPU/BPU 多个温区 |
| `cpu frequency → min/cur/max` | 各 CPU 核的最小/当前/最大频率（kHz） | `cur < max` 且负载高时，可能是温控降频（throttling） |
| `bpu status → min/cur/max` | BPU 核频率（Hz） | 注意与 CPU 行的单位不同 |
| `bpu status → ratio` | BPU 核占用率（%） | 0 表示空闲；持续 90+ 表示 BPU 饱和 |

## 解读要点

- **温控降频判断**：温度 > 80°C 且 `cpu cur` 低于 `max` → 报告为温控降频，建议加装散热。
- **BPU 饱和判断**：任一核 `ratio` 持续高于 90 → 模型推理受 BPU 吞吐限制，
  交接 rdk-model-benchmark 做量化分析。
- **BPU 空闲但推理慢**：`ratio` 接近 0 而用户抱怨推理慢 → 瓶颈大概率在 CPU 前后处理
  或 IO，而不是 BPU 本身。

## 等价 sysfs 数据源

| hrut_somstatus 字段 | sysfs 路径 |
| --- | --- |
| BPU ratio | `/sys/devices/system/bpu/bpu*/ratio` |
| CPU 温度 | `/sys/class/thermal/thermal_zone*/temp`（毫摄氏度） |
| CPU 频率 | `/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq` |

## 相关命令：rdkos_info

需要一次性收集软硬件版本、驱动清单、RDK 软件包清单与系统日志时，官方提供
`sudo rdkos_info`（选项：`-b` 基础 / `-s` 简洁（默认）/ `-d` 详细）。其输出包含
`[Hardware Model]`、`[CPU And BPU Status]`、`[ION Memory Size]`、`[RDK OS Version]`、
`[RDK Kernel Version]`、`[RDK Miniboot Version]` 等段落，是设备身份与版本问题的
首选权威数据源。
