# rdk-peripheral-cookbook — Skill Card

## Description:

Hands-on peripheral driving on RDK boards — GPIO/I2C/SPI/UART/PWM, servos, DC/stepper/BLDC motors, LED/WS2812, audio (ALSA), and CAN (X5 SocketCAN vs S100/S600 MCU-domain CANHAL).

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK 板卡上实际驱动外设（点灯、转电机、读传感器、播录音频、CAN 通信）或排查"设备不识别 / 没驱动"问题的开发者与工程师。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: GPIO/I2C/SPI 引脚电平跨板型不统一（X 系列 3.3V，S600 部分 1.8V），误接可能导致硬件损坏。
Mitigation: 接线前必须查询 rdk-hardware 确认当前板型的 IO 电压和引脚定义。

## Reference(s):

- references/gpio-commands.md — GPIO 命令参考
- references/hardware-notes.md — 硬件注意事项
- references/rdk-can-and-board-io.md — CAN 与板载 IO 参考
- Agent Skills（agentskills.dev）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash code blocks]
Output Parameters: [1D]
Other Properties Related to Output: [None]

## Evaluation Agents Used:

- Claude Code (claude-code)

## Evaluation Tasks:

见 evals/tasks.yaml。按五维评测（Security / Correctness / Discoverability / Effectiveness / Efficiency）在 RDK X5 实机环境上执行。

## Evaluation Metrics Used:

- Security: 检查技能辅助执行是否避免不安全行为（密钥泄漏、破坏性命令、越权访问）。
- Correctness: 检查 Agent 是否遵循预期工作流并产出正确的最终结果。
- Discoverability: 检查 Agent 是否在相关时加载技能、在无关时不使用技能。
- Effectiveness: 检查 Agent 使用技能后是否显著优于不使用技能。
- Efficiency: 检查 Agent 是否消耗更少 token、避免冗余操作。

## Evaluation Results:

尚未发布正式基准数据；完成评测后在此登记各维度得分。

## Skill Version(s):

0.1.0 (source: frontmatter)

## Ethical Considerations:

D-Robotics 认为可信 AI 是共同责任。下载或使用本技能时，开发者应与内部团队确认
其满足相关行业与用例的要求，并防范不可预见的产品滥用。
如发现质量、风险或安全漏洞问题，请通过 D-Robotics 开发者社区反馈。
