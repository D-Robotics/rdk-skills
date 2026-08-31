---
name: rdk-gpio-40pin
description: Use the 40PIN interface on D-Robotics RDK devices with the preinstalled Hobot.GPIO Python library, covering GPIO, I2C, SPI, UART, and PWM wiring and first-run samples. Use when the user wants to light an LED, read a sensor, use serial/I2C/SPI/PWM on the 40PIN header, or asks about pin definitions and voltage levels. Triggers include 点亮 LED, 点灯, GPIO, 40PIN, 引脚定义, 串口, UART, I2C 传感器, PWM, Hobot.GPIO, 3.3V. Do not use for MIPI camera hookup (rdk-camera-setup) or kernel driver development.
version: 1.0.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - gpio
    - 40pin
    - peripherals
  languages:
    - bash
    - python
  data-classification: public
---

# RDK GPIO 40PIN

40PIN 外设接口的使用指引：GPIO / I2C / SPI / UART / PWM。基于官方预置的
`Hobot.GPIO` Python 库与 `03_Basic_Application/01_40pin_user_sample` 官方示例。

## Purpose

帮助用户在 RDK 40PIN 上正确接线并跑通第一个外设程序（点灯、读传感器、串口收发），
引脚定义与 API 用法一律引用官方文档而非记忆。

## When to use

当用户提出以下问题时激活：

- "怎么用 GPIO 点亮一个 LED？"
- "40PIN 的引脚定义 / 哪个脚是 3.3V？"
- "I2C / SPI / UART / PWM 怎么用？"
- "Hobot.GPIO 怎么导入和设置模式？"

**不要**用本技能做 MIPI 摄像头接入（交接 rdk-camera-setup）或驱动开发（指引官方
`07_Advanced_development` 文档）。

## Prerequisites

- 官方系统镜像预置 `Hobot.GPIO` 库（`import Hobot.GPIO as GPIO` 可直接使用）。
- 操作 GPIO 通常需要 root 或 gpio 用户组权限。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/pin_check.sh` | 检查 Hobot.GPIO 可用性、板卡型号与 40PIN 相关设备节点（i2c/spi/tty/pwm），输出 JSON。 | 无 |

## Instructions

1. 运行 `scripts/pin_check.sh` 确认库与设备节点就绪。
2. **引脚定义**：用 rdk-docs-reference 检索
   `01_40pin_user_sample/40pin_define.md`，引用与用户板卡匹配的引脚表（各板卡布局
   不同，禁止凭记忆报引脚号）。
3. **GPIO 示例**（官方用法）：
   ```python
   import Hobot.GPIO as GPIO
   GPIO.setmode(GPIO.BOARD)        # 按 40PIN 物理编号
   GPIO.setup(channel, GPIO.OUT)
   GPIO.output(channel, GPIO.HIGH)
   GPIO.cleanup()
   ```
4. **I2C**：`sudo i2cdetect -y -r <bus>` 先确认设备地址（总线号查引脚定义文档）。
5. **UART / SPI / PWM**：按官方对应示例文档（uart.md / spi.md / pwm.md）操作，
   引用原文命令。
6. 涉及接线的操作提醒用户先断电，确认电平（3.3V）后再上电。

## Reporting guidance

- 引脚号必须注明编号模式（BOARD 物理编号 vs BCM）与出处文档。
- 外设无响应时按顺序排查：接线/电平 → 设备节点存在性（pin_check.sh 输出）→
  权限 → 官方示例能否复现。

## Limitations

- 40PIN 电平为 3.3V，不可直连 5V 外设信号线；本技能不覆盖电平转换电路设计。
- 引脚复用（pinmux）修改属于高级配置，指引 srpi-config 或官方硬件开发文档。

## Error handling

- `import Hobot.GPIO` 失败：确认是官方镜像；报告 Python 版本与报错原文。
- 设备节点缺失：先查官方文档确认该板卡是否支持该外设，不要盲目 modprobe。

## Output contract for pin_check.sh

```json
{
  "board": "rdk-x5",
  "hobot_gpio": true,
  "devices": {
    "i2c": [ "/dev/i2c-0", "/dev/i2c-1" ],
    "spi": [ "/dev/spidev0.0" ],
    "uart": [ "/dev/ttyS1" ],
    "pwm": [ "/sys/class/pwm/pwmchip0" ]
  }
}
```

## Safety

pin_check.sh 只读。GPIO 输出操作会改变引脚电平——接线错误可能损坏外设或板卡，
执行前必须提示用户确认接线与电平。

## Cross-platform behavior

| 板卡 | 40PIN | Hobot.GPIO | 备注 |
| --- | --- | --- | --- |
| RDK X3 / X3 Module | 有 | 预置 | 引脚定义见 40pin_define.md（X3 scope） |
| RDK X5 / X5 Module | 有 | 预置 | 引脚定义见 40pin_define.md（X5 scope） |
| RDK Ultra / S100 / S600 | 见对应硬件手册 | 以实机 import 结果为准 | S 系列另有 MCU 扩展接口（见 rdk_s_doc） |
