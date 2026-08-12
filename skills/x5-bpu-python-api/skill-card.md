# x5-bpu-python-api — Skill Card

## Description:

Loads X5 .bin on board via hbm_runtime.HB_HBMRuntime, reads model I/O and runs local Python inference; requires system /etc/version >= 3.5.0 and matching X5 libdnn wheel/DEB.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

当系统 /etc/version 不低于 3.5.0 且已有匹配 X5 libdnn 的本地 wheel/DEB 时，使用本技能在板端加载 .bin 并执行 Python 推理与输出验证。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 从 PyPI 安装同名 S 系列包，导致 ABI 不兼容或推理结果错误。
Mitigation: 禁止安装 PyPI 同名 S 系列包；只使用用户提供的 X5 本地 wheel/DEB 或已登记离线制品，并验证 libdnn 版本匹配。

## Reference(s):

- Agent Skills（agentskills.dev）
- references/x5_bpu_pyapi.md — BPU Python API 参考

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
