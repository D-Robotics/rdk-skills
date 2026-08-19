# x5-ptq-config-authoring — Skill Card

## Description:

Generates and machine-validates X5 OE Mapper PTQ YAML; produces a reviewable march=bayes-e configuration after model pre-check and input/calibration contracts are settled.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当模型预检通过、输入和校准合同已明确，需要得到 march=bayes-e 的可审阅 PTQ YAML 配置时，使用本技能生成并校验配置。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: YAML 中误用 Plugin load/QAT 混用字段、HAT 或 S 系列参数，导致编译失败或产物不可用。
Mitigation: 拒绝 Plugin load/QAT 混用、HAT 和 S 系列字段；march 固定为 bayes-e，生成后通过机器校验确认字段合法性。

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
