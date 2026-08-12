# x5-runtime-perf-eval — Skill Card

## Description:

Evaluates model latency, throughput and stability on X5 board; uses hrt_model_exec or ai_benchmark to produce reproducible performance reports after correctness passes.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当功能正确性已通过，需要使用 hrt_model_exec 或 ai_benchmark 在 X5 板端得到可复现的延时、吞吐和稳定性性能报告时，使用本技能。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 在热降频或后台负载未知时直接下性能结论，导致数据不可复现。
Mitigation: 先记录板卡空闲程度、温度、频率和电源模式；性能评测不能替代正确性验证，也不在热降频或后台负载未知时直接下结论。

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
