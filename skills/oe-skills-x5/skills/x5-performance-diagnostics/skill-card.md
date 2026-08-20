# x5-performance-diagnostics — Skill Card

## Description:

Correlates X5 hb_perf static estimates, Runtime measurements, BPU ratio, temperature/frequency and CPU/I/O overhead to locate performance bottlenecks.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当模型太慢、静态与板端差异大或 BPU 利用率异常时，使用本技能关联静态估计、Runtime 实测、BPU ratio、温度频率和 CPU/I/O 开销以定位性能瓶颈。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 单一平均延时或 BPU ratio 被独立用作根因证据，误导优化方向。
Mitigation: 单一平均延时或 BPU ratio 不能独立证明根因；需区分模型图/编译、Runtime 调度、CPU 前后处理、数据搬运、系统负载和热/频率限制，默认只读不自动改 O3、core、频率或系统进程。

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
