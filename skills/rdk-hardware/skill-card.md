# rdk-hardware — Skill Card

## Description:

The hardware-facts base for RDK boards — the 6-board spec table (X3 / X5 / Ultra / S100 / S100P / S600) plus 40PIN/GPIO, buses (I2C/SPI/UART/PWM), power & LED meaning, display, network/IP, and CAN.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要查询 RDK 板卡硬件事实（引脚/IO 电平、CAN 类型、TOPS/RAM 差异、电源与 LED 颜色、默认 IP、TROS 路径、系统版本）的开发者与工程师。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 硬件规格数据可能随版本更新而过时，且各板型规格不统一（如 S600 无 40PIN、IO 为 1.8V）。
Mitigation: 以官方文档仓库 rdk_x_doc/rdk_s_doc 为准，定期同步；回答前先确认板型，读取该板的对应行，不从记忆中泛化"典型值"。

## Reference(s):

- references/board-specs.md — 每块板的精确数值：RAM / TOPS / 接口数 / 电源 / LED / IO 电平 / 默认 IP / 探测 ID
- references/hardware-notes.md — 板型确认后的子系统深入说明：40PIN、摄像头、总线、CAN、电源、显示、网络、BPU 监控、路径、散热、OS/用户差异
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
