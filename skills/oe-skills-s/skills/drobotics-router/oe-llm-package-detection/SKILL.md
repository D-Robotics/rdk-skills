---
name: oe-llm-package-detection
description: OE-LLM 包环境检测 Skill。当任务涉及 LLM 量化、LLM 压缩、LLM 编译、板端 LLM 推理等 LLM 工具链操作，且 .drobotics-s/.env.oe-llm-package 不存在时触发。自动完成 OE-LLM 包路径定位、版本采集、本地环境匹配检查、GPU Docker 判定，并将结果写入 .env 文件。
version: 1.1.1
license: Apache-2.0
---

# OE-LLM 包环境检测

## 执行方式

> **本 Skill 应通过 subagent 执行。** 主 agent 在前置检查中发现 `.env.oe-llm-package` 缺失或不完整时，应将本文件的完整内容作为 subagent prompt 派发执行。subagent 完成后汇报写入结果（OE-LLM 路径、版本、执行模式），主 agent 读取 `.env.oe-llm-package` 继续后续流程。

## 目标

检测 OE-LLM 包路径、版本及本地环境匹配情况，写入 `.drobotics-s/.env.oe-llm-package`，供后续所有 LLM 工具链任务直接使用。

## 触发条件

任何涉及 LLM 量化、LLM 压缩、LLM 编译、板端 LLM 推理、LLM 精度评估的任务进入 drobotics-router 前，如果 `.drobotics-s/.env.oe-llm-package` 不存在，顶层 Skill 会**中断任务并提示用户**：

> 未检测到 OE-LLM 包环境配置（`.drobotics-s/.env.oe-llm-package`）。请提供 OE-LLM 包路径，或回复"跳过"暂不配置。

- **用户提供路径** → 进入本检测流程
- **用户回复"跳过"** → 记录跳过（仅当次对话有效，下次仍会提示），继续后续任务

**LLM 任务的识别关键词**：LLM、大语言模型、VLM、视觉语言模型、llm_compression、AWQ、GPTQ、RTN、SmoothQuant、LLM 量化、LLM 编译、LLM 推理、oellm、InternVL、Qwen-VL、LLaMA 等。

## 检测流程

### 1. 检查 `.drobotics-s/.env.oe-llm-package` 是否存在

- 文件存在且内容完整（包含 `OE_LLM_DIR`、`OE_LLM_VERSION`、`EXECUTION_MODE` 等字段）→ 直接读取，跳过后续步骤
- 文件不存在或不完整 → 进入步骤 2

### 2. 定位 OE-LLM 包路径

> **S 系列命名说明**：RDK S100/S600 公共资料列出 OE-LLM 开发包，但其下载内容与镜像标识受限；S600 另有独立的 `D-Robotics_LLM_S600` SDK，二者不能混为一谈。公共 S100/S600 文档未公布可据以替换的 OE-LLM Docker 镜像名。因此，下方 `horizon_j6_open_explorer_llm` 路径和 `...llm_j6_gpu` 镜像只作为识别历史包/旧配置的兼容标识，不是对外产品名或新环境默认值。使用实际 OE-LLM 包内 `run_docker.sh` 和其配套手册确认镜像；不要根据 S 系列产品名称自行拼镜像名。

参考：[RDK S100/S600 版本资料](https://developer.d-robotics.cc/rdk_s_doc/Release_Note/s100/v4_0_2)（公共资料说明 OE-LLM 尚未发布，需联系 FAE）；[S600 LLM Toolchain v1.0.5](https://developer.d-robotics.cc/rdk_s_doc/en/Advanced_development/toolchain_development/LLM_Toolchain/rdk_s600/s100_LLM_Toolchain_v1_0_5) 是单独的 SDK 页面。

按优先级查找：

1. **环境变量**：`OE_LLM_DIR`、`OPEN_EXPLORER_LLM_DIR`、`HORIZON_OE_LLM_DIR`
2. **项目配置文件**：`.env`、`.drobotics-s/oe-llm.env`、`CLAUDE.md` 中声明的路径
3. **常见路径探测**：`/open_explorer_llm`、`~/open_explorer_llm`、`/opt/openexplorer_llm`，以及 `/mnt/oe-cli-test/` 下以 `horizon_j6_open_explorer_llm` 开头的历史目录（仅兼容识别）
4. **以上都没有** → 询问用户 OE-LLM 包路径

找到路径后，验证目录中存在 OE-LLM 包的标志性文件（以下至少两个）：

- `run_docker.sh`
- `llm_compression/` 目录
- `runtime/` 目录

注意：OE-LLM 包**没有**标准 OE 包的 `samples/`、`docs/`、`toolchain/` 目录，也没有 `package/host/ai_toolchain/` 子目录。

### 3. 采集 OE-LLM 版本信息

从 OE-LLM 包目录中提取以下信息：

**OE-LLM 包整体版本**：
- 优先检查包内 `README-CN`、`README-EN`、发布说明和 `llm_compression/deps_version.conf`
- 目录名只能作为线索；尤其不要把历史 `horizon_j6_open_explorer_llm_...` 目录中的版本当作当前 S 系列发布版本
- 以上都无法确定时询问用户

**组件版本**（从 `llm_compression/deps_version.conf` 解析）：

| 字段 | 含义 | 示例值 |
|------|------|--------|
| `HBDK_VERSION` | HBDK4 编译器版本 | 4.11.2 |
| `HORIZON_PLUGIN_PYTORCH_VERSION` | PyTorch 量化插件版本 | 3.3.4 |
| `HBM_INFER_VERSION` | HBM 推理引擎版本 | 3.15.3 |
| `LLM_COMPRESSION_VERSION` | LLM 压缩工具版本 | 2.0.2 |
| `TORCH_VERSION` | 配套 PyTorch 版本（含 CUDA） | 2.8.0+cu128 |
| `PYTHON_VERSION` | 配套 Python 版本 | py310 |

同时通过 `pip show` 检查已安装版本，并记录 OE-LLM 包内 whl 文件名中的版本：

| 组件 | pip 包名 | 说明 |
|------|----------|------|
| `hbdk4_compiler` | `hbdk4-compiler` | BPU 编译器 |
| `hbdk4_march` | `hbdk4-march` | BPU 架构定义 |
| `hbm_infer` | `hbm-infer` | HBM 推理引擎 |
| `horizon_plugin_profiler` | `horizon-plugin-profiler` | 性能分析插件 |
| `horizon_plugin_pytorch` | `horizon-plugin-pytorch` | PyTorch 量化插件（QAT） |

**Docker 信息**：
- 从实际 OE-LLM 包内的 `run_docker.sh` 提取 Docker 镜像名称和版本号，并核对它与包版本匹配。
- 旧配置中的 `openexplorer/ai_toolchain_ubuntu_22_llm_j6_gpu:{version}` 仅在识别既有环境时保留；不得将其展示为 RDK S 系列产品名、作为默认镜像或在新环境中自动回退到该镜像。
- 从 `run_docker.sh` 提取容器内挂载路径：`/open_explorer_llm`

### 4. 本地环境匹配检查

在当前环境中逐项检测：

1. **Python 版本**：`python3 --version`，要求 3.10 或 3.11
2. **pip 组件**：对每个组件执行 `pip show <包名>`，记录：
   - 是否安装
   - 版本号是否与 OE-LLM 包声明一致
3. **Python 模块导入检查**：
   - `import hbdk4`
   - `import hbm_infer`

根据检查结果判定执行模式：

- **全部匹配** → `EXECUTION_MODE=local`
- **部分缺失或版本不匹配** → `EXECUTION_MODE=docker`，记录缺失项

### 5. Docker 模式下的 GPU 判定

使用与当前 OE-LLM 包配套的镜像；公共 S 系列资料未给出可通用的 OE-LLM 镜像名称。仅在包内 `run_docker.sh` 明确指定、且版本匹配时使用该镜像。旧 `openexplorer/ai_toolchain_ubuntu_22_llm_j6_gpu` 只作为历史兼容标识。

当 `EXECUTION_MODE=docker` 时：

1. **启动 GPU Docker 容器并测试 GPU 可用性**。从包的 `run_docker.sh` 取得 `DOCKER_IMAGE`，显式指定 Bash 入口，不依赖未确认的默认 Entrypoint：
   ```bash
   docker run --rm --gpus all --network none --read-only --tmpfs /tmp \
     --entrypoint /bin/bash "$DOCKER_IMAGE" -lc 'nvidia-smi && python3 -c "import torch; print(torch.cuda.is_available())"'
   ```

2. **检查 nvidia-smi 输出**：
   - 能正常输出 GPU 信息 → `DOCKER_TYPE=gpu`
   - 报错或无 GPU 设备 → 提示用户 OE-LLM 包需要 GPU 环境，无法使用 CPU Docker

3. **采集 GPU 详细信息**（仅当 GPU 可用时）：
   ```bash
   docker run --rm --gpus all --network none --read-only --tmpfs /tmp \
     --entrypoint /bin/bash "$DOCKER_IMAGE" -lc "python3 -c 'import torch, json; print(json.dumps({\"cuda_version\": torch.version.cuda, \"gpu_count\": torch.cuda.device_count(), \"cuda_available\": torch.cuda.is_available()}))'"
   ```
   将返回的 JSON 写入 `GPU_INFO` 字段。

4. **向用户提示判定结果**：
   - GPU 可用时：`检测到 N 张 <GPU型号>，使用 GPU Docker 镜像`
   - GPU 不可用时：`未检测到可用 GPU，OE-LLM 包需要 GPU 环境才能运行`

### 6. 写入 `.drobotics-s/.env.oe-llm-package`

```bash
# OE-LLM 包环境信息（自动生成）
# 检测时间：<timestamp>

# === OE-LLM 包基本信息 ===
OE_LLM_DIR=<OE-LLM 包路径>
OE_LLM_VERSION=<OE-LLM 版本号，如 v2.0.0_rc3>

# === 组件版本 ===
HBDK_COMPILER_VERSION=<版本>
HBDK_MARCH_VERSION=<版本>
HBM_INFER_VERSION=<版本>
HORIZON_PLUGIN_PROFILER_VERSION=<版本>
HORIZON_PLUGIN_PYTORCH_VERSION=<版本>
LLM_COMPRESSION_VERSION=<版本>

# === 配套环境 ===
TORCH_VERSION=<版本，如 2.8.0+cu128>
PYTHON_VERSION=<版本，如 py310>

# === 执行模式 ===
EXECUTION_MODE=<local | docker>

# --- 以下仅在 EXECUTION_MODE=docker 时填写 ---
DOCKER_TYPE=gpu
DOCKER_IMAGE=<由当前 OE-LLM 包内 run_docker.sh 读取>
DOCKER_RUN_CMD=bash <OE_LLM_DIR>/run_docker.sh <dataset_path>
DOCKER_EXEC_PREFIX=docker run --rm --gpus all --entrypoint /bin/bash <DOCKER_IMAGE> -c
MISSING_COMPONENTS=<缺失或不匹配的组件列表，逗号分隔>

# --- 以下仅在 DOCKER_TYPE=gpu 时填写 ---
GPU_INFO=<JSON: {"cuda_version":"...","gpu_count":N,"gpus":[{"index":0,"name":"...","memory_gb":...,"compute_capability":"..."},...]}>
```

> **`DOCKER_EXEC_PREFIX` 说明**：不要依赖未经确认的镜像默认 Entrypoint。执行非交互命令时显式使用 `--entrypoint /bin/bash <image> -lc "<命令>"`。镜像和挂载路径都应以当前包中的 `run_docker.sh` 为准。

- 后续任务直接读取此文件，无需重复检测
- 如果 `EXECUTION_MODE=local`，不填写 Docker 相关字段

## 后续任务的使用方式

顶层 Skill 路由到子 Skill 后，子 Skill 在执行 CLI 命令前读取 `EXECUTION_MODE`：

- **`local`** → 先激活 venv，再直接执行：
  ```bash
  source .drobotics-s/venv-llm/bin/activate
  cd $OE_LLM_DIR/llm_compression && bash scripts/calib.sh ...
  ```
- **`docker`** → 读取 `DOCKER_EXEC_PREFIX`，拼接 CLI 命令：
  ```bash
  # 非交互式单命令（推荐，直接拼 DOCKER_EXEC_PREFIX）
  eval "$DOCKER_EXEC_PREFIX 'cd /open_explorer_llm/llm_compression && bash scripts/calib.sh ...'"

  # 交互式（通过 run_docker.sh 启动 shell）
  bash <OE_LLM_DIR>/run_docker.sh <dataset_path>

  # 手动 docker run
  docker run -it --rm \
    --gpus all \
    --shm-size="15g" \
    -v <OE_LLM_DIR>:/open_explorer_llm \
    -v <dataset_path>:/jfs-public \
    <DOCKER_IMAGE>
  ```

## OE-LLM 包与标准 OE 包的区别

| 方面 | 标准 OE 包 | OE-LLM 包 |
|------|-----------|-----------|
| whl 目录 | `package/host/ai_toolchain/` | `package/host/`（无子目录） |
| 标志性目录 | `samples/`、`docs/`、`toolchain/` | `llm_compression/`、`runtime/` |
| 版本来源 | `version.txt`、`VERSION`、`release_notes.md` | `llm_compression/deps_version.conf` |
| 核心组件 | horizon_tc_ui, hmct, horizon_plugin_pytorch, hbdk4_compiler | hbdk4_compiler, hbm_infer, horizon_plugin_profiler, horizon_plugin_pytorch |
| CLI 工具 | hb_compile, hb_model_info, hmct-debugger | llm_compression/scripts/ 下的脚本 |
| Docker 镜像 | 旧 `ai_toolchain_ubuntu_22_j6_gpu/cpu` 仅作为兼容标识 | 旧 `ai_toolchain_ubuntu_22_llm_j6_gpu` 仅作为兼容标识；新环境从包内 `run_docker.sh` 确认 |
| Docker 挂载 | `/open_explorer` | `/open_explorer_llm` |
| 交叉编译器 | 无 | `aarch64-linux-hb-gcc` .deb 包 |

## 注意事项

- OE-LLM 包版本决定了各组件的兼容版本，混用不同版本可能导致量化或编译失败
- OE-LLM 包与标准 OE 包的组件版本可能不同，不可混用
- 如果用户更换了 OE-LLM 包或升级了组件，需要删除 `.drobotics-s/.env.oe-llm-package` 重新检测
- Docker 模式下，OE-LLM 包路径会自动挂载到容器内的 `/open_explorer_llm`，命令中应使用容器内路径
- Docker 模式下需要 `--shm-size="15g"` 参数（共享内存），否则 LLM 推理可能 OOM
