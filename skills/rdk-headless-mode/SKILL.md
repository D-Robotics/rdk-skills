---
name: rdk-headless-mode
description: Safely and reversibly disable or restore the desktop (lightdm) and non-essential services on D-Robotics RDK devices to free memory and CPU. Use when the user wants to run headless, disable the GUI at boot, stop unnecessary services, or restore the desktop later. Triggers include 关桌面, 关闭桌面, 恢复桌面, 图形界面, 不进桌面, 关服务省内存, lightdm, 无头模式. Never touches ssh or network services. Do not use for CPU frequency or thermal settings (rdk-system-config).
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - headless
    - services
  languages:
    - bash
  data-classification: public
---

# RDK Headless Mode

将 RDK 变为无头边缘节点：安全、可回退地关闭桌面环境与非必要后台服务，
为模型推理释放内存与 CPU。桌面服务名以官方文档为准（Desktop 版为 `lightdm`）。

## Purpose

在用户确认后停用/禁用桌面与候选服务，并用 rdk-memory-audit 风格的 before/after
数据量化收益；所有操作可用同一脚本一键恢复。

## When to use

当用户提出以下问题时激活：

- "把桌面关了，板子只跑推理。"
- "开机不要进图形界面。"
- "之前关了桌面，现在把它恢复回来。"
- "关掉桌面后能省多少内存？"
- "哪些服务可以安全关掉省内存？"
- rdk-diagnostic 报告 `candidate_services` 中 lightdm 处于 active 后的行动步骤。

**不要**关闭 ssh、systemd-networkd/NetworkManager 等会导致失联的服务；本技能的
候选清单里永远不包含它们。

## Prerequisites

- root 权限（systemctl stop/disable 需要）。
- 用户已知晓：关闭 lightdm 后 HDMI 桌面不可用，恢复需重新启用。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/headless.sh` | 列出候选服务现状（默认只读）；`--apply` 停止并禁用；`--revert` 恢复。 | `--apply`、`--revert`、`--now-only`（只 stop 不 disable） |

## Instructions

1. 运行 `scripts/headless.sh` 查看候选服务现状与预计动作（只读）。
2. 向用户复述将关闭的服务清单并确认。
3. 确认后以 root 运行 `scripts/headless.sh --apply`；临时关闭（重启后恢复）用
   `--apply --now-only`。
4. 建议在 apply 前后各跑一次 rdk-memory-audit 的 `audit.sh`，报告实测释放量。
5. 恢复桌面：`scripts/headless.sh --revert`。

## Reporting guidance

- 只报告脚本输出中的服务状态（active/enabled），不要推断未列出的服务。
- 释放收益一律引用 before/after 实测差值，不使用经验数字。
- 官方文档中运行 HDMI 显示示例前也要求 `sudo systemctl stop lightdm`（Desktop 版）；
  向用户解释这属于正常操作路径。

## Candidate services

默认候选（与 rdk-diagnostic 的 candidate_services 一致）：

| 服务 | 作用 | 关闭影响 |
| --- | --- | --- |
| lightdm | 桌面显示管理器（Desktop 版） | HDMI 桌面不可用；SSH 不受影响 |
| cups | 打印服务 | 无打印需求则无影响 |
| bluetooth | 蓝牙 | 不用蓝牙外设则无影响 |
| ModemManager | 蜂窝调制解调器管理 | 无 4G/5G 模块则无影响 |
| avahi-daemon | mDNS 服务发现 | `<hostname>.local` 解析失效 |

## Limitations

- Server 版镜像本身无桌面，lightdm 候选会显示为 not-found，属正常。
- 本技能不卸载软件包，只 stop/disable，保证可逆。

## Error handling

- systemctl 不存在或权限不足时如实报错，不要改用 kill 强杀进程。
- `--revert` 后服务仍未启动时，报告 `systemctl status` 原始输出。

## Output contract for headless.sh

```json
{
  "mode": "dry-run",
  "services": {
    "lightdm": { "active": "active", "enabled": "enabled", "planned": "stop+disable" },
    "cups": { "active": "inactive", "enabled": "disabled", "planned": "none" }
  }
}
```

## Safety

- 默认 dry-run；`--apply` / `--revert` 均需显式传入。
- 永不触碰 ssh 与网络管理服务。
- 全部动作可用 `--revert` 恢复（enable + start）。

## Cross-platform behavior

全系 RDK 板卡一致；差异仅在镜像类型（Desktop 版有 lightdm，Server 版没有），
脚本按 systemctl 实际查询结果处理。
