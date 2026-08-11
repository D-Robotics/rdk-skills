# rdk-camera-setup — Skill Card

## Description:

Detect, connect, and verify MIPI/USB cameras on D-Robotics RDK devices using
i2cdetect, official pydev_demo samples, and V4L2 tooling.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

在 RDK 上接入 MIPI / USB 摄像头并需要快速验证"硬件识别 → 第一帧出图"链路的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: X5 探测流程会按官方步骤操作摄像头使能 GPIO；lightdm 停止会中断桌面会话。
Mitigation: GPIO 序列完全复刻官方文档；lightdm 操作需用户确认且可逆
（`sudo systemctl start lightdm`）。

## Reference(s):

- references/camera-verify.md — 摄像头检测与出图验证参考（含官方文档出处）

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

D-Robotics 认为可信 AI 是共同责任。摄像头相关应用涉及影像采集，开发者应确保符合
所在地隐私法规。问题请通过 D-Robotics 开发者社区反馈。
