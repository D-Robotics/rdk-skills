# x5-qat-deploy — Skill Card

## Description:

Orchestrates X5 horizon_plugin_pytorch calibration, QAT, fixed-point conversion and Plugin compilation; produces March.BAYES_E .hbm/.hbir with metric closure from a trainable PyTorch model.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当用户有可训练 PyTorch 模型、数据和浮点基线，希望得到 March.BAYES_E 的 .hbm/.hbir 及指标闭环时，使用本技能编排 Plugin QAT 全流程。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 将 Plugin .hbm/.hbir 与 OE Mapper .bin 混用，导致 Runtime 加载失败或后缀伪装。
Mitigation: Plugin .hbm/.hbir 与 OE Mapper .bin 是不同产物，不改后缀、不自动互转；Runtime 兼容性由匹配发布包实测决定。

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
