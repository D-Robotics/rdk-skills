# Remote Access Defaults — 官方出处

本文件记录 rdk-network-remote 技能所依据的官方文档路径与关键事实。
所有事实均来自本仓库 `.refs/` 下的官方文档克隆，不做二次推断。

## 有线以太网默认静态 IP

- DocScope: `rdk_x_doc/docs/01_Quick_start/remote_login.md`（"网络状态确认"章节对照表）

| 板卡 | 系统版本 | 默认静态 IP |
| --- | --- | --- |
| X3 | ≤ 2.0.0 | 192.168.1.10/24 |
| X3 | ≥ 2.1.0 | 192.168.127.10/24 |
| X5 | 3.0.0（有线） | 192.168.127.10/24 |
| X5 | 3.0.0（USB 网口） | 192.168.128.10/24 |

- 掩码 `255.255.255.0`，网关 `192.168.127.1`（与默认 IP 同段）。
- PC 直连时将 PC 配为同网段静态 IP（文档示例：板卡 `192.168.127.10`、
  PC `192.168.127.100`）。

## 串口登录

- DocScope: `rdk_x_doc/docs/01_Quick_start/remote_login.md`（"串口登录"章节）
- 波特率：RDK X3 `921600`，RDK X5 `115200`。
- 登录账号：用户名 `root`、密码 `root`。

## VNC / SSH

- DocScope: `rdk_x_doc/docs/01_Quick_start/remote_login.md`（"VNC登录"、"SSH登录"章节）
- VNC：面向 Ubuntu Desktop 版系统，使用 VNC Viewer 直连板卡 IP（文档推荐直接连接方式）。
- SSH：支持终端软件与命令行两种方式。

## 网络 / WiFi 配置

- DocScope: `rdk_x_doc/docs/02_System_configuration/01_network_blueteeth.md`
- 不同板卡与系统版本的无线配置工具与步骤存在差异；引用命令前先用
  rdk-docs-reference 检索对应板卡原文。

## S 系列板卡

- DocScope: `rdk_s_doc/docs/01_Quick_start/`（对应章节）
- S100 / S600 的默认 IP 与串口参数以 rdk_s_doc 为准，勿套用 X 系列数值。
