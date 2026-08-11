---
name: rdk-system-config
description: Configure D-Robotics RDK system settings including CPU performance mode (governor), thermal trip points, srpi-config, and boot auto-start services. Use when the user wants max CPU frequency, performance mode, to adjust throttle temperature, or auto-start a program at boot. Triggers include 性能模式, 锁频, 最高频率, 降频温度, 温控, governor, 开机自启动, srpi-config. Do not use to stop desktop or services (rdk-headless-mode), for network/WiFi setup or connectivity issues (rdk-network-remote), or for pure doc questions (rdk-docs-reference).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - system
    - performance
    - config
  languages:
    - bash
  data-classification: public
---

# RDK System Config

RDK 系统配置的行动类技能：CPU 性能模式、温控参数查看、`srpi-config`、
开机自启动。所有命令与默认值均来自官方 `02_System_configuration` 章节。

## Purpose

承接 rdk-diagnostic 的诊断结论（如温控降频、CPU 频率未拉满），执行官方文档规定的
配置动作，并在变更前展示当前状态、变更后验证生效。

## When to use

当用户提出以下问题时激活：

- "把 CPU 锁到最高频率 / 开性能模式。"
- "板子降频了怎么调整温控参数？"
- "程序怎么开机自启动？"
- "srpi-config 怎么用？"

**不要**用本技能停用服务（交接 rdk-headless-mode）、配置网络/WiFi 或排查连通性
（交接 rdk-network-remote），或做纯知识问答（交接 rdk-docs-reference）。

## Prerequisites

- 变更类操作需要 root。
- `srpi-config` 仅适用于 RDK X3 / X5 / X3 Module（官方限定）。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/perf_mode.sh` | 查看/设置 CPU governor 与温控 trip points。默认只读展示；变更需显式子命令。 | `status`（默认）、`performance`、`ondemand` |

## Instructions

1. 任何配置动作前先运行 `scripts/perf_mode.sh status` 展示当前 governor、
   各 policy 频率与温控 trip points。
2. **性能模式**（官方命令）：用户确认后运行 `scripts/perf_mode.sh performance`，
   等价于 `sudo bash -c 'echo performance > /sys/devices/system/cpu/cpufreq/policy0/scaling_governor'`；
   恢复默认用 `ondemand`。注意该设置**重启后失效**，持久化需按官方自启动文档配置。
3. **温控参数**：X3 默认 启动 80°C / 降频 95°C / 宕机 105°C
   （`/sys/devices/virtual/thermal/thermal_zone0/trip_point_{0,1,2}_temp`，单位毫摄氏度）。
   临时调整用 `echo <值> > trip_point_1_temp`；降频温度不得超过宕机温度，宕机温度
   不得超过 105°C（官方约束）。优先建议改善散热而非调高温度点。
4. **网络/WiFi**：属 rdk-network-remote 职责，直接交接（含配置与连通性诊断）。
5. **开机自启动**：按官方 `05_self_start.md` 提供 systemd service 模板，用
   `systemctl status <name>.service` 验证。
6. **srpi-config**：交互式工具，提示用户 `sudo srpi-config` 并说明其适用板卡限制。

## Reporting guidance

- 变更前后各展示一次 `status` 输出，证明配置已生效。
- 引用温控默认值时注明适用板卡（80/95/105°C 为 X3 官方值；其他板卡以实机读数为准）。
- 明确告知哪些设置是临时的（governor、echo 的 trip point），持久化路径是什么。

## Limitations

- governor 与 trip point 的 echo 设置重启后失效。
- 本技能不修改 config.txt / 设备树等启动配置文件——风险高，指引用户按官方文档手工
  操作并核对。

## Error handling

- 写 sysfs 权限不足：给出 sudo 命令，不静默失败。
- 板卡不存在 policy0 之外的 policy 时按实际枚举，不假设核簇布局。

## Output contract for perf_mode.sh status

```json
{
  "policies": [ { "policy": "policy0", "governor": "ondemand", "cur_khz": 1200000, "max_khz": 1800000 } ],
  "thermal": { "boot_c": 80.0, "throttle_c": 95.0, "shutdown_c": 105.0 }
}
```

## Safety

status 只读；`performance`/`ondemand` 是官方文档给出的标准操作、可随时切回；
不涉及不可逆变更。温控点调整仅在用户理解风险并确认后执行。

## Cross-platform behavior

| 板卡 | governor 路径 | srpi-config | 温控默认值 |
| --- | --- | --- | --- |
| RDK X3 / X3 Module | `/sys/devices/system/cpu/cpufreq/policy0/` | 支持 | 80 / 95 / 105 °C |
| RDK X5 | 同上 | 支持 | 以实机 trip_point 读数为准 |
| RDK Ultra / S100 / S600 | 按实机 policy 枚举 | 不支持（官方限定） | 以实机读数为准 |
