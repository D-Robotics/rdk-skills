# rdk-ecosystem — Skill Card

## Description:

RDK product-line awareness and buying/selection judgment — which board to buy (X3/X5/Ultra/S100/S100P/S600), whether a given model (YOLO / LLM / VLM) will actually run, how RDK compares to Jetson / Raspberry Pi / RK3588, and where the official ecosystem entry points live.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要选购或对比 RDK 板型（X3/X5/Ultra/S100/S100P/S600）、判断某模型能否在板上实际运行、或横向对比 RDK 与 Jetson/树莓派/RK3588 的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 过度承诺 LLM 能力——告诉用户 X5 能流畅跑 DeepSeek 7B，导致选购决策错误。
Mitigation: 始终引用官方 TPS/fps 基准数据，明确区分"能跑"与"可用"，并将实际部署路由到 rdk-llm-deployment。

## Reference(s):

- references/hardware-notes.md — 全板代定位、跨平台对比表与 LLM/VLM 期望校准详解
- references/official-docs.md — 按主题索引的官方文档/资源入口（入门、Studio、视觉、ROS、工具链、LLM、硬件、生态）
- Agent Skills（agentskills.dev）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash code blocks]
Output Parameters: [1D]
Other Properties Related to Output: [None]

## Evaluation Agents Used:

- Claude Code (claude-code)

## Evaluation Tasks:

见 evals/tasks.yaml。按五维评测（Security / Correctness / Discoverability / Effectiveness / Efficiency）在 RDK X5 实机环境上执行。

## Evaluation Metrics Used:

- Security: 检查技能辅助执行是否避免不安全行为（密钥泄漏、破坏性命令、越权访问）。
- Correctness: 检查 Agent 是否遵循预期工作流并产出正确的最终结果。
- Discoverability: 检查 Agent 是否在相关时加载技能、在无关时不使用技能。
- Effectiveness: 检查 Agent 使用技能后是否显著优于不使用技能。
- Efficiency: 检查 Agent 是否消耗更少 token、避免冗余操作。

## Evaluation Results:

尚未发布正式基准数据；完成评测后在此登记各维度得分。

## Skill Version(s):

0.1.0 (source: frontmatter)

## Ethical Considerations:

D-Robotics 认为可信 AI 是共同责任。下载或使用本技能时，开发者应与内部团队确认
其满足相关行业与用例的要求，并防范不可预见的产品滥用。
如发现质量、风险或安全漏洞问题，请通过 D-Robotics 开发者社区反馈。
