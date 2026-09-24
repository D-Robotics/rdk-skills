# X5 运行合同

每次实际执行创建唯一运行目录：

~~~text
<run-root>/
├─ input.json
├─ environment.json
├─ route.json
├─ plan.json
├─ run-state.json
├─ events.ndjson
├─ artifacts.json
├─ verification.json
├─ receipt.json
└─ logs/
~~~

## 文件职责

- `input.json`：用户输入和不可变推导摘要。
- `environment.json`：真实探测的工具、Python 和板端事实。文档字段标记 `verification: not_checked_by_environment_probe`；probe 不检查本地文档或调用 MCP。
- `route.json`：候选 Skill、拒绝理由、主 Skill 和 handoff 顺序。
- `plan.json`：命令、参数、输出目录、副作用、确认点和验证方式。
- `run-state.json`：当前状态、阶段、重试次数、下一步和确认记录。
- `events.ndjson`：按时间追加的机器可读事件。
- `artifacts.json`：产物类型、路径、哈希、来源阶段和验证状态。
- `verification.json`：验证命令、输入、阈值、结果和证据路径。
- `receipt.json`：面向用户和下游 Skill 的最终交接合同。

使用 `scripts/run_contract.py` 管理这些文件，避免各 Skill 自行发明不兼容格式。

## 官方文档证据

执行或给出具体 X5 OE 命令、参数、API、版本兼容性和流程细节前，按 [官方文档 MCP 检索合同](../../docs/local-document-retrieval.md) 调用 `mcp__rdk_docs__search_docs`，再以 `mcp__rdk_docs__get_page` 读取匹配的官方正文。把查询词、manual ID、页面标题和 URL 写入 `plan.json`；结果或受阻结论记录在 `verification.json` / `receipt.json`。环境探测的 `ready` 只说明目标环境工具检查通过，不能替代这项核验。没有本地 OE 手册不会影响 `ready`。
