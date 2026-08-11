# rdk-headless-mode — Skill Card

## Description:

Turn a D-Robotics RDK device into a headless edge node by safely and reversibly
disabling the desktop (lightdm) and non-essential background services.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

将 RDK 作为纯推理/边缘节点使用、希望释放桌面与冗余服务占用的内存与 CPU 的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 停用服务改变系统运行状态；错误扩大候选清单可能导致设备失联。
Mitigation: 默认 dry-run + 用户确认；候选清单硬编码且永不包含 ssh/网络服务；
全部动作可用 `--revert` 恢复。

## Reference(s):

- 官方文档中 Desktop 版关闭桌面的既定做法：`sudo systemctl stop lightdm`
  （rdk_x_doc/docs/03_Basic_Application/04_vision/RDK_X5/mipi_camera.md）

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

D-Robotics 认为可信 AI 是共同责任。变更系统服务状态前必须获得设备所有者的明确
确认。问题请通过 D-Robotics 开发者社区反馈。
