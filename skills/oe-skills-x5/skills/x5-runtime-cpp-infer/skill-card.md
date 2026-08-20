# x5-runtime-cpp-infer — Skill Card

## Description:

Generates or reviews X5 BPU SDK C++ inference projects; implements model loading, tensor memory, hbDNNInfer, output read-back and release from a validated X5 .bin.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当用户有 X5 .bin、I/O 合同和 Runtime SDK，需要实现模型加载、张量内存、hbDNNInfer、输出回读与释放时，使用本技能生成可审阅的 CMake C++ 推理工程。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 将示例中硬编码的 224x224 nv12 输入当作任意模型的通用输入，导致推理结果错误。
Mitigation: 模板只覆盖单输入已对齐 raw tensor；多输入或图像前处理必须按模型 I/O 合同扩展，不得套用硬编码尺寸。

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
