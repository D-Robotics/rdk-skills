---
name: rdk-diagnostic
description: Read-only health snapshot for D-Robotics RDK boards (X3/X5/Ultra/S100/S600). Use when the user asks what board or SoC this is, memory size, temperature, BPU load, what is running, or why the board is slow, hot, or out of memory. Triggers include 板卡型号, 多大内存, 温度, 发烫, 很烫, 特别烫, 很慢, 卡顿, BPU 占用, 设备快照, 跑着什么, hrut_somstatus, rdkos_info. Do not use to change settings, stop services, or free memory — hand off to rdk-system-config, rdk-headless-mode, or rdk-memory-audit.
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - diagnostic
    - telemetry
  languages:
    - bash
  data-classification: public
---

# RDK Diagnostic

为运行中的 D-Robotics RDK 设备提供统一的、Agent 友好的健康视图。替代对
`hrut_somstatus`、`/sys/devices/system/bpu/*/ratio`、`/proc/device-tree/model`、
`free`、`swapon`、`df`、`systemctl list-units` 等命令各自输出哪部分真相的记忆负担。

## Purpose

从 RDK 主机采集**只读**健康快照，使 Agent 能够基于实时数据（而非猜测）回答设备身份、
内存、BPU、温度、存储和服务状态问题。

## When to use

当用户提出以下问题时激活：

- "这是哪块 RDK 板卡？什么 SoC？多大内存？"
- "这块 RDK 现在跑着什么？"
- "为什么我的 RDK 很慢 / 很烫 / 内存不足？"
- "给我一份 BPU / CPU / 内存占用快照。"
- "帮我解释一下 hrut_somstatus 的输出。"
- "哪些正在运行的服务可以关掉？"
- 用户已安装 rdk-memory-audit、rdk-headless-mode、rdk-model-deploy 或
  rdk-model-benchmark，需要先做一次基线测量。

**不要**用本技能修改电源模式、清理缓存、停止服务、安装软件包、部署模型或调整推理参数。
只报告观测到的状态，然后交接（handoff）给对应的行动类技能。

## Prerequisites

- 在 RDK 主机上运行，或在能看到 RDK 系统路径与进程数据的沙箱/容器中运行。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/snapshot.sh` | 输出一体化 JSON 快照：身份、内存、BPU、温度、磁盘、内核错误计数、Top 进程与候选服务。 | `--human`、`--top-procs N`、`--record`（追加趋势样本到 `~/.rdk-skill/snapshots.jsonl`） |
| `scripts/mem_summary.sh` | 输出紧凑的人类可读 RAM / CMA / swap 摘要行。 | `--short`、`--watch`、`--interval N` |
| `scripts/detect_rdk.sh` | 导出或打印本仓库统一的 RDK 板卡/SoC/BPU 架构字段。 | 无参数 |

如果你的 Agent 运行时支持 run_script，用它运行 `scripts/snapshot.sh` 或
`scripts/mem_summary.sh` 并总结返回结果；否则从仓库根目录用 bash 运行脚本。

## Instructions

1. 运行 `scripts/snapshot.sh` 获取一体化 JSON 视图（首选默认）。
2. 需要一行人类可读的内存摘要时，运行 `scripts/mem_summary.sh`。
3. 需要官方全量系统报告（软硬件版本、驱动/软件包清单、日志）时，运行
   `sudo rdkos_info`（RDK OS 内置命令）并总结其输出。
4. 需要解释用户粘贴的 `hrut_somstatus` 输出时，查阅 `references/hrut-somstatus-fields.md`。
5. 需要了解 BPU sysfs 节点含义时，查阅 `references/bpu-sysfs.md`。
6. 用户问趋势类问题（"是不是越来越烫/越来越卡"）时，用 `--record` 周期性采样，
   基于 `~/.rdk-skill/snapshots.jsonl` 中的实测历史回答，而不是单点快照推断。

## Reporting guidance

在总结设备状态前先运行对应的辅助脚本，并且**只报告脚本返回的字段**。如果运行时阻止直接执行，
用 `bash {baseDir}/scripts/<script-name>` 运行，而不要尝试 chmod 文件。

- 回答"这是什么板卡"类问题时，引用 `product_model` 或 `board`、`soc`、`rdk_os_version`
  和 `mem_total_gb`。
- 回答"又慢又烫"类问题时，运行 snapshot.sh 并同时总结症状两侧：`thermal_c` 表征发热，
  `bpu.cores[*].ratio_pct`、`top_processes` 表征负载。最后给出具体的交接建议，例如
  rdk-memory-audit、rdk-headless-mode 或 rdk-model-benchmark。
- 回答"哪个进程占内存"类问题时，运行 snapshot.sh 并以 `pid <number>`、`cmd` 及其
  `rss_kb` / MiB 值点名首位进程。如果 CMA/ION 是相关信号，同时引用 `cma` 字段。

如果你的 Agent 运行时不会自动相对技能目录执行辅助脚本，用 AgentSkills 的 `{baseDir}`
占位符解析脚本路径：

```
{baseDir}/scripts/snapshot.sh
{baseDir}/scripts/mem_summary.sh
```

除非运行时明确将技能注册为可调用工具，否则不要把 `rdk-diagnostic` 当作工具名调用；
Agent Skills 通常是"指令 + 文件"，不是直接的工具函数。

所有脚本都 source 位于 `skills/rdk-diagnostic/scripts/detect_rdk.sh` 的统一平台检测器
（导出 `RDK_BOARD`、`RDK_SOC`、`RDK_BPU_ARCH`、`RDK_MEM_GB`、`RDK_OS_VERSION`、
`RDK_PRODUCT_MODEL`）。其他技能应 source 该检测器而不是重复实现 RDK 识别逻辑。
非 RDK 平台上以退出码 2 结束并给出修复提示。

## Limitations

- 看到本技能文件并不保证能访问 RDK 主机硬件。如果沙箱内缺少 `/proc/device-tree/model`、
  `/etc/version`、`hrut_somstatus` 或 `/sys/devices/system/bpu`，应说明沙箱缺少 RDK
  主机可见性，并请用户在 RDK 主机上运行或换用主机可见的沙箱配置。
- 部分 BPU / ION 调试节点需要 root，非特权运行可能报告 `bpu.readable: false` 或不完整的
  `cma` 字段。
- 本技能只报告观测状态。当某个工具缺失或不可访问时，**不得编造**内存、BPU、温度、服务
  或回收数据。

## Error handling

- 如果辅助脚本以"非 RDK 平台"退出，报告当前环境不是 RDK 主机或缺少主机可见性；不要用
  通用 Linux 值替代。
- 如果 `hrut_somstatus` 或 BPU sysfs 不可用，保留 JSON 中对应的 null / false / 空字段，
  并解释哪个信号受限。
- 如果 snapshot.sh 输出畸形 JSON，报告原始失败并在修复辅助脚本输出后重跑；不要手工编辑
  出一份合成的设备快照。

## Output contract for snapshot.sh

```json
{
  "board": "rdk-x5",
  "soc": "sunrise-5",
  "bpu_arch": "bayes-e",
  "mem_total_gb": 4,
  "rdk_os_version": "3.0.0",
  "product_model": "D-Robotics RDK X5 V1.0",
  "memory_kb": { "total": 4045884, "available": 2837520, "swap_total": 0, "swap_free": 0, "cached": 812340 },
  "cma": { "total_kb": 262144, "free_kb": 180224 },
  "bpu": {
    "readable": true,
    "cores": [ { "core": 0, "ratio_pct": 37 }, { "core": 1, "ratio_pct": 0 } ]
  },
  "thermal_c": { "cpu": 46.2, "bpu": 48.1 },
  "kernel_log": { "readable": true, "err_count": 3 },
  "disk": [ { "mount": "/", "used_pct": 41 } ],
  "top_processes": [ { "pid": 4321, "cmd": "hrt_model_exec", "rss_kb": 512000 } ],
  "candidate_services": { "lightdm": { "active": "active", "enabled": "enabled" } }
}
```

Agent 应向用户呈现其中的关键部分（板卡、可用内存、BPU 各核占用、最高温区、Top 进程），
并主动提出可深入的方向（top_processes、cma、candidate_services）。

## Safety

本技能是只读的：不修改调度策略、不执行 `sync`/`drop_caches`、不改动任何服务。
要基于发现采取行动，请交接给：

- **rdk-memory-audit** — 聚焦内存快照 + drop_caches 前后验证闭环
- **rdk-headless-mode** — 关闭桌面 + 辅助守护进程（安全、可回退）
- **rdk-camera-setup** — 摄像头检测与出图验证
- **rdk-model-deploy** — 选择 hobot_dnn / hrt_model_exec 部署路径
- **rdk-model-benchmark** — 可复现的模型延迟 / 帧率基准
- **rdk-log-forensics** — `kernel_log.err_count` 非零时的崩溃/日志取证深查

## Cross-platform behavior

| 板卡 | 识别的 variants | hrut_somstatus | BPU sysfs | CMA meminfo |
| --- | --- | --- | --- | --- |
| RDK X3 / X3 Module | rdk-x3-2gb, rdk-x3-4gb, rdk-x3-module | yes | yes（bpu0/bpu1） | yes |
| RDK X5 / X5 Module | rdk-x5-4gb, rdk-x5-8gb, rdk-x5-module | yes | yes（bpu0） | yes |
| RDK Ultra | rdk-ultra | yes | yes（bpu0/bpu1） | yes |
| RDK S100 / S100P | rdk-s100 | yes* | yes | yes |
| RDK S600 | rdk-s600 | yes* | yes | yes |

\* 不同 RDK OS 版本上 `hrut_somstatus` 的字段布局存在差异；脚本对每个工具的存在性做了
优雅降级处理，对无法触达的工具报告 null / false（在 Agent 无 `/sys/kernel/debug` 所需
特权时属正常现象）。板卡识别优先使用 `/proc/device-tree/model` 字符串，字符串过于泛化时
回退到内存容量启发式判断。
