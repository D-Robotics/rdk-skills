# rdk-diagnostic — Skill Card

## Description:

Read-only RDK health snapshot for board identity, memory, BPU, thermal, storage,
services, and top processes on D-Robotics RDK devices.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要以统一、Agent 友好的视角查看 D-Robotics RDK 设备健康状态（身份、内存、BPU、温度、
存储与服务状态）的开发者与工程师。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 技能建议在执行前需人工审阅，错误的指令可能引入误导性的诊断结论。
Mitigation: 部署前审查并扫描技能内容；本技能全部脚本为只读，不修改系统状态。

## Reference(s):

- references/hrut-somstatus-fields.md — hrut_somstatus 字段参考
- references/bpu-sysfs.md — BPU sysfs 节点参考
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
