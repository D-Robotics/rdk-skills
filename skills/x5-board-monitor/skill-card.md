# x5-board-monitor — Skill Card

## Description:

Collects and parses X5 hrut_somstatus, temperature, CPU/BPU/DDR/GPU frequencies, BPU ratio and dmesg evidence; builds board-side resource snapshots for performance correlation.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当需要建立 X5 板端资源快照或关联性能异常时，使用本技能采集并解析 hrut_somstatus、温度、频率、BPU ratio 和 dmesg 证据。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 套用 S 系列 UCP 监控工具，导致命令不可用或数据解读错误。
Mitigation: 手册规定 X5 使用 hrut_somstatus 查看 BPU 使用率；不使用 S 系列 UCP 监控工具，默认只读和有界采样。

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
