# rdk-source-map — Skill Card

## Description:

Map and disambiguate repositories in the D-Robotics GitHub org — tell the user what a repo is, which layer it belongs to, which board it targets, and how to build an RDK OS image or TROS workspace from source.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要快速定位 D-Robotics GitHub 组织中某个仓库的用途、所属层级、对应板卡，或需要从源码构建 OS 镜像 / TROS 工作仓的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 仓库可能被重命名、归档或迁移，导致分类信息过时。
Mitigation: 以 GitHub API 实时数据为准，定期同步仓库元信息。

## Reference(s):

- references/repo-families.md — 仓库族谱分类
- references/os-image-build.md — OS 镜像源码构建流程
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
