# rdk-model-zoo — Skill Card

## Description:

Run a ready-made, officially pre-compiled BPU model from the RDK Model Zoo on a board — pick the right branch (branch = board), download the matching .bin/.hbm, run the sample, and read the per-board benchmark (latency/FPS/accuracy).

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要使用官方预编译 BPU 模型而非自行量化，或查询"RDK 有没有现成的 YOLO/分类/分割/OCR .bin/.hbm"以及"我的板用哪个分支"的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 克隆错误分支（branch ≠ board）导致模型产物或运行时 API 与硬件不匹配；.bin（X 系列）与 .hbm（S 系列）跨架构不可互换。
Mitigation: 克隆前先确认板型（cat /sys/class/socinfo/board_id），再克隆对应分支；从记忆中复述目录/模型名前先 `ls samples/` 核实实际检出的分支内容。

## Reference(s):

- references/model-zoo-catalog.md — 分支策略、目录结构、格式×运行时表、下载路径、运行检查清单
- references/per-board-model-catalog.md — 每板每模型的已验证基准表（延迟/FPS/精度）与精确分支/示例路径，含 S600 LLM 数值与 S100/S600 示例矩阵
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
