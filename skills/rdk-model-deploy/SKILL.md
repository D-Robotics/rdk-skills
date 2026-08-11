---
name: rdk-model-deploy
description: Deploy quantized models on D-Robotics RDK devices (.bin for X series, .hbm for S series) via RDK Model Zoo samples, pydev_demo Python APIs, and hrt_model_exec validation. Use when the user wants to run YOLO, classification, segmentation or any model on RDK, asks where to start, or hits model load failures. Triggers include 部署模型, 跑模型, 模型加载失败, dnn_node 报错, Model Zoo, hobot_dnn, bin 模型, hbm 模型. Do not use for model conversion/quantization (hb_mapper, dev machine) or performance benchmarking (rdk-model-benchmark).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - model
    - deploy
  languages:
    - bash
    - python
  data-classification: public
---

# RDK Model Deploy

在 RDK 板端部署 `.bin` 定点模型的路径选择与验证指引。信息基线为官方文档与
[RDK Model Zoo](https://github.com/D-Robotics/rdk_model_zoo)（官方社区开源仓库）。

## Purpose

帮助用户从"手里有一个模型/一个需求"走到"板上跑通推理"：选择合适的部署路径
（Model Zoo 示例 / pydev_demo Python API / 自研集成），并用官方工具完成模型有效性
验证。

## When to use

当用户提出以下问题时激活：

- "我想在 RDK 上跑 YOLO / 分类 / 分割模型，从哪开始？"
- "Model Zoo 的模型怎么部署到板子上？"
- "这个 .bin 模型怎么在 Python 里调用？"
- "模型加载失败 / dnn_node 跑起来模型加载报错怎么办？"
- "模型部署后怎么确认输出是对的？"

**不要**用本技能做模型量化转换（开发机侧 `hb_mapper` 工具链），也不要评测性能
（交接 rdk-model-benchmark）。

## Prerequisites

- 已有目标板可运行的 `.bin` 模型（来自 Model Zoo 发布物或工具链转换产物），
  或计划直接使用 Model Zoo 收录的模型。
- 模型文件建议放在 `/userdata`（官方建议）。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/check_model.sh` | 部署前检查：模型文件存在性、`hrt_model_exec model_info` 输出、板卡与 BPU 架构匹配提示。 | `--model <path>` |

## Instructions

1. **选路径**：
   - 标准视觉任务（分类/检测/分割/姿态/OCR/多模态）→ 优先
     [RDK Model Zoo](https://github.com/D-Robotics/rdk_model_zoo)，其中提供
     "原始模型 → 定点转换 → 推理运行 → 结果解析 → 示例验证" 的完整参考实现。
   - 快速上手 Python 推理 API → 官方镜像内 `/app/pydev_demo` 示例
     （01 分类、02 检测、06 分割等，含 `hobot_dnn` 用法）。
2. **部署前检查**：运行 `scripts/check_model.sh --model /userdata/xxx.bin`，
   确认模型可被 `hrt_model_exec model_info` 解析且与当前板卡 BPU 架构匹配。
3. **跑通验证**：用所选路径的示例代码执行一次真实输入推理，核对输出 shape 与
   后处理结果。
4. **交接**：性能不达标 → rdk-model-benchmark；内存不足 → rdk-memory-audit。

## Reporting guidance

- 引用 `model_info` 的输入/输出张量信息说明模型接口，不要凭模型文件名推断。
- **BPU 架构不匹配是常见错误**：X3（Bernoulli）与 X5（Bayes-e）的 .bin 模型互不通用；
  S 系列（Nash-e/Nash-p）使用 `.hbm` 格式，与 X 系列 `.bin` 完全不兼容。
  用户拿 X3 模型在 X5 上跑失败时，明确指出需要用对应架构重新转换或下载对应板卡的
  Model Zoo 发布物。
- 给出的 Model Zoo 链接与用户手册链接必须来自官方文档，不要编造仓库路径。

## Limitations

- 本技能不覆盖模型训练与量化调优；精度问题指引用户查阅官方工具链 PTQ 文档。
- Model Zoo 收录模型以仓库实际内容为准，Agent 不应背诵"支持列表"。

## Error handling

- `model_info` 解析失败：报告原始错误，提示检查模型是否为该板卡架构转换的产物；
  按 `references/conversion-failure-triage.md` 的决策表把报错归因到转换侧或
  板端环境，避免用户在错误的一侧反复排查。
- 推理输出全零/乱码：提示检查输入前处理（NV12/RGB 排布、量化系数），指引对照
  Model Zoo 参考实现。
- `ion alloc failed`：交接 rdk-memory-audit。

## Output contract for check_model.sh

```json
{
  "model_file": "/userdata/yolov5s_672x672_nv12.bin",
  "exists": true,
  "board": "rdk-x5",
  "bpu_arch": "bayes-e",
  "model_info_ok": true,
  "notes": [ "verify the .bin was compiled for bayes-e before deploying" ]
}
```

## Safety

只读检查与示例运行；不删除、不覆盖用户模型文件。

## Cross-platform behavior

| 板卡 | BPU 架构 | 模型兼容性 |
| --- | --- | --- |
| RDK X3 | Bernoulli | 仅运行 Bernoulli 架构转换的 .bin |
| RDK X5 | Bayes-e | 仅运行 Bayes-e 架构转换的 .bin |
| RDK Ultra | Bayes | 仅运行 Bayes 架构转换的 .bin |
| RDK S100 / S100P | Nash-e | 仅运行 Nash-e 架构的 `.hbm`（模型名含 `nashe` 标签） |
| RDK S600 | Nash-p | 仅运行 Nash-p 架构的 `.hbm`（模型名含 `nashp` 标签） |

S 系列说明（源自 rdk_s_doc）：模型格式为 `.hbm`，官方预置模型位于
`/opt/hobot/model/`，Model Zoo 发布物按板卡分目录下载
（archive.d-robotics.cc/downloads/rdk_model_zoo/rdk_s100 与 rdk_s600）。
