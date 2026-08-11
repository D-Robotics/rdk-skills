---
name: rdk-network-remote
description: Diagnose and fix network connectivity and remote access on D-Robotics RDK devices — SSH, serial console, VNC, wired/wireless network, and static IP defaults. Use when the user cannot reach the board, ssh or ping fails, WiFi needs configuring, or they ask how to log in without a monitor. Triggers include ssh 连不上, 连不上板子, 网络不通, ping 不通, 串口登录, 波特率, VNC 远程桌面, 静态 IP, 192.168.127.10, WiFi 配置, 无线网络, 有线直连, remote login. Do not use for CPU frequency or thermal settings (rdk-system-config), disabling the desktop (rdk-headless-mode), or web sample display issues (rdk-vision-pipeline).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - network
    - remote-access
    - ssh
  languages:
    - bash
  data-classification: public
---

# RDK Network & Remote Access

RDK 设备的网络连通性与远程访问（SSH / 串口 / VNC）诊断与配置。默认 IP、波特率、
登录方式均以官方 `01_Quick_start/remote_login.md` 与
`02_System_configuration/01_network_blueteeth.md` 为准，见 `references/` 出处标注。

## Purpose

"连不上板子"是一切设备侧工作的前置阻塞。本技能在板端做分层网络自检
（接口 → 链路 → IP → 网关 → DNS → 远程服务），并给出官方文档规定的
串口兜底登录路径与静态 IP 默认值，帮助用户恢复远程访问。

## When to use

当用户提出以下问题时激活：

- "ssh 连不上开发板了。"
- "板子 ping 不通 / 网络不通。"
- "没有显示器怎么登录板子？"
- "WiFi / 有线网络怎么配置？"
- "串口登录用什么波特率？VNC 怎么连？"

**不要**用本技能调 CPU 频率或温控（交接 rdk-system-config）、关闭桌面服务
（交接 rdk-headless-mode）或排查 web 示例出图问题（交接 rdk-vision-pipeline）。

## Prerequisites

- 板端诊断需在 RDK 主机上运行（本技能同时提供 PC 侧排查指引，用于板端完全失联时）。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/net_diag.sh` | 板端分层网络自检：接口/链路/IP/默认路由/网关连通/DNS/SSH 服务状态，输出 JSON。 | `--json`（默认）、`--human`、`--no-ping` |

## Instructions

1. **板端可操作时**：运行 `scripts/net_diag.sh`，按 `first_failed_layer` 定位：
   - `link`：网线/WiFi 未连接 → 检查物理连接或按第 3 步配置 WiFi。
   - `ip`：接口无地址 → 对照官方静态 IP 默认值（见 `references/remote-access.md`），
     有线默认 `192.168.127.10/24`（不同板卡/版本差异见 references 表格）。
   - `gateway` / `dns`：局域网或上游问题 → 引用脚本证据指导用户查网关。
   - `ssh_service`：sshd 未运行 → `sudo systemctl status ssh` 后按状态处理。
2. **板端完全失联时**（用户从 PC 侧提问）：给出官方兜底路径——
   - 串口登录：X3 波特率 921600，X5 波特率 115200，用户名/密码 `root`/`root`
     （官方 remote_login.md）。
   - 有线直连：PC 配静态 IP 与板卡同网段（如 `192.168.127.100`），再 ping
     `192.168.127.10`。
3. **WiFi 配置**：按官方 `01_network_blueteeth.md` 对应板卡章节操作；先用
   rdk-docs-reference 检索并引用原文命令，不同板卡工具（nmcli/wpa_cli）有差异。
4. **VNC**：仅 Desktop 版系统支持；按官方文档用 VNC Viewer 直连板卡 IP。
5. 任何配置变更前先展示 `net_diag.sh` 当前状态，变更后重跑验证。

## Reporting guidance

- 只报告 `net_diag.sh` 实测字段；PC 侧指引须注明"来自官方文档默认值，
  以实机为准"。
- 引用默认 IP 时必须带板卡/系统版本适用范围（见 references 中的官方对照表），
  不要把 X3 旧版的 `192.168.1.10` 说成通用默认值。
- 网关/DNS ping 失败时如实报告 `null`（--no-ping 或命令缺失时），不推断连通性。

## Limitations

- 本技能不修改路由器/交换机侧配置，不处理企业网认证。
- 板端失联场景下只能提供官方文档路径指引，无法实测。
- ping 检测默认单包、2 秒超时；受防火墙影响时结论仅供参考。

## Error handling

- 脚本报 not-an-rdk-host：说明当前 Agent 不在板端，切换到 PC 侧指引路径（第 2 步）。
- `nmcli`/`iwconfig` 缺失：对应字段报 null，不猜测无线状态。
- 修改网络配置有断连风险：变更前明确告知用户，并优先给出可回退的命令。

## Output contract for net_diag.sh

```json
{
  "board": "rdk-x5",
  "interfaces": [
    { "name": "eth0", "state": "UP", "carrier": true, "addrs": [ "192.168.127.10/24" ] },
    { "name": "wlan0", "state": "DOWN", "carrier": false, "addrs": [] }
  ],
  "default_route": { "via": "192.168.127.1", "dev": "eth0" },
  "gateway_ping": true,
  "dns": { "nameservers": [ "8.8.8.8" ], "resolve_ok": true },
  "ssh_service": { "present": true, "active": "active" },
  "first_failed_layer": null
}
```

`first_failed_layer` 按 link → ip → route → gateway → dns → ssh_service 顺序
给出第一个失败层；全部通过为 null。

## Safety

`net_diag.sh` 只读（ping 为单包探测）；任何网络配置变更（WiFi 连接、静态 IP 修改）
均需用户确认后执行，并提前告知断连风险与回退方式。绝不修改 sshd 配置或防火墙规则。

## Cross-platform behavior

| 板卡 | 有线默认静态 IP | 串口波特率 | 备注 |
| --- | --- | --- | --- |
| RDK X3（系统 ≤2.0.0） | 192.168.1.10/24 | 921600 | 官方 remote_login.md 对照表 |
| RDK X3（系统 ≥2.1.0） | 192.168.127.10/24 | 921600 | 同上 |
| RDK X5 | 192.168.127.10/24（USB 网口 192.168.128.10/24） | 115200 | 同上 |
| RDK Ultra / S100 / S600 | 以对应板卡官方文档为准 | 以对应板卡官方文档为准 | 用 rdk-docs-reference 检索 |
