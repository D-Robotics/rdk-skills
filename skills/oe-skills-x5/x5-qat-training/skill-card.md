# x5-qat-training — Skill Card

## Description:

Executes X5 Plugin calibration, quantization-aware training, validation and post-convert fixed-point evaluation; produces comparable metrics and checkpoints from an adapted model.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当适配模型已可运行，需要执行 calibration、量化感知训练、validation 和 convert 后定点评测以生成可比较指标与检查点时，使用本技能。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 训练循环引入 HAT Engine/config/callback 或未固定 March，导致不可复现或产物不兼容。
Mitigation: 固定 March.BAYES_E，记录 Plugin/PyTorch/CUDA 版本；训练循环由用户项目/PyTorch 实现，不引入 HAT Engine、config 或 callback。

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
