---
name: rdk-model-benchmark
description: Emit structured latency/FPS benchmark metrics for quantized models on D-Robotics RDK devices using the official hrt_model_exec perf tool, including a baseline mode with preinstalled models. Use when the user wants to measure inference latency, frame rate, peak FPS, find the optimal thread count, locate slow operators via profiling, or check whether the board performs normally. Triggers include 推理延迟, 帧率, 极限帧率, 能跑多少帧, 性能评测, 性能正常吗, 跑分, 基准测试, 最慢的算子, hrt_model_exec, perf. Do not use for deployment path selection (rdk-model-deploy) or model conversion (hb_mapper toolchain docs).
version: 0.1.0
license: Apache-2.0
metadata:
  author: D-Robotics RDK Team
  tags:
    - rdk
    - benchmark
    - bpu
  languages:
    - bash
  data-classification: public
---

# RDK Model Benchmark

用官方 `hrt_model_exec perf` 工具在 RDK 板端评测 `.bin` 定点模型的推理延迟与极限帧率，
输出结构化指标。参数语义严格对齐官方算法工具链文档（见 references 出处）。

## Purpose

产出可复现的模型性能基准：平均单帧延迟（Average latency）、极限帧率（Frame rate）、
以及可选的逐算子 profile（profiler.log / profiler.csv），用于回答"这个模型在这块板子
上能跑多快"。

## When to use

当用户提出以下问题时激活：

- "这个 .bin 模型在 X5 上能跑多少帧？"
- "帮我测一下模型的推理延迟。"
- "我的板子性能正常吗？跑个基准看看。"
- "怎么找出模型里最慢的算子？"
- "单核和双核跑差多少？"

**不要**用本技能做模型转换/量化（那是开发机侧工具链 `hb_mapper` 的工作，指引用户
查阅官方 `04_toolchain_development` 章节）。

## Prerequisites

- `.bin` 定点模型已拷贝到板上（官方建议放在 `/userdata` 目录）。
- 板上存在 `hrt_model_exec` 工具（官方系统镜像或工具链发布包自带）。

## Available Scripts

| Script | Purpose | Arguments |
| --- | --- | --- |
| `scripts/benchmark.sh` | 包装 `hrt_model_exec perf`，先打印模型信息再按参数评测，输出结构化摘要。 | `--model <path>` 或 `--baseline`、`--core N`、`--threads N`、`--frames N`、`--profile` |

## Instructions

1. 运行 `scripts/benchmark.sh --model /userdata/xxx.bin` 获取默认基准
   （core_id=0 任意核、单线程、200 帧，与官方默认一致）。
2. 用户没有自己的模型、只想知道"板子性能正不正常"时，运行
   `scripts/benchmark.sh --baseline`：脚本自动选用官方预置模型目录
   （`/app/model/basic` 或 `/opt/hobot/model/<soc>/basic`）中的第一个模型，
   输出中 `model_source` 标明来源；结论仅限该模型，不得外推为整机评分。
3. 求极限帧率时，按官方建议逐步调大 `--threads`（取值范围 1–8），报告最优线程数
   与对应 FPS。
4. 需要逐算子耗时时加 `--profile`，分析生成的 `profiler.log`；若 CPU 算子是瓶颈，
   按官方文档建议指引用户查阅算子支持列表确认可否迁移到 BPU。
5. 评测期间可并行运行 rdk-diagnostic 的 `mem_summary.sh --watch` 观察内存与 BPU 占用。

## Reporting guidance

- 只报告 `hrt_model_exec perf` 实际输出的 `Average latency` 与 `Frame rate` 字段值，
  注明线程数、core_id 与帧数三个运行条件。
- core_id 语义（官方定义）：`0` 任意核心、`1` 核心 0、`2` 核心 1；测双核极限帧率
  用 `0`。
- 对比不同配置时用同一模型文件、同一帧数，逐项列表呈现。

## Limitations

- 评测结果受温度与后台负载影响；温度接近温控阈值时应先降温再测，否则注明
  "可能存在降频"。
- `hrt_model_exec` 各版本参数略有差异；脚本失败时报告原始 stderr，不要猜测替代参数。

## Error handling

- 工具不存在时，指引用户检查系统版本或从官方工具链发布包获取，不要用其他工具冒充。
- 模型加载失败（ION 分配失败等）时，交接 rdk-memory-audit 检查内存余量。

## Output contract for benchmark.sh

```json
{
  "model_file": "/userdata/mobilenetv1_224x224_nv12.bin",
  "model_source": "user",
  "running_condition": { "core_id": 0, "thread_num": 1, "frame_count": 200 },
  "perf_result": { "average_latency_ms": 4.003, "fps": 244.2 },
  "profile_path": null
}
```

`model_source` 为 `user` 或 `baseline:<目录>`；--baseline 模式下找不到预置模型时
脚本以 `baseline-model-not-found` 退出，不得用其他文件冒充。

## Safety

只读评测；不修改模型文件，不改系统配置。上游动作（部署选型）见 rdk-model-deploy。

## Cross-platform behavior

| 板卡 | BPU 核数 | 双核极限帧率测法 |
| --- | --- | --- |
| RDK X3 | 2 | `--core 0` + 调大 `--threads` |
| RDK X5 | 1 | 单核，仅调 `--threads` |
| RDK Ultra | 2 | `--core 0` + 调大 `--threads` |
| RDK S100 / S100P | 依配置（Nash-e） | 同上，以 rdk-diagnostic 报告的核数为准；模型为 `.hbm` |
| RDK S600 | 4x Nash core（Nash-p） | 同上；模型为 `.hbm` |
