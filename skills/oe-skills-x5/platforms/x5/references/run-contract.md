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
- `environment.json`：真实探测的工具、Python、文档和板端事实。
- `route.json`：候选 Skill、拒绝理由、主 Skill 和 handoff 顺序。
- `plan.json`：命令、参数、输出目录、副作用、确认点和验证方式。
- `run-state.json`：当前状态、阶段、重试次数、下一步和确认记录。
- `events.ndjson`：按时间追加的机器可读事件。
- `artifacts.json`：产物类型、路径、哈希、来源阶段和验证状态。
- `verification.json`：验证命令、输入、阈值、结果和证据路径。
- `receipt.json`：面向用户和下游 Skill 的最终交接合同。

使用 `scripts/run_contract.py` 管理这些文件，避免各 Skill 自行发明不兼容格式。
