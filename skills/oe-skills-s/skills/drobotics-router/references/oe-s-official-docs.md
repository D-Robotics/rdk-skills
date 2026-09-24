# OE S 系列官方手册依据

本参考记录 PTQ/QAT 默认路径和版本敏感项。在线手册持续更新；执行前按用户 `.drobotics-s/.env.oe-package` 中的实际 `OE_VERSION` 核对本地包和命令帮助，不能把 3.7.0 的参数直接套到其他版本。

## PTQ 优先

- [PTQ、QAT 简介](https://developer.d-robotics.cc/oe_s_doc/guide/faststart/ptq_qat_overview)：官方建议先尝试 PTQ，检查部署精度和性能是否达标。
- [环境部署](https://developer.d-robotics.cc/oe_s_doc/guide/env_install)：建议优先使用 Docker；训练完成后先选简单的 PTQ，只有精度问题确实无法解决时才切换到 QAT。当前在线手册列出的发布包为 `oe-package-3.7.0-s100-s600.tgz`。
- [浮点模型准备（PTQ）](https://developer.d-robotics.cc/oe_s_doc/guide/ptq/ptq_usage/model_prepare)：Caffe 可直接用于 PTQ；PyTorch、TensorFlow、TensorFlow Lite 和 PaddlePaddle 经 ONNX 支持。当前手册列出 ONNX `opset` 10–19、`ir_version` ≤ 9。ONNX 模型应先验证与原始框架推理结果一致。
- [PTQ + 上板快速上手](https://developer.d-robotics.cc/oe_s_doc/guide/faststart/ptq_quickstart)：推荐先检查模型，再准备与模型推理前处理一致的校准数据并执行量化编译；仅做性能快速验证时可不提供校准集。

## 工具流程

- [hb_config_generator](https://developer.d-robotics.cc/oe_s_doc/guide/ptq/ptq_tool/hb_config_generator)：官方 YAML 生成工具，支持最简配置和包含默认值的配置。使用全参数配置前要核对每个值与实际模型、目标平台匹配。
- [hb_compile 工具](https://developer.d-robotics.cc/oe_s_doc/guide/ptq/ptq_tool/hb_compile)：覆盖模型检查、浮点模型量化编译、HBIR 修改和编译。
- [模型量化编译](https://developer.d-robotics.cc/oe_s_doc/guide/ptq/ptq_tool/hb_compile/convert)：配置模式使用 YAML；fast-perf 用于快速性能评测，有不同的参数约束。用已安装包中的 `hb_compile --help` 和对应版本手册确认参数。
- [模型部署环境](https://developer.d-robotics.cc/oe_s_doc/guide/env_install)：当前手册建议 Ubuntu 22.04、Python 3.10，并列出 OE 3.7.0 的安装要求。具体以已安装包版本为准。

## 产品名称与工具标识

面向用户的产品名称使用 RDK S100、S100P、S600。配置中 `march` 仍使用工具链支持列表里的 `nash-*` 值；Python 包和模块（例如 `horizon_tc_ui`、`horizon_plugin_pytorch`）、镜像仓库及服务 URL 也保留实际名称。当前 Docker 检测指引使用在开发机核验过的 S100/S600 v3.7.0 镜像，不替换成猜测出来的包名或 march。
