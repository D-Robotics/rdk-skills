# X5 本地手册映射

## 纳入范围

| 能力 | 本地 source |
| --- | --- |
| 环境与版本 | `_sources/oe_mapper/source/env_install/*` |
| PTQ 快速流程 | `_sources/oe_mapper/source/faststart/quickstart.rst.txt` |
| checker/makertbin | `_sources/oe_mapper/source/ptq/ptq_tool/hb_mapper/*` |
| YAML 与校准 | `_sources/oe_mapper/source/ptq/ptq_usage/*`、`hb_mapper_makertbin.rst.txt` |
| 精度与性能 | `_sources/oe_mapper/source/ptq/ptq_tool/accuracy_debug.rst.txt`、`hb_verifier.rst.txt`、`hb_perf.rst.txt` |
| Plugin QAT | `_sources/plugin/source/user_guide/*`、`api_reference/*`、`quick_start/*` |
| Runtime | `_sources/runtime/source/*` |
| 板端 Python | `skills/x5-bpu-python-api/references/x5_bpu_pyapi.md` |

## 排除范围

`_sources/hat/**` 全部不属于当前 Pack。`--platform x5` 检索会在索引层过滤这些页面，Router 和 Skill 也必须继续执行范围门禁。

## 加载原则

1. `SKILL.md` 只保存决策、合同和关键流程。
2. 参数、错误码、完整 API 和长示例按需读取本地 source。
3. 稳定且重复的操作优先使用 Pack scripts；脚本行为必须能追溯到本表中的手册页面。
4. 手册之间冲突时记录冲突，不自行选择“看起来合理”的路径。
