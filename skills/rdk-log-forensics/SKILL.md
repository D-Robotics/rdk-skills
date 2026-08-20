---
name: rdk-log-forensics
description: Read-only crash and log forensics for D-Robotics RDK devices — extract kernel errors from dmesg, list failed systemd units, detect coredumps and abnormal reboots, and summarize evidence for root-cause analysis. Use when a program crashed, the board rebooted or froze unexpectedly, a service will not start, or the user pastes an error asking what the logs say. Triggers include 崩溃, 死机, 自动重启, 突然重启, 段错误, Segmentation fault, coredump, 内核报错, dmesg 报错, journalctl, 服务起不来, 起不来了, 开机失败, oops. Do not use for live performance snapshots (rdk-diagnostic), memory measurement (rdk-memory-audit), or apt/disk maintenance (rdk-system-maintain).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - logs
    - forensics
    - crash
  languages:
    - bash
  data-classification: public
---

# RDK Log Forensics

崩溃 / 死机 / 服务起不来类问题的**只读**日志取证：从 dmesg、systemd、coredump
中提取结构化异常证据，替代"把整段日志贴给我看看"的低效循环。官方全量报告命令
`rdkos_info` 与 rdk-diagnostic 中的用法一致。

## Purpose

把散落在 dmesg / journalctl / /var/crash 里的异常信号收敛成一份结构化清单
（错误计数、失败单元、最近异常原文摘录），让 Agent 基于证据归因，
并为上层诊断编排提供第四类证据源（前三类：快照、
内存审计、模型基准）。

## When to use

当用户提出以下问题时激活：

- "程序跑着跑着崩溃了 / 段错误。"
- "板子突然自动重启 / 死机了，看看日志？"
- "某个服务起不来了。"
- "dmesg / journalctl 里这些报错是什么意思？"
- "帮我收集一下崩溃现场的日志证据。"

**不要**用本技能做实时性能快照（交接 rdk-diagnostic）、内存测量（交接
rdk-memory-audit）或 apt/磁盘维护（交接 rdk-system-maintain）。

## Prerequisites

- 完整 dmesg 与 journalctl 历史通常需要 root；非特权运行时对应字段报
  `readable: false`。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/collect_logs.sh` | 只读收集：内核 err+ 级消息计数与最近条目、systemd 失败单元、coredump/crash 文件、上次启动是否异常，输出 JSON。 | `--json`（默认）、`--human`、`--lines N` |

## Instructions

1. 运行 `scripts/collect_logs.sh` 获取结构化异常清单。
2. **服务起不来**：以 `failed_units` 为入口，对具体单元运行
   `systemctl status <unit>` 与 `journalctl -u <unit> -n 50` 摘取首个 ERROR 原文。
3. **突然重启/死机**：看 `last_boot.clean` 与 `kernel.recent_errors`；存在
   thermal/oops/OOM 关键字时分别交接——温度类 → rdk-diagnostic；OOM/CMA 类 →
   rdk-memory-audit；模型推理崩溃 → rdk-model-deploy。
4. **用户粘贴报错**：先在脚本输出的 `kernel.recent_errors` 中确认板端是否有
   同源记录，再用 rdk-docs-reference 检索官方 FAQ 中的同类报错。
5. 需要官方全量系统报告（软硬件版本、驱动、日志打包）时运行 `sudo rdkos_info`
   并总结，与 rdk-diagnostic 的用法一致。

## Reporting guidance

- 每条结论必须引用脚本输出的具体字段（如 `failed_units[0].unit`、
  `kernel.err_count`）；无证据时说"日志中未见相关记录"，不推断。
- 摘录内核消息时保留原文（含时间戳），不改写、不翻译报错本身。
- 崩溃归因给出"证据 → 假设 → 验证方法"三段，不直接下结论。

## Limitations

- 只读取证：不清理日志、不重启服务、不修改 core_pattern。
- 内核 ring buffer 有限，久远的崩溃现场可能已被覆盖；如实报告观察窗口。
- 不做应用级 core 文件的 gdb 解析（超出板端技能范围，指引用户在开发机分析）。

## Error handling

- `dmesg` 无权限：报告 `kernel.readable: false` 并给出 sudo 提示，不用空结果
  冒充"没有错误"。
- `journalctl`/`coredumpctl` 缺失：对应字段报 null 并说明信号受限。
- 脚本报 not-an-rdk-host 时如实报告环境不可见。

## Output contract for collect_logs.sh

```json
{
  "board": "rdk-x5",
  "kernel": {
    "readable": true,
    "err_count": 3,
    "recent_errors": [ "[12034.5] mipi_host0: rx timeout" ]
  },
  "failed_units": [ { "unit": "myapp.service", "active": "failed" } ],
  "coredumps": { "coredumpctl": null, "var_crash_files": 1 },
  "last_boot": { "clean": false, "previous_boot_available": true }
}
```

## Safety

全部操作只读；不执行任何清理、重启、内核参数修改。取证输出可能包含路径与
进程名，不包含凭据文件内容——本技能绝不读取 /etc/shadow、密钥或用户隐私文件。

## Cross-platform behavior

全系 RDK 板卡适用；dmesg 权限策略、journald 持久化配置随 RDK OS 版本不同，
脚本对缺失工具逐项降级并如实报告 null / false。
