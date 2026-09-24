# X5 官方手册 MCP 映射

## 调用合同

- X5 OE：调用 `mcp__rdk_docs__search_docs`，参数 `manual="oe-x5"`、`source="docs"`；再把命中的官方 URL 传给 `mcp__rdk_docs__get_page` 并读取正文。
- 板端 X5 Python API：使用 `manual="rdk-x"` 搜索并读取页面。页面如包含其他芯片样例，仅可采用明确标注 X5 的内容。
- 下表的 URL 是检索导航和此前通过 MCP `search_docs` + `get_page` 核验过的官方页面。每次执行具体工具链操作仍需重新查询并读取页面，不能用映射表或包内副本替代。
- MCP 不可用、无匹配官方命中、页面读取失败或正文不足以确认确切边界时，停止依赖该细节的操作并报告阻塞。

## 主题映射

| 主题 | 手册 / MCP 查询词 | 已核对的官方页面 |
| --- | --- | --- |
| Docker、host 安装与环境 | `oe-x5`: `X5 OE Docker 环境部署` | [环境部署](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/env_install/env_deploy.html) |
| PTQ/QAT 选择与 PTQ 主流程 | `oe-x5`: `X5 PTQ QAT overview` | [PTQ/QAT 简介](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/faststart/ptq_qat_overview.html)、[PTQ 快速上手](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/faststart/quickstart.html) |
| PTQ 模型检查、编译和模型信息 | `oe-x5`: `X5 hb_mapper checker makertbin hb_model_info` | [checker](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_checker.html)、[makertbin](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/ptq/ptq_tool/hb_mapper/hb_mapper_makertbin.html)、[hb_model_info](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/ptq/ptq_tool/hb_model_info.html) |
| PTQ YAML 与校准数据 | `oe-x5`: `X5 PTQ YAML calibration data` | [校准数据准备](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/ptq/ptq_usage/prepare_calibration_data.html)、[量化编译](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/ptq/ptq_usage/quantize_compile.html) |
| PTQ 精度分析 | `oe-x5`: `X5 accuracy_debug hb_verifier` | [accuracy_debug](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/ptq/ptq_tool/accuracy_debug.html)、[hb_verifier](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/ptq/ptq_tool/hb_verifier.html) |
| Plugin QAT、校准与术语 | `oe-x5`: `X5 Plugin QAT calibration March BAYES_E` | [QAT 指南](https://developer.d-robotics.cc/oe_x5_doc/cn/plugin/source/user_guide/qat.html)、[Calibration 指南](https://developer.d-robotics.cc/oe_x5_doc/cn/plugin/source/user_guide/calibration.html)、[术语](https://developer.d-robotics.cc/oe_x5_doc/cn/plugin/source/terminology/terminology.html) |
| Plugin 编译 API | `oe-x5`: `X5 Plugin check_model compile_model export_hbir` | [编译 API](https://developer.d-robotics.cc/oe_x5_doc/cn/plugin/source/api_reference/apis/compiler.html) |
| Runtime C/C++ 与 BPU SDK | `oe-x5`: `X5 Runtime BPU SDK hbDNN` | [Runtime 开发](https://developer.d-robotics.cc/oe_x5_doc/cn/runtime/source/runtime_dev.html)、[BPU SDK API](https://developer.d-robotics.cc/oe_x5_doc/cn/runtime/source/bpu_sdk_api/bpu_sdk_api.html) |
| 板端推理、性能与系统工具 | `oe-x5`: `X5 hrt_model_exec ai_benchmark hrut_somstatus` | [hrt_model_exec](https://developer.d-robotics.cc/oe_x5_doc/cn/runtime/source/tool_introduction/hrt_model_exec.html)、[AI Benchmark](https://developer.d-robotics.cc/oe_x5_doc/cn/runtime/source/ai_benchmark/ai_benchmark.html)、[辅助工具](https://developer.d-robotics.cc/oe_x5_doc/cn/runtime/source/tool_introduction/auxiliary_tool.html) |
| 性能调优 | `oe-x5`: `X5 OE performance tuning` | [性能调优](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/tune_content/performance_tune.html) |
| 板端 Python API | `rdk-x`: `X5 hbm_runtime HB_HBMRuntime Python API` | [X5 AI Python API](https://developer.d-robotics.cc/rdk_x_doc/Basic_Application/multi_media_sp_dev_api/RDK_X5/pydev_multimedia_api_x5/ai-python-api) |

## 已知版本措辞限制

`rdk-x` 的 Python API 页面把适用范围写为“X5 3.5.0 版本之后”，并提到之后的版本默认安装 `hbm_runtime`。不要将其改写成 `>= 3.5.0`。执行前读取板端 `/etc/version` 并再次通过 MCP 读取最新页面；高于 3.5.0 也仅通过文档静态版本筛查，仍需确认包来源和板端实际导入。版本正好为 3.5.0 时，补充 MCP 页面复核、目标板包来源和实际 `import hbm_runtime` 证据；证据不足时报告阻塞。

## 范围边界

OE 的 `oe-x5` 手册与 `rdk-x` 中明确标注 X5 的 Python API 内容是此 Pack 的官方资料范围。HAT、J5、X3 或 S 系列页面即使出现在搜索结果或示例中，也不能作为 X5 命令、API、版本或运行合同的证据。
