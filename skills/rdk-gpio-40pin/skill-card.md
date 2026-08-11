# rdk-gpio-40pin — Skill Card

## Description:

Use the 40PIN interface on D-Robotics RDK devices with the preinstalled
Hobot.GPIO Python library, covering GPIO, I2C, SPI, UART, and PWM samples.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK 40PIN 上接入 LED、传感器、串口等外设并跑通首个程序的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 错误接线或电平不匹配（5V 接 3.3V 引脚）可能损坏外设或板卡。
Mitigation: 技能强制要求先查官方引脚定义并提示断电接线；pin_check.sh 本身只读。

## Reference(s):

- rdk_x_doc/docs/03_Basic_Application/01_40pin_user_sample/（40pin_define/gpio/i2c/spi/uart/pwm）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash/python code blocks]
Output Parameters: [1D]
Other Properties Related to Output: [None]

## Evaluation Agents Used:

- Claude Code (claude-code)
- Qoder (qoder)

## Evaluation Tasks:

见 evals/tasks.yaml。

## Evaluation Metrics Used:

Security / Correctness / Discoverability / Effectiveness / Efficiency（五维，
与 rdk-diagnostic 的 skill-card 定义一致）。

## Evaluation Results:

尚未发布正式基准数据。

## Skill Version(s):

0.1.0 (source: frontmatter)

## Ethical Considerations:

D-Robotics 认为可信 AI 是共同责任。涉及硬件接线的指引必须包含安全提示。
问题请通过 D-Robotics 开发者社区反馈。
