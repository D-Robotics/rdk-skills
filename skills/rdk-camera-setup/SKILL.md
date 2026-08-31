---
name: rdk-camera-setup
description: Detect, connect, and verify MIPI/USB cameras on D-Robotics RDK devices using i2cdetect and official pydev_demo samples. Use when the user connects a camera and wants to confirm it works, gets no image or a black screen, or i2cdetect finds no address. Triggers include 摄像头, MIPI, USB 相机, IMX219, OV5647, IMX477, 出图, 黑屏, 扫不到地址, mipi_cam, /dev/video0. Do not use for sensor driver development or ISP tuning — point to official 07_Advanced_development docs.
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - camera
    - mipi
  languages:
    - bash
    - python
  data-classification: public
---

# RDK Camera Setup

MIPI / USB 摄像头的检测、接入与出图验证。所有命令与总线号均以 D-Robotics 官方文档
（rdk_x_doc / rdk_s_doc）为准，见 `references/` 中的出处标注。

## Purpose

帮助用户确认摄像头硬件被正确识别（I2C 地址可探测、V4L2 设备存在），并用官方示例完成
第一帧出图验证，定位"接了摄像头但没图"类问题。

## When to use

当用户提出以下问题时激活：

- "MIPI 摄像头接上了怎么验证能不能用？"
- "接了 IMX219 / OV5647 / IMX477，怎么确认接好了？"
- "i2cdetect 扫不到摄像头地址。"
- "USB 摄像头在 RDK 上怎么打开？"
- "运行 mipi_camera 示例黑屏 / 报错。"

**不要**用本技能修改设备树或驱动——驱动级问题定位后应指引用户查阅官方
`07_Advanced_development` 文档章节。

## Prerequisites

- 摄像头已按官方指引连接（22pin 排线金属面背对黑色卡扣插入连接器）。
- 官方系统镜像自带 `/app/pydev_demo` 示例目录。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/detect_camera.sh` | 按板卡型号扫描对应 I2C 总线并列出 V4L2 设备，输出 JSON 检测结果。 | `--json`（默认）、`--human` |

## Instructions

1. 运行 `scripts/detect_camera.sh` 获取 I2C 与 V4L2 检测结果。
2. MIPI 摄像头未探测到时，按 `references/camera-verify.md` 中对应板卡的官方步骤
   （X5 需先拉 GPIO 使能再 `i2cdetect`）人工复查。
3. 出图验证：
   - MIPI：运行官方示例 `/app/pydev_demo/08_mipi_camera_sample/02_mipi_camera_dump.py`
     （保存 YUV 文件，无需显示器）。
   - USB：确认 `/dev/video0` 存在后运行 `/app/pydev_demo/07_usb_camera_sample` 示例。
4. 需要 HDMI 可视化且系统为 Desktop 版时，先执行 `sudo systemctl stop lightdm`
   （官方要求），结束后可 `sudo systemctl start lightdm` 恢复。

## Reporting guidance

- 报告 I2C 探测结果时引用脚本输出的 `i2c.detected_addrs`；IMX219 的典型地址是 `0x10`。
- **多路摄像头**：脚本会扫描板卡全部摄像头总线并列出所有 V4L2 设备；逐总线报告
  `detected_addrs`，明确哪个接口上有 sensor、哪个接口空置，不要只报告第一路。
- 未探测到地址时，按官方 FAQ 的排查顺序报告：排线方向 → 总线号是否对应接口 →
  换用官方适配的摄像头型号（IMX219 / OV5647 / IMX477）。
- 不要凭记忆给出总线号；X3 与 X5 不同（见 references），一律以脚本或 references 为准。

## Limitations

- 本技能验证到"官方示例能出图"为止；ISP 调参、自定义 sensor 驱动超出范围。
- I2C 扫描需要 root（`sudo i2cdetect`）；非特权运行时脚本报告 `i2c.readable: false`。

## Error handling

- `i2cdetect` 命令缺失时提示 `sudo apt install i2c-tools`，不要跳过检测直接跑示例。
- 示例运行报 ION/VIO 分配失败时，交接 rdk-memory-audit 检查 ION 内存余量。
- 出图验证通过后，用户想进一步"摄像头实时跑模型看画面"时，交接
  rdk-vision-pipeline 走端到端链路。

## Output contract for detect_camera.sh

```json
{
  "board": "rdk-x5",
  "i2c": {
    "readable": true,
    "buses_scanned": [ 4, 6 ],
    "detected_addrs": { "4": [ "0x10" ], "6": [] }
  },
  "v4l2_devices": [ "/dev/video0" ],
  "pydev_demo_present": true
}
```

## Safety

只读检测 + 官方示例运行；唯一的系统级操作是 X5 上按官方文档拉摄像头使能 GPIO
（`/sys/class/gpio/gpio353|gpio351`），以及用户确认后临时停止 lightdm。

## Cross-platform behavior

| 板卡 | MIPI 检测总线 | 备注 |
| --- | --- | --- |
| RDK X3 / X3 Module | i2c-1 / i2c-2 | `sudo i2cdetect -y -r 1`（官方 FAQ） |
| RDK X5 | i2c-6（mipi_host0，靠网口）/ i2c-4（mipi_host2） | 探测前需按官方步骤拉 GPIO353/GPIO351 使能 |
| RDK S100 / S100P / S600 | i2c-1 / i2c-2（vcon 设备树节点管理 sensor，rdk_s_doc 多媒体开发章节） | 脚本默认扫描 bus 1/2 并如实报告；细节以 rdk_s_doc 为准 |
