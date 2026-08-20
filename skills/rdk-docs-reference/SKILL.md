---
name: rdk-docs-reference
description: Search and quote official D-Robotics documentation (rdk_x_doc / rdk_s_doc / tros_doc) to answer RDK knowledge questions with sourced citations instead of memory. Use for pin definitions, interface specs, FAQ errors, srpi-config options, config.txt, board differences, release notes, TROS installation and node/application documentation, and as the fallback for any RDK question no workflow skill covers. Triggers include 官方文档, 文档里怎么说, FAQ, 引脚定义在哪查, 接口规格, 支持什么分辨率, S100 和 S600 区别, TROS 节点开发. Do not use as a substitute for live measurement — hand real device state to rdk-diagnostic or rdk-memory-audit.
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - docs
    - reference
    - faq
  languages:
    - bash
  data-classification: public
---

# RDK Docs Reference

RDK 通用知识检索技能：任何不属于其他工作流技能的 RDK 问题（引脚定义、接口规格、
FAQ 报错、版本说明、文档原文出处），都先检索官方文档仓库再回答，输出必须带出处。

## Purpose

把"Agent 凭记忆回答 RDK 问题"降级为"Agent 查官方文档后带出处回答"，保证一切结论
可追溯到 rdk_x_doc / rdk_s_doc / tros_doc 的具体文件。

## When to use

当用户提出以下类型的问题时激活：

- "40PIN 引脚定义是什么？" "X5 的 HDMI 支持什么分辨率？"
- "这个报错在官方 FAQ 里有说法吗？"
- "srpi-config 都能配置什么？" "config.txt 有哪些选项？"
- "S100 和 S600 有什么区别？"
- 其他技能（diagnostic/camera/model 等）覆盖不到的任何 RDK 知识性问题。

**不要**在有专用工作流技能的场景使用本技能替代实操（例如内存审计应交给
rdk-memory-audit 实测，而不是引用文档理论值）。

## Prerequisites

- 本地存在官方文档克隆。默认路径为仓库根的 `.refs/rdk_x_doc`、`.refs/rdk_s_doc` 与
  `.refs/tros_doc`，
  可用环境变量 `RDK_DOCS_ROOT` 指向其他位置。
- 缺失时先获取：`git clone --depth 1 https://github.com/D-Robotics/rdk_x_doc.git`
  （rdk_s_doc、tros_doc 同理）。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/search_docs.sh` | 在官方文档仓库中全文检索关键词，输出 `文件路径:行号:命中行`。 | `--query <kw>`（可多次）、`--repo x\|s\|tros\|all`、`--limit N`、`--summary`（按章节分组统计）、`--toc [--query <kw>]`（按关键词过滤目录） |

## Instructions

1. 从用户问题中提取 1–3 个中文/英文关键词，运行
   `scripts/search_docs.sh --query <关键词>`（多关键词做交集缩小范围）。
2. 用 Read 打开命中最多的 1–2 个文档文件，阅读相关段落。
3. 基于文档原文组织回答，**必须**附带出处（如
   `rdk_x_doc/docs/03_Basic_Application/01_40pin_user_sample/40pin_define.md`）。
4. 板卡差异问题（X3/X5/S100/S600）注意文档中的 `<DocScope products=...>` 标记，
   只引用与用户板卡匹配的段落。
5. `--toc` 可列出文档章节树，用于"官方文档里有没有讲过 X"类问题。

## Search methodology

以下是检索方法协议（与具体板卡无关，适用于任何主题）：

1. **仓库限定优先**：问题涉及具体板卡时，先用 `--repo x` 或 `--repo s` 限定仓库，
   再看 DocScope；TROS 节点/应用文档用 `--repo tros`。禁止用 A 板的命中回答 B 板的问题。
2. **章节即适用性信号**：命中路径的章节段（如 `05_mcu_development` vs
   `02_linux_development`）决定该命中属于哪个子系统。用 `--summary` 看命中的章节
   分布；若某术语只出现在另一个子系统的章节里，不要把它当作 Linux 用户态可用的证据。
3. **器物词失败→功能词重试**：具体实现名（设备节点、命令名、库名）搜不到或命中可疑时，
   改搜上位功能词（如 can0 → CAN，wifi_connect → 网络配置），并用
   `--toc --query <功能词>` 按章节名发现目标文档。
4. **负向问题双向取证**：回答"为什么 X 在这块板上不可用"时，必须同时拿到两份证据：
   （a）目标板文档中 X 缺失或仅属于其他子系统；（b）目标板文档中承担同一功能的
   替代机制章节。只有（a）没有（b）时如实说"未找到替代机制"，不得推断。
5. **跨板对比逐板取证**："各板是否一样"类问题，对每块板卡分别限定检索一次，
   逐行引用出处；禁止用单块板的结果外推全系。

## Reporting guidance

- 回答格式：结论 + 关键原文（引用块）+ 出处路径。
- 检索无命中时如实说明"官方文档未覆盖该主题"，可再用 `--repo all` 或换关键词重试
  一次；仍无结果则明确告知，不得编造。
- 文档与实机行为冲突时，以实机为准并建议向官方反馈文档问题。

## Limitations

- 检索质量取决于本地文档克隆的新鲜度；建议定期 `git pull`。
- 图片内容（引脚图、接线图）无法检索正文，只能给出所在文档链接。

## Error handling

- 文档目录不存在：输出 rdk_x_doc、rdk_s_doc、tros_doc 的获取指引（git clone 命令），不要在无文档时凭记忆回答。
- 关键词过泛导致命中过多：取前 N 条并提示用户缩小范围。

## Output contract for search_docs.sh

```
rdk_x_doc/docs/03_Basic_Application/01_40pin_user_sample/gpio.md:10:开发板预置了 GPIO Python 库 `Hobot.GPIO`...
rdk_x_doc/docs/03_Basic_Application/01_40pin_user_sample/gpio.md:16:>>> import Hobot.GPIO as GPIO
```

## Safety

纯只读检索，不修改任何文件。

## Cross-platform behavior

| 文档仓库 | 覆盖板卡 | `--repo` 取值 |
| --- | --- | --- |
| rdk_x_doc | X3 / X3 Module / X5 / X5 Module / Ultra | `x` |
| rdk_s_doc | S100 / S100P / S600 | `s` |
| tros_doc | TROS 安装、环境、节点与应用文档 | `tros` |
| 三者 | 全系与 TROS 文档 | `all`（默认） |
