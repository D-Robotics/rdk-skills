---
name: hmct-workflow
description: >
  HMCT 模型转换与 PTQ 量化总入口——对浮点 ONNX/Caffe 的标准 PTQ 流程优先使用 hb_config_generator 生成官方 YAML，再运行 hb_compile -c。
  根据用户意图自动路由：
  (1) 提供了校准数据 → 使用 hb_config_generator 生成官方 YAML 配置，再运行 hb_compile -c 执行标准 PTQ；
  (2) 未提供校准数据 → 使用 hb_compile -m --march 检查模型；
  (3) 用户希望进行精度调优 → 转交 s-hmct-cosine-similarity-tuning SKILL 执行多阶段调优；
  (4) 用户希望进行单项精度 debug 分析（节点灵敏度、数据分布、累积误差等）→ 调用 hmct-debugger CLI 执行对应分析工具。
  当用户提示词中出现 HMCT、模型转换、模型量化、PTQ、hb_compile、YAML 配置、精度调优、cosine similarity、节点灵敏度、数据分布、累积误差、debug 等关键词时应触发此 Skill。
version: 1.0.2
license: Apache-2.0
---

# HMCT 工作流路由

本 Skill 是 HMCT 工具链的统一入口，根据用户意图自动分发到对应子流程。

## 路由规则

```
用户请求
  │
  ├─ 意图：浮点 ONNX/Caffe 模型的 PTQ 量化，且提供了校准数据（cal_data_dir）
  │   └─→ 路由 A：hb_config_generator 生成官方 YAML → hb_compile -c
  │
  ├─ 意图：检查模型能否被工具链处理，当前没有校准数据
  │   └─→ 路由 B：hb_compile -m <model> --march <march>（只检查，不执行 PTQ）
  │
  ├─ 意图：精度调优 / cosine similarity 不达标 / 混精度配置
  │   └─→ 路由 C：精度调优工作流（转交 s-hmct-cosine-similarity-tuning）
  │
  ├─ 意图：单项 debug 分析（灵敏度、分布、累积误差等）
  │   └─→ 路由 D：精度 Debug 工具
  │
  └─ 不确定
      └─→ 询问用户意图后再路由
```

---

## 路由 A：完整量化构建（YAML 驱动，推荐）

**触发条件：** 用户希望执行模型量化转换，且提供了校准数据。

**关键词：** 模型转换、量化构建、PTQ 构建、校准、hb_compile、YAML 配置

**首选官方命令行工作流：`hb_config_generator` 生成 YAML，用户确认配置后运行 `hb_compile -c`。**
标准 PTQ 不调用 `s-hbdk-compile` 中的自定义 `compile_model.py`，也不让 Agent 直接编写 `hbdk4.compiler` API 编译代码。只有用户明确要求 API 级代码，或官方 CLI 无法完成某个已确认的特殊操作时，才转到相应的高级 Skill。

### 工作流

```
Step 1: 收集参数 → Step 2: hb_config_generator 生成 YAML → Step 3: 用户确认 YAML → Step 4: hb_compile -c 编译
```

### 需要收集的参数

#### 必填

| 参数 | 说明 |
|------|------|
| `-m` / `--model` | 输入 ONNX 模型路径；Caffe 模型还需要 `-p` / `--proto` |
| `calibration_parameters.cal_data_dir` | 校准数据目录，填入生成的官方 YAML |

#### 可选参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--march` | 必须依据目标板选择 | S100=`nash-e`，S100P=`nash-m`，S600=`nash-p`；未知时先确认 |
| `input_parameters` | 从模型信息和用户描述核对 | 输入名称、形状、训练/运行格式及前处理参数 |
| `calibration_parameters` | 根据工具链版本与用户需求填写 | 校准数据目录和量化参数；保留生成器的字段结构 |
| `model_parameters.working_dir` | 由用户指定或沿用生成配置 | 编译产物目录 |

### 执行方式

```bash
# Step 1: 生成官方完整 YAML 模板（工具在当前目录生成 full_compile_config.yaml）
hb_config_generator -f -m <模型路径> --march <芯片架构>

# Step 2: 编辑 full_compile_config.yaml
# 将校准数据目录填入 calibration_parameters.cal_data_dir，
# 并按模型和用户信息核对 input_parameters / compiler_parameters。

# Step 3: 用户确认 YAML 配置后运行
hb_compile -c full_compile_config.yaml
```

### YAML 配置示例

```yaml
model_parameters:
  onnx_model: /path/to/model.onnx
  march: nash-e                  # S100；S100P=nash-m；S600=nash-p
  working_dir: ./model_output
  output_model_file_prefix: model
input_parameters:
  input_type_rt: nv12
  input_type_train: bgr
  input_layout_train: NCHW
calibration_parameters:
  cal_data_dir: /path/to/calibration_data
compiler_parameters:
  compile_mode: latency
```

示例只展示官方配置 section 与字段名。实际任务先由 `hb_config_generator -f` 生成当前工具链版本的模板，再按真实模型输入、前处理和校准参数修改；不要用此片段覆盖生成器输出中的其它必需字段。

### 执行步骤

1. 确认浮点模型路径、校准数据目录和目标板；未知目标板时先询问，不默认猜 `march`
2. 运行 `hb_config_generator -f -m <模型路径> --march <march>` 生成完整官方 YAML
3. 编辑生成文件中的 `calibration_parameters.cal_data_dir`，并根据模型信息核对输入配置
4. **向用户展示配置摘要并等待确认**；除非用户已明确要求直接执行，否则此时停下
5. 用户确认后，在同一 OE 环境中运行 `hb_compile -c <生成的 YAML>`
6. 检查 `hb_compile.log` 和目标 HBM 是否生成，再报告路径与结果

### 参考文档

- `hb_config_generator` 命令与配置编写见 `../tc_ui/s-tc-ui/references/tasks/task-yaml-authoring.md`
- `hb_compile` 主流程与验证见 `../tc_ui/s-tc-ui/references/tasks/task-float-to-hbm.md`
- 官方 PTQ 文档：<https://developer.d-robotics.cc/oe_s_doc/guide/ptq/ptq_tool/hb_config_generator>、<https://developer.d-robotics.cc/oe_s_doc/guide/ptq/ptq_usage/quantize_compile>

---

## 路由 B：快速模型检查

**触发条件：** 用户只想检查模型是否可被工具链识别/处理，尚未提供校准数据。这条路由不执行 PTQ 量化。

**关键词：** 验证模型、check_model、快速检查、测试转换、能不能转

### 工作流

```
Step 1: 确认模型路径与 march → Step 2: hb_compile -m 做模型检查 → Step 3: 报告检查结果
```

### 需要收集的参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `-m` / `--model` | 是 | 输入 ONNX/Caffe 模型路径 |
| `--march` | 是 | 目标 BPU 架构，按 S100/S100P/S600 选择 `nash-e/m/p` |

### 执行方式

```bash
# 只检查模型，不运行校准量化
hb_compile -m <模型路径> --march <芯片架构>
```

### 执行步骤

1. 确认模型路径和目标板；march 未知时先询问
2. 执行 `hb_compile -m <模型路径> --march <march>` 做 check
3. 明确说明 check 通过只代表模型检查成功，不代表 PTQ 已完成或 HBM 已产出
4. 若用户实际需要 PTQ，转回路由 A，收集校准数据并生成 YAML

---

## 路由 C：精度调优工作流

**触发条件：** 用户希望对量化后模型进行精度调优，或反馈 cosine similarity 不达标。

**关键词：** 精度调优、cosine similarity、精度不达标、混精度、INT16、敏感节点、node_config、PTQ 调优

### 转交目标

转交至 **s-hmct-cosine-similarity-tuning** Skill 处理。

### 需要收集的参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--onnx_path` | 是 | 输入 ONNX 模型路径 |
| `--cali_data_dir` | 是 | 校准数据目录 |
| `--march` | 否 | BPU 芯片架构，默认 `nash-p` |
| `--work_dir` | 否 | 工作目录，默认 ONNX 所在目录 |
| `--node_config_path` | 否 | 固定节点配置文件 |
| `--num_sample` | 否 | 敏感度分析的 bad case 数量，默认 1 |
| `--progressive_thresholds` | 否 | 渐进阈值列表，默认 `0.99 0.999 0.9999 0.99999` |
| `--calibration_type` | 否 | 激活校准方法，写入 `model_config.activation.calibration_type`；默认不指定（由 HMCT 决定）；可传单值（如 `max`）或多值（如 `max kl`，触发 modelwise search） |
| `--per_channel` | 否 | 激活 per-channel 量化开关，接受 `true/false`（可同时传两个值触发搜索） |
| `--asymmetric` | 否 | 激活非对称量化开关，接受 `true/false`（可同时传两个值触发搜索） |
| `--bias_correction` | 否 | 是否开启权重 bias correction，接受 `true/false` |
| `--bias_correction_num_sample` | 否 | bias correction 样本数（`int >= 1`），仅 `--bias_correction true` 时生效 |
| `--bias_correction_metric` | 否 | bias correction 误差度量，可选 `cosine-similarity`/`mse`/`mae`/`mre`/`sqnr`/`chebyshev` |

### 执行方式

```bash
# 默认（由 HMCT 自动选择校准方法）
python3 HMCT_Skill/s-hmct-cosine-similarity-tuning/script/hmct_precision_tuning.py \
    --onnx_path <模型路径> \
    --cali_data_dir <校准数据目录> \
    --march <芯片架构>

# 显式指定单一校准方法
python3 HMCT_Skill/s-hmct-cosine-similarity-tuning/script/hmct_precision_tuning.py \
    --onnx_path <模型路径> \
    --cali_data_dir <校准数据目录> \
    --calibration_type max

# 多校准方法（HMCT 触发 modelwise search）
python3 HMCT_Skill/s-hmct-cosine-similarity-tuning/script/hmct_precision_tuning.py \
    --onnx_path <模型路径> \
    --cali_data_dir <校准数据目录> \
    --calibration_type max kl
```

### 调优流程概览

```
INT8 基线 → 全 INT16 ─┬─ 达标 → INT8+INT16 渐进回退
                      └─ 未达标 → INT16+dual-int16 ─┬─ 达标 → 渐进回退
                                                    └─ 未达标 → 全 FP16 ─┬─ 达标 → 渐进回退
                                                                         └─ 未达标 → 深层分析
```

### 参考文档

完整调优流程见 [s-hmct-cosine-similarity-tuning/SKILL.md](s-hmct-cosine-similarity-tuning/SKILL.md)

---

## 路由 D：精度 Debug 工具（单项分析）

**触发条件：** 用户希望针对性地运行某一项 debug 分析（如节点灵敏度、数据分布、累积误差），而非完整调优流程。

**关键词：** 节点灵敏度、数据分布、逐通道分布、累积误差、tensor 分析、debug、hmct-debugger

### 可用工具

| 工具 | 说明 | CLI 命令 |
|------|------|----------|
| `get-sensitivity-of-nodes` | 节点灵敏度排序 | `hmct-debugger get-sensitivity-of-nodes` |
| `plot-distribution` | 量化前后数据分布对比 | `hmct-debugger plot-distribution` |
| `get-channelwise-data-distribution` | 逐通道数据分布 | `hmct-debugger get-channelwise-data-distribution` |
| `plot-acc-error` | 逐层累积误差可视化 | `hmct-debugger plot-acc-error` |
| `tensor-analysis` | 张量级详细分析 | `hmct-debugger tensor-analysis` |
| `sensitivity-analysis` | 敏感节点深入分析 | `hmct-debugger sensitivity-analysis` |
| `runall` | 一键运行全部 debug 功能 | `hmct-debugger runall` |

### 需要收集的参数

| 参数 | 必填 | 说明 |
|------|------|------|
| 模型路径 | 是 | 校准后的模型文件路径 |
| 校准数据路径 | 是 | 校准数据路径 |
| 分析目标节点 | 视工具而定 | 部分工具需要指定节点列表 |

### 执行步骤

1. 确认用户需要运行哪项分析工具
2. 确认模型路径和校准数据路径
3. 如果不确定运行哪项，建议先运行 `runall` 一键分析
4. 使用 CLI 命令或 Python API 执行，向用户报告输出路径

### 参考文档

完整参数说明见 [reference/debug_tools.md](reference/debug_tools.md)

---

## 路由判定示例

| 用户输入 | 路由 | 原因 |
|----------|------|------|
| "帮我把 model.onnx 转换为量化模型，校准数据在 ./cali_data" | A | 生成官方 YAML，确认后运行 hb_compile -c |
| "构建时帮我加上 input_dict 做归一化预处理" | A | 需传预处理参数到 YAML |
| "用 quant_config.json 量化这个模型" | A | 按 YAML 配置方式执行 |
| "我想看下这个模型能不能在 nash-e 上跑通" | B | 验证意图，无校准数据 |
| "帮我验证一下 model.onnx 能否转换成功" | B | 验证意图 |
| "用随机数据快速估算模型性能" | `s-tc-ui` fast-perf | 只做性能估算，不冒充 PTQ 量化 |
| "量化后精度下降了，帮我调优" | C | 精度调优意图 |
| "cosine similarity 只有 0.95，怎么提升" | C | 精度不达标 |
| "帮我做混精度配置，把敏感节点设成 INT16" | C | 精度调优意图 |
| "帮我看看哪些节点灵敏度最差" | D | 单项 debug 分析 |
| "画一下 conv1 的数据分布" | D | 单项 debug 分析 |
| "我有个 ONNX 模型想用 HMCT 处理" | 询问 | 意图不明确，需进一步确认 |

---

## 目录结构

```
HMCT_Skill/
├── SKILL.md                                    ← 本文件（路由入口）
├── reference/
│   ├── build_model.md                          ← build_model / check_model 参考文档
│   ├── run_build.py                            ← 旧 HMCT API 示例；仅用户明确要求 API 流程时参考，不作为标准 PTQ 路径
│   └── debug_tools.md                          ← 精度 debug 工具参考文档
└── s-hmct-cosine-similarity-tuning/
    ├── SKILL.md                                ← 精度调优 Skill 定义
    ├── example.md                              ← Prompt 示例
    └── script/
        ├── hmct_precision_tuning.py            ← 主调优脚本（含构建逻辑）
        └── get_sensitivity_of_nodes.py         ← 敏感度分析脚本
```
