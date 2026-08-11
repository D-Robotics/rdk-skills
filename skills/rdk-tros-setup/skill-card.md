# rdk-tros-setup — Skill Card

## Description:

Install, verify, and troubleshoot TogetheROS.Bot (tros.b) on D-Robotics RDK
devices, including environment sourcing and running hobot package examples.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK 上搭建 TogetheROS.Bot 机器人开发环境、跑通 hobot 功能包示例的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 版本不配套的 tros.b 安装可能导致节点无法运行。
Mitigation: tros_check.sh 输出实测状态；安装命令一律引用官方对应板卡文档。

## Reference(s):

- rdk_x_doc/docs/08_FAQ/03_applications_and_examples.md（环境 source 与示例运行约定）

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

D-Robotics 认为可信 AI 是共同责任。安装操作须经用户确认后执行。
问题请通过 D-Robotics 开发者社区反馈。
