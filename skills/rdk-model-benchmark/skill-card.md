# rdk-model-benchmark — Skill Card

## Description:

Emit structured latency/FPS benchmark metrics for .bin quantized models on
D-Robotics RDK devices using the official hrt_model_exec perf tool.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK 板端量化评估模型推理延迟、极限帧率与算子级瓶颈的算法与部署工程师。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 长时间高负载评测会推高板卡温度，可能触发温控降频使结果失真。
Mitigation: 报告时注明温度状态；建议配合 rdk-diagnostic 监控，必要时降温复测。

## Reference(s):

- references/hrt-model-exec.md — hrt_model_exec 工具参考（含官方文档出处）

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

D-Robotics 认为可信 AI 是共同责任。基准数据仅代表特定环境下的实测结果，对外发布时
应注明运行条件。问题请通过 D-Robotics 开发者社区反馈。
