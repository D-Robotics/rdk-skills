# rdk-model-deploy — Skill Card

## Description:

Deploy .bin quantized models on D-Robotics RDK devices, choosing between RDK
Model Zoo samples, pydev_demo Python APIs, and hrt_model_exec validation paths.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK 板端从零跑通模型推理、或将既有 .bin 模型集成到应用中的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 部署与板卡 BPU 架构不匹配的模型会导致加载失败或未定义行为。
Mitigation: check_model.sh 强制先做 model_info 解析与架构匹配提示。

## Reference(s):

- references/deploy-paths.md — 模型部署路径参考（含官方文档出处）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash code blocks]
Output Parameters: [1D]
Other Properties Related to Output: [None]

## Evaluation Agents Used:

- Claude Code (claude-code)
- Qoder (qoder)

## Evaluation Tasks:

见 evals/tasks.yaml。

## Evaluation Metrics Used:

Security / Correctness / Discoverability / Effectiveness / Efficiency（五维，
与 rdk-diagnostic 的 skill-card 定义一致）。

## Evaluation Results:

尚未发布正式基准数据。

## Skill Version(s):

0.1.0 (source: frontmatter)

## Ethical Considerations:

D-Robotics 认为可信 AI 是共同责任。部署的模型应经过适当的精度与安全评估。
问题请通过 D-Robotics 开发者社区反馈。
