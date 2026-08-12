# x5-model-diagnostics — Skill Card

## Description:

Read-only triage of X5 environment, checker, PTQ, QAT, Runtime, accuracy, performance and log issues; locates the first failing stage from a failure receipt and evidence.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当已有 failure receipt、environment.json、日志或中间产物，需要定位首次失败阶段并输出根因假设和最小恢复实验时，使用本技能进行只读分诊。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 将诊断退化为"换参数再跑一次"，掩盖根因并浪费资源。
Mitigation: 诊断不是换参数再跑的别名；从失败收据确定首次失败阶段，输出可证伪的根因假设和最小恢复实验，默认不重跑训练、编译、安装或上传。

## Reference(s):

- Agent Skills（agentskills.dev）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash code blocks]
Output Parameters: [1D]
Other Properties Related to Output: [None]

## Evaluation Agents Used:

- Claude Code (claude-code)

## Evaluation Tasks:

见 platforms/x5/evals/cases.yaml（平台级评测矩阵）。

## Evaluation Metrics Used:

- Security: 检查技能辅助执行是否避免不安全行为。
- Correctness: 检查 Agent 是否遵循预期工作流并产出正确的最终结果。
- Discoverability: 检查 Agent 是否在相关时加载技能、在无关时不使用技能。
- Effectiveness: 检查 Agent 使用技能后是否显著优于不使用技能。
- Efficiency: 检查 Agent 是否消耗更少 token、避免冗余操作。

## Evaluation Results:

尚未发布正式基准数据；完成评测后在此登记各维度得分。

## Skill Version(s):

1.0.0 (source: X5 Pack V2)

## Ethical Considerations:

D-Robotics 认为可信 AI 是共同责任。下载或使用本技能时，开发者应与内部团队确认
其满足相关行业与用例的要求，并防范不可预见的产品滥用。
如发现质量、风险或安全漏洞问题，请通过 D-Robotics 开发者社区反馈。
