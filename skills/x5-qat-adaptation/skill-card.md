# x5-qat-adaptation — Skill Card

## Description:

Adapts a floating-point PyTorch model into an X5 Plugin QAT model; sets March.BAYES_E, quantization boundaries, quantizable operators, prepare and fake-quant state entry points.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当需要为 X5 Plugin QAT 设置 March.BAYES_E、量化边界、可量化算子、prepare 和 fake-quant 状态入口时，使用本技能将浮点模型适配为 QAT 模型。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 适配时未设置正确的 March 或使用了 eager 路径导致量化语义偏差。
Mitigation: 在模型构建/prepare 前执行 set_march(March.BAYES_E)；优先使用文档推荐的 FX 路径，只有模型确实依赖 eager 时才采用 eager 合同。

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
