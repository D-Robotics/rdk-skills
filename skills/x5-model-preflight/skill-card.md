# x5-model-preflight — Skill Card

## Description:

Runs format, input-contract, floating-point reference and hb_mapper checker pre-checks on ONNX/Caffe models for X5 PTQ; determines if a model can enter the bayes-e PTQ pipeline.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当尚未生成正式 YAML、需要判断模型能否进入 bayes-e PTQ 时，使用本技能对模型执行格式、输入合同、浮点参考运行和 checker 预检。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 将 checker 通过误判为最终 YAML 配置下 makertbin 必然成功，忽略后续配置变更风险。
Mitigation: checker 是快速支持性检查，不等于最终 YAML 配置下的 makertbin 结果；预检通过后仍需走配置编写和编译流程。

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
