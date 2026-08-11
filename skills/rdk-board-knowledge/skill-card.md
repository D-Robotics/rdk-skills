# rdk-board-knowledge — Skill Card

## Description:

Identify which RDK board you're on, confirm its runtime baseline (SoC/OS/TROS), diagnose common on-board errors (camera, model/BPU, TROS/ROS2, APT/pubkey, GPIO/I2C/serial, power, network), and flash the S-series (S100/S100P/S600) via xburn DFU/Fastboot.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要识别板型、确认运行时基线、排查板上常见故障（摄像头/模型/TROS/GPIO/电源/网络）或为 S100/S100P/S600 刷写系统镜像的开发者与运维人员。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 未确认板型即套用 X5 模板回答，导致包名、TROS 路径与工具链建议全部错误；刷写时选错 product/media 会变砖。
Mitigation: 回答前先以只读身份探测（cat /sys/class/socinfo/board_id）确认板型；刷写前核对 product 与 media（S100=emmc，S600=ufs），并在断电状态拨开关。

## Reference(s):

- references/failure-hints.md — 59 条症状→建议→文档条目（摄像头、模型、TROS、GPIO、电源、网络、音频、S 系列专项）
- references/official-faq.md — 官方 rdk_doc/rdk_s_doc 08_FAQ 问答与 URL
- references/xburn-flashing.md — S100/S100P/S600 刷写全流程（DFU/Fastboot、Xburn 设置、区域烧录、驱动安装、引导链与镜像架构、故障排查）
- references/diagnostic-commands.md — 命令风险分级与板型适用性
- references/hardware-notes.md — 常见开发陷阱与误区→纠正目录
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
