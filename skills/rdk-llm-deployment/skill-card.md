# rdk-llm-deployment — Skill Card

## Description:

Run on-device LLM / VLM chat and the voice stack (ASR→LLM→TTS, plus the xiaozhi 小智 assistant) on D-Robotics RDK boards. Covers hobot_llamacpp GGUF LLM/VLM on X5/S100, the S600 oellm_runtime SDK path, the legacy hobot_llm on X3, and sensevoice_ros2 + hobot_tts.

This skill is ready for commercial/non-commercial use.

## Owner

D-Robotics

### License/Terms of Use:

Apache-2.0

## Use Case:

需要在 RDK 板上运行端侧大模型对话、VLM 看图问答或搭建完整语音助手（ASR→LLM→TTS，含小智 xiaozhi）的开发者。

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: 在 S600 上误用 hobot_llamacpp 编译（无 S600 构建宏），浪费排障时间；VLM 仅下载 GGUF 而遗漏 ViT 编码器文件导致无法运行。
Mitigation: S600 必须使用 D-Robotics_LLM_S600 SDK 的 oellm_runtime（.hbm, march nash-p）；VLM 需同时下载 ViT 编码器（X5 为 .bin，S100 为 .hbm）与语言 GGUF 两个文件。

## Reference(s):

- references/llm-build-commands.md — 全部 4 个工作流的构建与运行命令速查（hobot_llamacpp、S600 SDK + oellm_server、hobot_llm、sensevoice/hobot_tts/xiaozhi）
- references/llm-voice-stack.md — 每块板完整命令：hobot_llamacpp 运行矩阵、sensevoice/hobot_tts/xiaozhi 配置、oellm_server 参数、S100/S600 基准、模型来源表
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
