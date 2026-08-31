---
name: rdk-tros-setup
description: Install, verify, troubleshoot, and run TogetheROS.Bot (tros.b) on D-Robotics RDK devices, including sourcing /opt/tros/setup.bash, running hobot package examples and NodeHub apps (e.g. body detection), and WebSocket browser visualization. Use when the user asks how to install tros, confirm it is installed, run a hobot/NodeHub application, view results in the browser, or hits ros2 package-not-found and environment issues. Triggers include tros 安装, tros 装好了吗, ros2 找不到 package, source setup.bash, hobot 节点, 跑 hobot 应用, 人体检测, websocket 可视化, NodeHub, TogetheROS. Do not use for full-source cross-compilation (dev machine, official FAQ) or for model load failures (rdk-model-deploy).
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - tros
    - ros2
    - robotics
  languages:
    - bash
  data-classification: public
---

# RDK TogetheROS.Bot Setup

TogetheROS.Bot（tros.b）机器人中间件的安装校验、环境配置与示例运行。
环境配置方式以官方 FAQ 为准：`source /opt/tros/setup.bash`。

## Purpose

帮助用户确认 tros.b 已正确安装并能跑通 hobot 功能包示例，定位"命令找不到 /
节点起不来 / 环境变量不对"类问题。

## When to use

当用户提出以下问题时激活：

- "tros 怎么安装 / 怎么确认装好了？"
- "ros2 run 报找不到 package。"
- "hobot 的示例（如 mipi_cam、dnn_node）怎么跑？"
- "人体检测 / NodeHub 应用怎么跑起来？"
- "websocket 可视化页面不显示图像或 AI 结果。"
- "source 了环境还是不行。"

**不要**用本技能编译 tros.b 全量源码（交叉编译属开发机侧，指引官方 FAQ Q8）或
排查纯硬件问题（交接 rdk-diagnostic / rdk-camera-setup）。

## Prerequisites

- RDK OS（Ubuntu 系）；tros.b 通过 apt 安装到 `/opt/tros`。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/tros_check.sh` | 检查 /opt/tros 安装状态、可用发行版目录、ros2 命令与环境变量是否就绪，输出 JSON。 | 无 |

## Instructions

1. 运行 `scripts/tros_check.sh` 获取安装与环境状态。
2. **未安装**：指引按官方文档 apt 安装（用 rdk-docs-reference 检索对应板卡的
   tros 安装章节并引用原文命令，不同板卡/版本包名有差异）。
3. **已安装但命令不可用**：按官方 FAQ 配置环境——
   ```bash
   source /opt/tros/setup.bash
   ```
   该脚本设置 PATH、LD_LIBRARY_PATH、AMENT_PREFIX_PATH 等环境变量；提醒用户每个
   新终端都需 source，或写入 `~/.bashrc`。
4. **跑示例**：按官方文档从 tros.b 安装路径拷贝示例配置文件到工作目录再运行
   （官方 FAQ 明确要求 config 目录含示例模型与回灌图片）。
5. **跑 NodeHub / hobot 应用**（如人体检测）：launch 文件位于
   `/opt/tros/<tros_distro>/share/<package_name>/launch/`（官方 FAQ Q1）；具体
   包名与启动命令按 `references/tros-apps.md` 的流程用 rdk-docs-reference 检索
   对应板卡原文后引用，不凭记忆拼命令。
6. **WebSocket 可视化不显示**：按官方 FAQ Q9 的链路逐段排查（图像发布节点 →
   websocket 节点 → 同局域网 → AI 消息同步）；浏览器访问不了板卡 IP 时交接
   rdk-network-remote。摄像头节点提示“标定数据不存在”属正常现象（FAQ Q8），
   不影响出图。
7. 运行失败时收集：`ros2 pkg list | grep <pkg>`、报错原文、`tros_check.sh` 输出，
   再对照官方 FAQ `03_applications_and_examples.md` 检索同类问题。

## Reporting guidance

- 引用安装/运行命令时注明出处文档与适用板卡（DocScope）。
- 环境问题优先展示 `tros_check.sh` 的 `env_sourced` 字段证据，不要凭猜测让用户
  重装系统。

## Limitations

- tros.b 版本与 RDK OS 版本存在配套关系；跨版本兼容问题以官方 Release Note 为准。
- 本技能不覆盖 ROS2 应用开发教学，只负责环境就绪、示例与 NodeHub 应用跑通。

## Error handling

- apt 安装失败：报告源配置与报错原文，指引官方系统更新 FAQ。
- 节点运行报模型加载失败：交接 rdk-model-deploy 检查模型与板卡架构匹配。

## Output contract for tros_check.sh

```json
{
  "tros_installed": true,
  "tros_root": "/opt/tros",
  "distros": [ "humble" ],
  "ros2_available": true,
  "env_sourced": false,
  "hint": "run: source /opt/tros/setup.bash"
}
```

## Safety

只读检查；安装动作（apt install）需用户确认后由用户或 Agent 显式执行。

## Cross-platform behavior

全系 RDK 板卡支持 tros.b；不同板卡预装与包集合有差异，一律以 `tros_check.sh`
实测输出与官方对应板卡文档为准。
