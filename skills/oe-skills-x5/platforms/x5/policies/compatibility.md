# X5 兼容性与产物矩阵

## 强制平台映射

| 场景 | X5 正确值 | 禁止值 | 依据 |
| --- | --- | --- | --- |
| OE Mapper CLI/YAML | `bayes-e` | `bayes`、`bernoulli2`、`nash-*` | X5 PTQ 手册 |
| Plugin Python API | `March.BAYES_E` | `March.BAYES` | Plugin 术语表中 X5/J5 映射 |
| PTQ Runtime 模型 | `.bin` | 将 `.hbm` 改后缀伪装为 `.bin` | OE Mapper/Runtime 手册 |
| 板端 Python API | X5 `.bin` + 匹配的 `hbm_runtime` | `.hbm`、PyPI 同名 S 系列包 | X5 Python API 手册 |

## PTQ 与 QAT 是两条合同

### OE Mapper PTQ

- 输入：ONNX，或 Caffe `.caffemodel + .prototxt`。
- 路径：`hb_mapper checker` → YAML → `hb_mapper makertbin`。
- 目标：`march: bayes-e`。
- 主要产物：校准/量化中间 ONNX、性能报告和板端 `.bin`。
- Runtime：按 X5 Runtime 手册使用 `hb_model_info`、`hrt_model_exec`、BPU SDK 或 X5 Python API。

### horizon_plugin_pytorch QAT

- 输入：可训练 PyTorch 模型、数据、基线和 Plugin 版本。
- 目标：模型构建和转换前显式设置 `March.BAYES_E`。
- 路径：模型适配 → calibration → QAT → quantized 验证 → `check_model` → `compile_model` 或 `export_hbir`。
- Plugin Generic Quick Start 使用 `March.BAYES` 作为示例，并明确要求按目标平台替换；该值对应 J5，不能直接复制到 X5。
- Plugin 编译接口使用 `.hbm/.hbir` 名称。它不是 OE Mapper `.bin` 的同义词，也不得自动交给 `hb_mapper makertbin`。
- 在当前 Runtime 发布包中部署 Plugin `.hbm` 前，必须以实际 Runtime 工具/API 和模型信息完成兼容性验证；证据不足时状态为 `blocked`，不得通过改后缀绕过。

## HAT 边界

以下内容明确不属于当前 X5 Pack：

- `hat` Python 包或 Horizon Torch Samples 框架；
- HAT Trainer、HAT config、registry、launcher、callbacks；
- HAT Model Zoo 和示例训练工程；
- `tools/compile_perf.py` 等 HAT 工具。

本地文档中出现 HAT 页面不代表 X5 Pack 支持 HAT。检索结果命中 HAT 时，Router 必须说明超出范围，不得自动迁移 HAT 配置到 Plugin 或 OE Mapper。

## 版本与核验

- 当前手册基线：OE Mapper `v1.2.8 / Python 3.10`。
- 每次发布更新本文件、Pack 版本、Eval 和 smoke 记录。
- Plugin、PyTorch、Runtime、板端镜像和 wheel/DEB 必须来自实际环境探测；Pack 不维护未经探测的隐式默认版本。
