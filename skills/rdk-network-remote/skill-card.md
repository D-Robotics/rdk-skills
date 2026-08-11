# rdk-network-remote — Skill Card

## Description:

Layered network connectivity and remote access (SSH / serial / VNC) diagnosis
for D-Robotics RDK devices, with official static-IP and baud-rate defaults.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

无法通过网络访问 RDK 设备、需要配置有线/无线网络、或需要串口/VNC 兜底登录路径的
开发者与工程师。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 网络配置变更可能导致设备断连、无法远程恢复。
Mitigation: net_diag.sh 为只读诊断；任何配置变更均需用户确认、提前告知断连风险
并给出串口兜底登录路径；绝不修改 sshd 配置或防火墙规则。

## Reference(s):

- references/remote-access.md — 官方默认 IP / 波特率 / 登录方式对照与出处
- Agent Skills（agentskills.dev）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash code blocks]
Output Parameters: [1D]
Other Properties Related to Output: [None]

## Evaluation Agents Used:

- Claude Code (claude-code)
- Qoder (qoder)

## Evaluation Tasks:

见 evals/tasks.yaml。按五维评测（Security / Correctness / Discoverability /
Effectiveness / Efficiency）在 RDK X5 实机环境上执行。

## Evaluation Metrics Used:

- Security: 检查技能辅助执行是否避免不安全行为（密钥泄漏、破坏性命令、越权访问）。
- Correctness: 检查 Agent 是否遵循预期工作流并产出正确的最终结果。
- Discoverability: 检查 Agent 是否在相关时加载技能、在无关时不使用技能。
- Effectiveness: 检查 Agent 使用技能后是否显著优于不使用技能。
- Efficiency: 检查 Agent 是否消耗更少 token、避免冗余操作。

## Evaluation Results:

尚未发布正式基准数据；完成 NVSkills-Eval 风格评测后在此登记各维度得分。

## Skill Version(s):

0.1.0 (source: frontmatter)

## Ethical Considerations:

D-Robotics 认为可信 AI 是共同责任。下载或使用本技能时，开发者应与内部团队确认
其满足相关行业与用例的要求，并防范不可预见的产品滥用。
如发现质量、风险或安全漏洞问题，请通过 D-Robotics 开发者社区反馈。
