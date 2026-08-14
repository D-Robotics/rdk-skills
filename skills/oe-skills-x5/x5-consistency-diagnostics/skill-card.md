# x5-consistency-diagnostics — Skill Card

## Description:

Compares X5 floating-point, calibration/QAT, fixed-point, compilation and Runtime outputs on fixed inputs to locate the first numerical or I/O inconsistency stage.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当 Plugin 编译后掉点、仿真与板端不同或 C++/Python 输出不一致时，使用本技能比较各阶段固定输入输出，定位首个数值或 I/O 不一致阶段。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 图像解码/resize/色彩变换在各阶段重复执行且实现不同，引入虚假不一致。
Mitigation: 每个阶段接收的逻辑输入相同；图像解码/resize/色彩变换只执行一次，优先排除输入打包、layout、dtype、量化参数和输出解析错误。

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
