# 官方文档 MCP 检索

本目录不包含本地 OE 代码快照或离线手册。此处的说明仅用于定位文档检索入口，不提供可替代当前官方资料的命令、参数、API 或版本结论。

涉及 S 系列 OE 技术事实时，使用当前 Agent 环境提供的文档 MCP：调用 `mcp__rdk_docs__search_docs` 并设置 `manual=oe-s`、`source=docs`，再通过 `mcp__rdk_docs__get_page` 阅读命中的官方页面。

如果 MCP 工具不可用、没有命中相关页面或证据不足，报告缺少的证据并暂停未确认的技术结论。不要回退到本地代码快照、其他版本资料或模型记忆。

更多工作区规则见 [DROBOTICS-S.md](DROBOTICS-S.md)。
