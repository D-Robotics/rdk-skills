# rdk-board-delegate — Skill Card

## Description:

Deep S-series (S100/S100P/S600) "big-brain / little-brain" heterogeneous development — MCU1 FreeRTOS firmware (build, remoteproc load, IPC, UART, CAN) and the Acore/Linux subsystems unique to S boards (hbmem zero-copy, IPC with real-time core pinning, PCIe, EtherCAT, PTP/gPTP, OTA, VDSP).

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK S100/S100P/S600 上进行 MCU 固件开发、大小脑异构 IPC、EtherCAT/PTP 时间同步、PCIe、OTA 升级或 VDSP 开发的工程师。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: MCU1 固件在 echo stop 后未等待 wfi 即 echo start，会在运行中的代码上重载固件导致跑飞；S100 与 S600 构建参数顺序不同易混淆。
Mitigation: 停机后必须等待系统进入 wfi 模式再重启；严格按板型使用对应参数顺序（S100 = s100 mcu1 gcc，S600 = s600 gcc mcu1）。

## Reference(s):

- references/mcu-development.md — MCU1 固件工具链、构建系统、remoteproc/wfi、IPC、UART/CAN、FreeRTOS 任务与中断规则、S100/S600 差异
- references/s-advanced.md — Acore 侧 S 系列子系统：hbmem 零拷贝、IPC + 实时核绑核、PCIe、EtherCAT、PTP/gPTP、OTA、VDSP
- references/hardware-notes.md — 大小脑设计原理、三域表、X5 与 S100 机器人管线对比、S100/S100P/S600 规格与选购指南
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
