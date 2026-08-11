# rdk-embodied-lerobot — Skill Card

## Description:

Deploy a trained embodied-AI policy onto an RDK board — LeRobot ACT imitation policies and Pi0 VLA (openpi) — by exporting to ONNX, compiling to a BPU `.hbm`, and running the on-board control loop that drives a robot arm.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

已有训练好的 ACT 模仿学习策略或 Pi0/openpi VLA 模型，需要导出 ONNX、编译为 BPU `.hbm` 并在 RDK S100/S100P/S600 上运行控制回路驱动机械臂的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 误用 D-Robotics/lerobot fork 替代上游 v0.5.2 导致数据集加载报错；S100 上 Python 3.12 直接 pip install hbm-runtime 会导入失败。
Mitigation: 当前 s100/s600 分支必须使用上游 huggingface/lerobot v0.5.2（fork 仅用于 legacy stable 分支）；S100 需在 Python 3.12 venv 中编译 bundled bpu_runtime/ C++ 扩展。

## Reference(s):

- references/lerobot-workflow.md — ACT 完整命令、bpu_export_config.yaml 字段、双配置 OE 流程、C++ bpu_runtime 构建、Pi0 最小运行表与数据规格、关联仓库列表
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
