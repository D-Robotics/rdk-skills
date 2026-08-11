# 官方文档仓库结构地图

> 信息来源：`rdk_x_doc` / `rdk_s_doc` 仓库实际目录结构（Docusaurus）。

## 章节 → 主题速查

| 章节 | rdk_x_doc（X 系列） | rdk_s_doc（S 系列） |
| --- | --- | --- |
| 01_Quick_start | 硬件介绍、系统烧录、显示、远程登录 | 硬件介绍（S100/S600）、系统安装、配置向导、RDK Studio |
| 02_System_configuration | 网络/蓝牙、srpi-config、config.txt、**Thermal 与 CPU 频率管理**、自启动 | 同类主题 |
| 03_Basic_Application | **40PIN**（GPIO/I2C/SPI/UART/PWM）、cdev/pydev 示例、视觉、音频、多媒体 API | 同类主题 |
| 04_model_zoo_intro / 04_Algorithm_Application | Model Zoo 概述 | **算法应用（.hbm 模型 Python/C++ 示例）** |
| 06_Application_case | AMR、巡线小车等案例 | 应用案例 |
| 07_Advanced_development | 硬件开发、Linux/驱动开发、多媒体开发、**算法工具链** | 同类主题 + 硬件单元测试 |
| 08_FAQ | 硬件系统/接口/应用示例/系统更新/工具链 FAQ | 同类 FAQ |
| 09_Appendix | Linux 命令手册、**RDK 命令手册**（hrut_*、rdkos_info 等） | 同类手册 |
| 10_Release_Note | 版本说明 | 版本说明 |

## 检索技巧

- 命令类问题 → 先搜 `09_Appendix/rdk-command-manual/`。
- 报错类问题 → 优先 `08_FAQ/`，FAQ 按"硬件系统/接口/应用示例/系统更新/工具链"分文件。
- 板卡差异 → 文档正文用 `<DocScope products="RDK-X5">` 等标记区分产品，引用时必须
  确认 scope 与用户板卡一致。
- 英文文档位于各仓库 `i18n/en/` 下，默认检索中文即可。
