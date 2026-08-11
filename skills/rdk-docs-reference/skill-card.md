# rdk-docs-reference — Skill Card

## Description:

Search and quote the official D-Robotics documentation (rdk_x_doc / rdk_s_doc)
to answer any RDK knowledge question with sourced citations instead of memory.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要就 RDK 硬件规格、接口定义、FAQ 报错、系统配置等任意知识性问题获得**带官方出处**
答案的开发者；也是其他工作流技能覆盖不到的长尾问题的兜底入口。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 本地文档克隆过期可能导致引用旧版内容。
Mitigation: 输出始终带出处路径便于核对；建议定期 git pull 更新文档克隆。

## Reference(s):

- references/docs-map.md — 官方文档仓库结构地图与检索技巧

## Skill Output:

Output Type(s): [Analysis, Citations]
Output Format: [file:line matches + quoted markdown excerpts]
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

D-Robotics 认为可信 AI 是共同责任。所有回答必须可追溯到官方文档出处；检索无果时
必须如实告知而非编造。问题请通过 D-Robotics 开发者社区反馈。
