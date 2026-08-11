# rdk-multimedia — Skill Card

## Description:

Drive the RDK board's low-level multimedia hardware pipeline — hardware H.264/H.265/JPEG/MJPEG encode/decode, camera VIN/ISP capture, VPS/PYM scale-crop-rotate, and HDMI/MIPI display — via sp_dev on X3/X5/Ultra or the /app/multimedia_samples + MediaCodec stack on S100/S100P/S600.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK 板上驱动底层多媒体硬件管线（硬件编解码、摄像头采集、缩放裁剪、HDMI/MIPI 显示）且不经过 ROS 层的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 将 X 系列的 HB_VPS_*/HB_VOT_* 代码套用到 S 系列板上，因两套多媒体栈完全不互通导致编译失败或行为异常。
Mitigation: 先确认板族（X3/X5/Ultra vs S100/S100P/S600），再选择对应 API 列；X 系列用 sp_dev/HB_*，S 系列用 Camsys/PYM/GDC + MediaCodec + IDE/IDU。

## Reference(s):

- references/multimedia-pipeline.md — 编解码分辨率/对齐/实例限制、码率模式、VPS 通道表、sp_dev 函数签名、完整 X↔S 单元映射、S100 vs S600 MIPI/CIM/ISP 计数
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
