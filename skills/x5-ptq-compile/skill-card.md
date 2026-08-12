# x5-ptq-compile — Skill Card

## Description:

Executes hb_mapper checker/makertbin on validated X5 YAML and verifies the unique .bin and BPU march; generates bayes-e PTQ artifacts when config and environment are ready.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当配置和环境已就绪、需要生成 bayes-e PTQ 产物时，使用本技能执行已验证 YAML 的 hb_mapper makertbin 并验证唯一 .bin。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 量化配置 YAML 错误可能导致编译产物不可用。
Mitigation: 编译前必须通过 validate_ptq_config.py --check-paths 校验；编译时重新验证 YAML 哈希和 march: bayes-e。

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
