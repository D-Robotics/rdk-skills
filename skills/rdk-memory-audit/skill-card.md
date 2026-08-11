# rdk-memory-audit — Skill Card

## Description:

Measure DRAM and CMA/ION memory usage on D-Robotics RDK devices and verify
before/after memory reclamation with live audit data.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

在 RDK 上部署模型或多媒体应用前后，需要量化评估内存余量与回收效果的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: `--apply` 会执行 drop_caches，导致短暂的缓存冷启动性能下降。
Mitigation: 默认 dry-run；仅在用户确认后以 root 执行，且操作本身不丢数据。

## Reference(s):

- references/rdk-memory-layout.md — RDK 内存构成参考（源自官方 rdkos_info / FAQ 文档）

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

D-Robotics 认为可信 AI 是共同责任。下载或使用本技能时，开发者应确认其满足相关行业
与用例的要求，并防范不可预见的产品滥用。问题请通过 D-Robotics 开发者社区反馈。
