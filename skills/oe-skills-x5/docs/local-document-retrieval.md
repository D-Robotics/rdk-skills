# 官方文档 MCP 检索

## 适用范围

本 Pack 的路由、Skill、索引和运行合同负责选择流程与记录证据。命令、参数、API、版本门槛、默认行为和工具链细节必须以官方文档 MCP 检索结果及页面正文为准。此流程不依赖机器安装离线文档包。

## 检索合同

1. X5 OE 使用 `mcp__rdk_docs__search_docs`，指定 `manual="oe-x5"`、`source="docs"`，根据目标阶段和具体命令/API/版本构造查询。
2. 只将 `developer.d-robotics.cc` 的官方手册结果作为官方证据。社区论坛可补充经验，但不能证明受支持的命令、API 或版本门槛。
3. 对检索命中的官方 URL 调用 `mcp__rdk_docs__get_page`，从正文确认芯片型号、手册上下文、版本措辞和所需细节。不得仅凭搜索摘要、其他芯片手册、旧输出或本地 Markdown 推断。
4. 执行计划或结果记录查询词、手册 ID、页面标题与 URL；精确版本边界必须按正文原文保留，不将“之后”等表述自行改写成包含边界的比较运算符。
5. 板端 X5 Python API 可在 `rdk-x` 手册检索；页面若包含其他芯片示例，只能使用明确标注 X5 的段落。无法确认目标版本支持时，停止依赖该 API 的操作并报告阻塞。
6. MCP 不可用、无官方命中、页面读取失败或正文无法回答问题时，停止依赖该细节的操作并报告阻塞。不要回退到包内资料作为官方事实。

## 环境探测

`probe_environment.py` 只检查本机/容器工具链和可选板端事实，不调用 MCP。输出的 `documentation.available: null` 与 `verification: "not_checked_by_environment_probe"` 表示文档核验不在探测器职责内；这不降低 Docker 或 host 工具链的环境状态。开始具体操作前，Skill 必须按上述合同单独完成 MCP 核验。

`--docs-root` 仅为兼容旧调用保留并被忽略。`search_local_docs.py` 与 Pack 内离线文档可以作为维护者自选的辅助材料，但不参与路由、ready 判定或发布验证，也不能替代 MCP。

## 手册映射

常见主题、官方 URL 与已核对的范围见 [X5 手册映射](../platforms/x5/references/manual-map.md)。该映射用于构造查询和导航；使用时仍应通过 MCP 搜索并重新读取页面正文。
