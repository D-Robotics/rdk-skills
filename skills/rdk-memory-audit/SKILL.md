---
name: rdk-memory-audit
description: Measure DRAM and CMA/ION memory on D-Robotics RDK devices and verify reclamation with before/after data. Use when the user asks how much memory is left, wants to measure or free memory, or mentions drop_caches, CMA, ION, ion alloc failed. Triggers include 内存不够, 内存不足, 还剩多少内存, 实测内存, 腾出内存, 释放内存, 清缓存, 内存够不够. Do not use to stop the desktop or services (rdk-headless-mode) and do not quote doc theory instead of live measurement.
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - memory
    - audit
  languages:
    - bash
  data-classification: public
---

# RDK Memory Audit

聚焦内存的审计闭环：先测量、再回收、再验证。所有结论必须来自 `scripts/audit.sh` 的
实测数据，禁止凭经验估算 RDK 的可回收内存。

## Purpose

对 RDK 的 DRAM 与 CMA/ION 内存做基线测量，在执行回收动作（drop caches、关停进程）
前后用同一脚本对比验证，产出"回收了多少、来自哪里"的可信结论。

## When to use

当用户提出以下问题时激活：

- "RDK 内存不够了，还能腾出来多少？"
- "现在还剩多少内存？帮我实测一下。"
- "帮我清一下缓存 / 清掉所有缓存。"
- "跑这个模型之前先看看内存够不够。"
- "drop_caches 到底有没有用？释放了多少？"
- "CMA / ION 被谁占了？"
- rdk-diagnostic 报告 `memory_kb.available` 偏低后的深入分析。

**不要**用本技能停服务或改系统配置——关停桌面/服务请交接 rdk-headless-mode。
本技能唯一的变更动作是 `--apply` 门控下的 `drop_caches`。

## Prerequisites

- 在 RDK 主机上运行。
- `--apply` 回收步骤需要 root（写 `/proc/sys/vm/drop_caches`）。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/audit.sh` | 输出 JSON 内存审计：DRAM、CMA、swap、Top RSS 进程。 | `--label <name>` |
| `scripts/reclaim_verify.sh` | 基线 → 回收 → 复测的完整闭环；默认 dry-run，只有 `--apply` 才真正执行 drop_caches。 | `--apply` |

## Instructions

1. 运行 `scripts/audit.sh --label baseline` 获取基线。
2. 需要验证回收效果时，运行 `scripts/reclaim_verify.sh`（dry-run 预览动作）。
3. 用户明确同意后，以 root 运行 `scripts/reclaim_verify.sh --apply`，脚本自动输出
   before/after 差值。
4. 报告时引用脚本输出的 `reclaimed_kb` 字段，注明数据来自实测。
5. **回收后仍不够用时的后续路径**（按收益排序）：
   - 常驻占用大 → 交接 rdk-headless-mode 关停桌面/非必要服务；
   - 模型/CMA 压力大 → 交接 rdk-model-deploy 换小模型；
   - 仍需扩展虚拟内存 → swap/zram 属通用 Linux 手段，非 RDK 专有结论；先用
     rdk-docs-reference 检索官方文档是否有对应板卡的 swap 指引，有则引用原文；
     无官方指引时明确告知用户这是通用方案，且 TF 卡 swap 有磨损与性能代价，
     由用户决策后再执行。

如果运行时不自动解析技能相对路径，使用 `{baseDir}` 占位符：

```
{baseDir}/scripts/audit.sh
{baseDir}/scripts/reclaim_verify.sh --apply
```

## Output contract for audit.sh

```json
{
  "label": "baseline",
  "timestamp": "2026-07-26T15:00:00+08:00",
  "memory_kb": { "total": 4045884, "available": 2837520, "cached": 812340, "buffers": 40210 },
  "cma_kb": { "total": 262144, "free": 180224 },
  "swap_kb": { "total": 0, "free": 0 },
  "top_rss": [ { "pid": 4321, "cmd": "python3", "rss_kb": 512000 } ]
}
```

`reclaim_verify.sh --apply` 额外输出：

```json
{ "before_available_kb": 2837520, "after_available_kb": 3122040, "reclaimed_kb": 284520 }
```

## Limitations

- `drop_caches` 只回收 page cache / dentry / inode，**不会**回收 CMA/ION 中被驱动或
  模型持有的内存；CMA 占用需要定位持有进程后交由用户决定是否关停。
- 非 root 运行时 `reclaim_verify.sh --apply` 会失败并明确报错，不要静默降级。
- 不得根据"经验值"估算可回收内存；一切以脚本 before/after 差值为准。

## Error handling

- 写 `/proc/sys/vm/drop_caches` 权限不足时，报告需要 root 并给出 sudo 命令，不要伪造
  after 数据。
- 如果 after 值高于 before（负回收），如实报告——期间可能有进程释放/申请内存，建议复测。

## Safety

默认只读；唯一的变更动作（drop_caches）必须显式 `--apply` 且经用户确认。drop_caches
是内核支持的安全操作，不会导致数据丢失，但会造成短暂的缓存冷启动性能下降。
基于审计结论的进一步动作请交接：

- **rdk-headless-mode** — 关停桌面与非必要服务以释放常驻内存
- **rdk-model-deploy** — 更换更小的模型或单核绑定以降低 CMA 压力

## Cross-platform behavior

全系 RDK 板卡（X3 / X5 / Ultra / S100 / S600）行为一致；CMA 字段依赖内核 `CmaTotal`/`CmaFree`
暴露，缺失时报告 null 并说明。
