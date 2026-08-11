---
name: rdk-vision-pipeline
description: Bring up and debug the end-to-end vision inference pipeline on D-Robotics RDK devices — camera capture, BPU model inference, and HDMI/Web display output — and locate which stage is broken. Use when the user wants 摄像头跑模型, real-time video inference, web browser preview of detections, or the pipeline runs but shows no image, no boxes, or heavy lag. Triggers include 实时推理, 视频流, 摄像头跑模型, 摄像头实时检测, 端到端, web 展示, 网页看画面, 推流, 画面卡顿, 有画面没有框, web_display, start_nginx. Do not use for single-camera hookup checks (rdk-camera-setup), model file deployment alone (rdk-model-deploy), or pure latency numbers (rdk-model-benchmark).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - vision
    - pipeline
    - inference
  languages:
    - bash
    - python
  data-classification: public
---

# RDK Vision Pipeline

摄像头 → BPU 推理 → HDMI/Web 展示的端到端链路跑通与断点定位。所有示例路径与命令
均来自官方 `03_Basic_Application` 章节（pydev_demo / cdev_demo），见 `references/`
中的出处标注。

## Purpose

用户买 RDK 的核心目的是"摄像头接上、模型跑起来、画面看得到"。本技能把这条链路
拆成可独立验证的阶段（camera / model / bpu / output），逐段检测并精确报告断在
哪一环，然后交接给对应的单点技能修复。

## When to use

当用户提出以下问题时激活：

- "怎么让摄像头实时跑 YOLO / 检测模型？"
- "网页上怎么看摄像头的检测画面？"
- "示例跑起来了但是没有画面 / 有画面没有框。"
- "摄像头实时推理特别卡。"
- "web_display 示例访问不了 / start_nginx 之后没图。"

**不要**用本技能做单独的摄像头接线验证（交接 rdk-camera-setup）、单独的模型文件
部署排错（交接 rdk-model-deploy）或纯基准测试（交接 rdk-model-benchmark）。

## Prerequisites

- 摄像头已通过 rdk-camera-setup 验证出图，或至少已物理连接。
- 官方系统镜像自带 `/app/pydev_demo` 示例与 `/app/model/basic` 预置模型。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/pipeline_check.sh` | 逐段检测 camera / samples / model / bpu / display / web 六个阶段，输出各段 pass/fail 与首个断点的 JSON。 | `--json`（默认）、`--human` |

## Instructions

1. 运行 `scripts/pipeline_check.sh` 获取全链路分段检测结果，先看 `first_broken_stage`。
2. 按断点交接或修复：
   - `camera` 失败 → 交接 rdk-camera-setup（I2C 探测、排线方向）。
   - `model` 失败（预置模型目录缺失）→ 交接 rdk-model-deploy，或按官方示例文档
     从 rdk_model_zoo / hobot_model 获取模型。
   - `bpu` 失败 → 交接 rdk-diagnostic 确认 BPU sysfs 可见性。
   - `display` 与 `web` 都失败 → 无输出端；HDMI 走官方 display_use 文档，Web 走
     第 3 步。
3. **Web 展示链路**（官方 web_display 示例，见 `references/pipeline-stages.md`）：
   进入 `/app/pydev_demo` 下的 web_display 示例目录，先执行 `sudo sh start_nginx.sh`
   再运行示例脚本，浏览器访问 `http://<开发板 IP>`。Desktop 版系统需先
   `sudo systemctl stop lightdm` 才能独占显示/编码资源（官方要求）。
4. **卡顿定位**：链路各段都 pass 但画面卡顿时，把问题转为量化问题——
   运行 rdk-model-benchmark 测该模型单帧延迟；若延迟正常，则瓶颈在前后处理或
   编码/传输段，用 rdk-diagnostic 看 CPU 占用与温度是否降频。
5. 浏览器访问不了开发板 IP 时，先交接 rdk-network-remote 确认网络连通。

## Reporting guidance

- 只报告 `pipeline_check.sh` 输出的字段；`first_broken_stage` 为 null 时明确说
  "链路各段静态检查均通过"，再进入动态运行验证。
- 报告断点时同时给出该段的证据字段（如 camera 段的 `v4l2_devices` 为空）与
  交接建议，不要泛泛说"检查一下摄像头"。
- 引用示例命令时注明来源文档（DocScope：对应板卡的 pydev_demo 章节）。

## Limitations

- 本技能做静态链路检查 + 官方示例运行指引；不修改设备树、不调 ISP、不写自定义
  推理代码。
- `pipeline_check.sh` 验证的是"各段组件就绪"，不能替代实际跑通一次示例的动态验证。
- Web 端口占用检测依赖 `ss`；缺失时报告 `web.port80_listening: null`。

## Error handling

- 脚本报 not-an-rdk-host 时如实报告环境不可见，不得凭记忆假设链路状态。
- 示例运行报 ION/VIO 分配失败 → 交接 rdk-memory-audit 检查 CMA/ION 余量。
- 示例报模型加载失败（march 不匹配等）→ 交接 rdk-model-deploy 的模型排错路径。

## Output contract for pipeline_check.sh

```json
{
  "board": "rdk-x5",
  "stages": {
    "camera":  { "pass": true,  "v4l2_devices": [ "/dev/video0" ] },
    "samples": { "pass": true,  "pydev_demo": true, "web_display_sample": "/app/pydev_demo/09_web_display_camera_sample" },
    "model":   { "pass": true,  "model_dirs": [ "/app/model/basic" ], "hrt_model_exec": true },
    "bpu":     { "pass": true,  "readable": true },
    "display": { "pass": false, "hdmi_connected": false },
    "web":     { "pass": true,  "nginx_present": true, "port80_listening": false }
  },
  "cma_free_kb": 180224,
  "first_broken_stage": null
}
```

`display` 与 `web` 至少一个 pass 即认为输出端可用；`first_broken_stage` 按
camera → samples → model → bpu → output 顺序给出第一个失败段。

## Safety

只读检测 + 官方示例运行指引；唯一的系统级操作是官方要求的临时 `stop lightdm`
（用户确认后执行，结束可 `start lightdm` 恢复）。不修改任何持久配置。

## Cross-platform behavior

| 板卡 | 预置模型目录 | web_display 示例 | 备注 |
| --- | --- | --- | --- |
| RDK X3 / X3 Module | /app/model/basic | pydev_demo web_display 示例 | cdev_demo 提供 C 版链路 |
| RDK X5 / X5 Module | /app/model/basic、/opt/hobot/model/x5/basic | 09_web_display_camera_sample | 官方示例默认模型 yolov5x_672x672_nv12.bin |
| RDK S100 / S600 | /opt/hobot/model/&lt;soc&gt;/basic | 见 rdk_s_doc 对应章节 | 模型为 .hbm/.bin 以实机目录为准 |
