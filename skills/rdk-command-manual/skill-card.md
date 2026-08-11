# rdk-command-manual — Skill Card

## Description:

Command-manual lookup for RDK-specific commands (hrut_somstatus, hrut_boardid, hrut_socuid, hrut_ps, rdkos_info, rdk-miniboot-update, rdk-backup, srpi-config, devmem) plus the Linux command appendix (apt/dmesg/ip/scp/tar...) as documented by D-Robotics.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

已知命令名（或片段）需要查询其精确语法、选项/标志、适用板型与官方文档来源的 RDK 开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 同一命令名在不同板型上行为不同（如 hrut_boardid 在 X3 有 g/s 子选项而 X5 仅打印），未先确认板型即复述选项易误导。
Mitigation: 回答前先确认板型（X3/X5/Ultra/S 系列），并提示用户在板上运行 `which <cmd>` 或 `<cmd> -h` 核实后再解释。

## Reference(s):

- references/rdk-commands.md — RDK 专属命令完整语法、选项、板型差异、srpi-config 菜单树、刷写/OTA 指引与源路径
- references/linux-commands.md — Linux 附录命令索引与官方 URL 模式
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
