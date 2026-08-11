# rdk-system-config — Skill Card

## Description:

Configure D-Robotics RDK system settings including CPU performance mode,
thermal trip points, network/WiFi, srpi-config, and boot auto-start services.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要调整 RDK 运行姿态（性能模式、温控、网络、自启动）的开发者；rdk-diagnostic
诊断出降频/频率未拉满后的行动侧入口。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 调高温控 trip point 可能使芯片在更高温度下运行。
Mitigation: 遵守官方约束（降频温度 ≤ 宕机温度 ≤ 105°C）；优先建议改善散热；
所有变更展示 before/after 状态且重启即恢复。

## Reference(s):

- rdk_x_doc/docs/02_System_configuration/04_frequency_management.md（频率与温控）
- rdk_x_doc/docs/02_System_configuration/05_self_start.md（自启动）
- rdk_x_doc/docs/02_System_configuration/01_network_blueteeth.md（网络/蓝牙）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash code blocks]
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

D-Robotics 认为可信 AI 是共同责任。系统配置变更须经设备所有者确认。
问题请通过 D-Robotics 开发者社区反馈。
