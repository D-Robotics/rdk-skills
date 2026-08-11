# rdk-accessories — Skill Card

## Description:

Bring up D-Robotics official finished accessories — GS130W / GS130Wi binocular depth cameras, the RDK IMU Module (Bosch BMI088), and the RDK S100/S600 Camera & MCU-Port expansion boards — covering selection, wiring, mounting, and driver/SDK bring-up.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要连接或驱动 D-Robotics 官方成品配件（GS130W/Wi 双目相机、RDK IMU 模组、S100/S600 扩展板）的开发者，涵盖接线方向、SDK/IIO 驱动启动与扩展板接口查询。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: GS130W 与 GS130Wi 的 FFC 排线方向相反，带电热插拔可能烧毁器件；扩展板跨系列混插不可通用。
Mitigation: 接线前必须断电并核对型号对应方向；每块扩展板仅适配本系列，安装前确认板卡平行且螺丝均匀固定。

## Reference(s):

- references/accessories-catalog.md — 全规格、22-pin/40-pin/CAN 引脚、IMU SDK 与 IIO 用法、S100/S600 扩展板接口与电源表
- references/imu-sdk-guide.md — rdk-imu-module-sdk 完整 API 参考（C/Python/ROS2）、IIO sysfs 接口、代码示例与故障排查
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
