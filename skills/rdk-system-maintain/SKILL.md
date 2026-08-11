---
name: rdk-system-maintain
description: Keep the D-Robotics RDK OS healthy over time — repair apt sources (sunrise.list / archive.d-robotics.cc), fix apt update failures and lock errors, guide system upgrades against Release Notes, expand the TF-card filesystem, and clean up disk space. Use when apt update fails, the source domain cannot be resolved, disk is full, or the user asks how to upgrade RDK OS. Triggers include apt update 失败, 换源, 软件源, 版本升级, 升级新版本, sunrise.list, Could not resolve, apt 锁, 磁盘满了, 空间不足, 扩容, Expand Filesystem. Do not use for flashing a new image (install_os docs via rdk-docs-reference), memory measurement (rdk-memory-audit), or network-layer failures (rdk-network-remote).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - maintenance
    - apt
    - storage
  languages:
    - bash
  data-classification: public
---

# RDK System Maintain

RDK OS 的日常运维：apt 软件源修复、系统升级指引、TF 卡文件系统扩容与磁盘清理。
源配置与升级约束均以官方 FAQ（`08_FAQ/01_hardware_and_system.md` Q10 等）与
`02_System_configuration/02_srpi-config.md` 为准，见 `references/` 出处标注。

## Purpose

设备用久了绕不开"apt 挂了、盘满了、要不要升级"。本技能先做只读体检
（源域名是否过期、锁是否被占、磁盘水位），再按官方 FAQ 的确定性步骤修复，
避免用户在过期域名和锁文件上浪费时间或误删包管理状态。

## When to use

当用户提出以下问题时激活：

- "apt update 失败 / 报 Could not resolve。"
- "软件源怎么换成新的？sunrise.list 里该写什么？"
- "系统怎么升级到新版本？"
- "磁盘满了 / 空间不足，怎么清理？"
- "TF 卡换大了，文件系统怎么扩容？"

**不要**用本技能烧录系统镜像（属 install_os 文档，交接 rdk-docs-reference）、
测量内存（交接 rdk-memory-audit）或排查网络不通（交接 rdk-network-remote——
域名解析失败先确认 DNS 层是否正常）。

## Prerequisites

- 修复类操作需要 root；只读体检不需要。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/maintain_check.sh` | 只读体检：apt 源域名有效性、GPG key 存在性、apt/dpkg 锁占用、各挂载点磁盘水位、大目录候选，输出 JSON。 | `--json`（默认）、`--human` |

## Instructions

1. 运行 `scripts/maintain_check.sh` 获取体检结果。
2. **apt 源过期域名**（`apt_sources.stale_domains` 非空）：按官方 FAQ Q10 修复——
   ```bash
   sudo sed -i 's/archive.sunrisepi.tech/archive.d-robotics.cc/g' /etc/apt/sources.list.d/sunrise.list
   sudo wget -O /usr/share/keyrings/sunrise.gpg http://archive.d-robotics.cc/keys/sunrise.gpg
   sudo apt update
   ```
   正确的源行见 `references/apt-maintenance.md`（按板卡区分 ubuntu-rdk /
   ubuntu-rdk-x5 / ubuntu-rdk-s100）。
3. **apt 锁被占**（`apt_lock.held: true`）：按官方 FAQ 顺序处理——先等待后台
   自动更新结束或重启；清理锁文件是官方标注"谨慎操作"的最后手段，必须先确认
   无 apt/dpkg 进程再让用户明示确认。
4. **系统升级**：官方约束——1.x 系统**无法**通过 apt 升级到 2.x 及以上，必须
   重新烧录镜像；同大版本内 `sudo apt update && sudo apt upgrade`。升级前用
   rdk-docs-reference 检索对应板卡 Release Note 确认版本配套。
5. **磁盘清理**：引用 `disk` 与 `large_dirs` 字段点名占用大头；清理动作
   （apt clean、删除用户数据）逐条列出并经用户确认，绝不批量 rm。
6. **文件系统扩容**：指引 `sudo srpi-config` → Advanced Options →
   Expand Filesystem（官方步骤，适用 X3/X5 系；重启生效）。

## Reporting guidance

- 只报告 `maintain_check.sh` 实测字段；源修复命令必须注明来自官方 FAQ Q10。
- 报告磁盘水位时引用具体 `mount` 与 `used_pct`，超过 90% 明确标注风险。
- 升级建议必须先声明官方的 1.x → 2.x 烧录约束，再谈 apt upgrade。

## Limitations

- 本技能不执行系统镜像烧录，不修改分区表。
- `large_dirs` 仅扫描常见可清理目录（apt 缓存、日志），不做全盘 du（避免 IO 冲击）。
- srpi-config 仅适用官方限定板卡（X3 / X5 系）。

## Error handling

- 源域名解析失败但 DNS 层也异常时，先交接 rdk-network-remote 排查网络。
- `apt update` 修复后仍报错：报告原始错误全文并用 rdk-docs-reference 检索 FAQ，
  不要尝试第二来源的镜像站猜测。
- 清理锁文件前必须确认 `apt_lock.holder_pid` 进程已不存在；仍在运行时拒绝清理。

## Output contract for maintain_check.sh

```json
{
  "board": "rdk-x5",
  "apt_sources": {
    "file": "/etc/apt/sources.list.d/sunrise.list",
    "present": true,
    "stale_domains": [ "archive.sunrisepi.tech" ],
    "gpg_key_present": true
  },
  "apt_lock": { "held": false, "holder_pid": null },
  "disk": [ { "mount": "/", "used_pct": 41, "avail_kb": 12345678 } ],
  "large_dirs": [ { "path": "/var/cache/apt", "size_kb": 204800 } ],
  "last_apt_update_epoch": 1753500000
}
```

## Safety

`maintain_check.sh` 只读。所有修复动作（sed 改源、清锁、apt clean、扩容）
均需展示命令、说明后果并经用户确认后执行；清理锁文件按官方"谨慎操作"标注
处理，删除用户文件不在本技能范围内。

## Cross-platform behavior

| 板卡 | 官方源（sunrise.list） | srpi-config 扩容 |
| --- | --- | --- |
| RDK X3 / X3 Module | `http://archive.d-robotics.cc/ubuntu-rdk jammy universe` | 支持 |
| RDK X5 / X5 Module | `http://archive.d-robotics.cc/ubuntu-rdk-x5 jammy universe` | 支持 |
| RDK S100 / S100P | `http://archive.d-robotics.cc/ubuntu-rdk-s100 jammy main` | 不支持（官方限定） |
| RDK Ultra / S600 | 以实机 sunrise.list 与对应官方文档为准 | 不支持（官方限定） |
