# rdk-system-maintain — Skill Card

## Description:

Day-2 maintenance for RDK OS: apt source repair, upgrade guidance against
Release Notes, TF-card filesystem expansion, and disk-space cleanup.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

遇到 apt update 失败、软件源域名过期、磁盘空间不足或需要系统升级/扩容指引的
RDK 设备使用者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 修改软件源、清理 apt 锁文件可能破坏包管理系统状态。
Mitigation: maintain_check.sh 为只读体检；全部修复命令来自官方 FAQ 并需用户
确认；锁文件清理遵循官方"谨慎操作"标注，先确认无 apt/dpkg 进程；不删除用户文件。

## Reference(s):

- references/apt-maintenance.md — 官方源配置、锁处理、升级约束与扩容出处
- Agent Skills（agentskills.dev）

## Skill Output:

Output Type(s): [Analysis, Shell commands]
Output Format: [JSON with inline bash code blocks]
Output Parameters: [1D]
Other Properties Related to Output: [None]

## Evaluation Agents Used:

- Claude Code (claude-code)
- Qoder (qoder)

## Evaluation Tasks:

见 evals/tasks.yaml。按五维评测（Security / Correctness / Discoverability /
Effectiveness / Efficiency）在 RDK X5 实机环境上执行。

## Evaluation Metrics Used:

- Security: 检查技能辅助执行是否避免不安全行为（密钥泄漏、破坏性命令、越权访问）。
- Correctness: 检查 Agent 是否遵循预期工作流并产出正确的最终结果。
- Discoverability: 检查 Agent 是否在相关时加载技能、在无关时不使用技能。
- Effectiveness: 检查 Agent 使用技能后是否显著优于不使用技能。
- Efficiency: 检查 Agent 是否消耗更少 token、避免冗余操作。

## Evaluation Results:

尚未发布正式基准数据；完成 NVSkills-Eval 风格评测后在此登记各维度得分。

## Skill Version(s):

0.1.0 (source: frontmatter)

## Ethical Considerations:

D-Robotics 认为可信 AI 是共同责任。下载或使用本技能时，开发者应与内部团队确认
其满足相关行业与用例的要求，并防范不可预见的产品滥用。
如发现质量、风险或安全漏洞问题，请通过 D-Robotics 开发者社区反馈。
