# x5-runtime-deploy — Skill Card

## Description:

Orchestrates X5 Runtime model gating, board upload, CLI/C++ inference, correctness, performance and resource verification; runs X5 .bin with hrt_model_exec or BPU SDK.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当用户要上板运行 X5 .bin、使用 hrt_model_exec 或 BPU SDK 进行推理、正确性、性能与资源验证时，使用本技能编排 Runtime 部署闭环。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Plugin .hbm/.hbir 未经验证直接送入 .bin API，导致 Runtime 崩溃或结果错误。
Mitigation: 当前 Runtime 手册主路径是 X5 .bin；Plugin .hbm/.hbir 不得未经验证直接送入 .bin API，需先用 hb_model_info 证明 BPU march: bayes-e。

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
