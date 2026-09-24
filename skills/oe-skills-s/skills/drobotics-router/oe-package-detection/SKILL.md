---
name: oe-package-detection
description: OE 包环境检测 Skill。当任务涉及量化、编译、部署等工具链操作，且 .drobotics-s/.env.oe-package 不存在时触发。自动完成 OE 包路径定位、版本采集、本地环境匹配检查、S 系列 GPU/CPU Docker 判定，并将结果写入 .env 文件。
version: 1.1.0
license: Apache-2.0
---

# OE 包环境检测

## 执行方式

> **本 Skill 应通过 subagent 执行。** 主 agent 在前置检查中发现 `.env.oe-package` 缺失或不完整时，应将本文件的完整内容作为 subagent prompt 派发执行。subagent 完成后汇报写入结果（OE 路径、版本、执行模式），主 agent 读取 `.env.oe-package` 继续后续流程。

## 目标

检测 OE 包路径、版本及本地环境匹配情况，写入 `.drobotics-s/.env.oe-package`，供后续所有工具链任务直接使用。

## 触发条件

任何涉及量化、编译、部署、板端推理、性能/精度评估的任务进入 drobotics-router 前，如果 `.drobotics-s/.env.oe-package` 不存在，顶层 Skill 会**中断任务并提示用户**：

> 未检测到 OE 包环境配置（`.drobotics-s/.env.oe-package`）。请提供 OE 包路径，或回复"跳过"暂不配置。

- **用户提供路径** → 进入本检测流程
- **用户回复"跳过"** → 记录跳过（仅当次对话有效，下次仍会提示），继续后续任务

## 检测流程

### 1. 检查 `.drobotics-s/.env.oe-package` 是否存在

- 文件存在且内容完整（包含 `OE_DIR`、`OE_VERSION`、`EXECUTION_MODE` 等字段）→ 直接读取，跳过后续步骤
- 文件不存在或不完整 → 进入步骤 2

### 2. 定位 OE 包路径

按优先级查找：

1. **环境变量**：`OE_DIR`、`OPEN_EXPLORER_DIR`、`HORIZON_OE_DIR`
2. **项目配置文件**：`.env`、`.drobotics-s/oe.env`、`CLAUDE.md` 中声明的路径
3. **常见路径探测**：`/open_explorer`、`~/open_explorer`、`/opt/openexplorer`
4. **以上都没有** → 询问用户 OE 包路径

找到路径后，验证目录中存在 OE 包的标志性文件（如 `run_docker.sh`、`samples/`、`docs/`、`toolchain/` 等至少两个），否则提示用户确认路径是否正确。

### 3. 采集 OE 版本信息

从 OE 包目录中提取以下信息，并优先按当前 D-Robotics S 系列 OE 发布包和在线手册识别版本：

**OE 包整体版本**：
- 检查 `version.txt`、`VERSION`、`release_notes.md` 或 `release_notes.txt`
- 从文件名推断（当前在线手册列出的发布包为 `oe-package-3.7.0-s100-s600.tgz`）
- 以上都无法确定时询问用户

**各组件版本**（通过 `pip show` 检查已安装版本，同时记录 OE 包内 whl 文件名中的版本）：

| 组件 | pip 包名 | 说明 |
|------|----------|------|
| `horizon_tc_ui` | `s-tc-ui` | 模型集成工具 |
| `hmct` | `hmct` | 模型转换/量化工具 |
| `horizon_plugin_pytorch` | `horizon-plugin-pytorch` | PyTorch 量化插件（QAT） |
| `hbdk4_compiler` | `hbdk4-compiler` | 编译器 |

**Docker 信息**：
- D-Robotics OE 手册强烈建议使用 Docker。默认 `EXECUTION_MODE=docker`；只有用户明确要求本机执行，且本地 OE 包版本与所有依赖均已核实时，才选择 `local`。
- 使用与 OE 包版本完全匹配的 S 系列镜像。OE 3.7.0 CPU 镜像 `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_cpu:v3.7.0` 已在受限容器中验证可执行 `hb_compile --help` 和 `hb_config_generator --help`。GPU 镜像 `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_gpu:v3.7.0` 已在 sz-dev 的 GPU 容器中实测，`nvidia-smi` 可见 RTX 5090 且 `torch.cuda.is_available()` 为 True；其他宿主机仍须单独检查。
- S100/S600 镜像命名：
  - CPU：`registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_cpu:v{version}`
  - GPU：`registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_gpu:v{version}`
- 手册列出的 OE 3.7.0 发布包为 `oe-package-3.7.0-s100-s600.tgz`，对应镜像标签 `v3.7.0`。其他版本须先从匹配的 `run_docker.sh` 或镜像仓库确认标签；不要擅自使用不同版本的镜像。`OE_VERSION` 保存为数字版本（例如 `3.7.0`）；如来源带 `v` 前缀，拼接标签前先去掉。
- 旧配置中的 `openexplorer/ai_toolchain_ubuntu_22_j6_cpu` / `..._j6_gpu` 只作为历史兼容信息识别，不作为新环境默认镜像。镜像不可用时报告版本不匹配，不自动切换旧镜像。

### 4. 本地环境匹配检查

在当前环境中逐项检测：

1. **Python 版本**：`python3 --version`，要求 >= 3.8
2. **pip 组件**：对每个组件执行 `pip show <包名>`，记录：
   - 是否安装
   - 版本号是否与 OE 包声明一致
3. **CLI 工具可用性**：检查以下命令是否可执行：
   - `hb_compile --version`（或 `which hb_compile`）
   - `hb_model_info --version`（或 `which hb_model_info`）
   - `hmct-debugger --version`（或 `which hmct-debugger`）

默认使用 Docker：

- `EXECUTION_MODE=docker`，记录本地缺失或不匹配项；运行时使用版本匹配的 S 系列镜像。
- 只有用户明确要求本机执行，且本地 OE 包、Python 和组件版本均匹配时，才设 `EXECUTION_MODE=local`。

### 5. Docker 模式下的 GPU/CPU 判定

当 `EXECUTION_MODE=docker` 时，需要确定使用 GPU 还是 CPU 镜像：

1. **启动 GPU Docker 容器并测试 GPU 可用性**。显式指定 Bash 入口，不依赖未验证的镜像默认 Entrypoint：
   ```bash
   OE_VERSION=3.7.0
   OE_VERSION_TAG="${OE_VERSION#v}"
   GPU_IMAGE="registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_gpu:v${OE_VERSION_TAG}"
   docker run --rm --gpus all --network none --read-only \
     --tmpfs /tmp:rw,exec,nosuid,size=256m --entrypoint /bin/bash "$GPU_IMAGE" \
     -lc 'nvidia-smi && python3 -c "import torch; print(torch.cuda.is_available())"'
   ```

2. **检查 GPU 与 CUDA 输出**：
   - `nvidia-smi` 正常且 `torch.cuda.is_available()` 为 True → `DOCKER_TYPE=gpu`
   - 任一检查失败 → `DOCKER_TYPE=cpu`；若用户要求 QAT，说明当前容器不能执行 GPU 训练

3. **采集 GPU 详细信息**（仅当上一步确认 GPU 可用时）：
   ```bash
   docker run --rm --gpus all --network none --read-only \
     --tmpfs /tmp:rw,exec,nosuid,size=256m --entrypoint /bin/bash "$GPU_IMAGE" \
     -lc "python3 -c 'import torch, json; print(json.dumps({\"cuda_version\": torch.version.cuda, \"gpu_count\": torch.cuda.device_count(), \"cuda_available\": torch.cuda.is_available()}))'"
   ```
   将返回的 JSON 写入 `GPU_INFO` 字段。如果 PyTorch 无法识别 GPU（`cuda.is_available()=False`），则 `GPU_INFO` 设为空。

4. **向用户提示判定结果**：
   - GPU 可用时：`检测到 N 张 <GPU型号>，默认使用 GPU Docker 镜像`
   - GPU 不可用时：`未检测到可用 GPU，将使用 CPU Docker 镜像。如需 GPU 加速，请检查 NVIDIA 驱动和 Docker GPU 支持`

### 6. 写入 `.drobotics-s/.env.oe-package`

```bash
# OE 包环境信息（自动生成）
# 检测时间：<timestamp>

# === OE 包基本信息 ===
OE_DIR=<OE 包路径>
OE_VERSION=<OE 数字版本号，如 3.7.0；不要包含 v 前缀>

# === 组件版本 ===
HORIZON_TC_UI_VERSION=<版本>
HMCT_VERSION=<版本>
HORIZON_PLUGIN_PYTORCH_VERSION=<版本>
HBDK_COMPILER_VERSION=<版本>

# === 执行模式 ===
EXECUTION_MODE=<local | docker>

# --- 以下仅在 EXECUTION_MODE=docker 时填写 ---
DOCKER_TYPE=<gpu | cpu>
DOCKER_IMAGE=registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_<gpu|cpu>:v<OE_VERSION>
DOCKER_RUN_CMD=bash <OE_DIR>/run_docker.sh ./data
DOCKER_EXEC_PREFIX=docker run --rm [--gpus all] -v <OE_DIR>:/open_explorer --entrypoint /bin/bash <DOCKER_IMAGE> -lc
MISSING_COMPONENTS=<缺失或不匹配的组件列表，逗号分隔>

# --- 以下仅在 DOCKER_TYPE=gpu 时填写 ---
GPU_INFO=<JSON: {"cuda_version":"...","gpu_count":N,"gpus":[{"index":0,"name":"...","memory_gb":...,"compute_capability":"..."},...]}>
```

> **`DOCKER_EXEC_PREFIX` 说明**：不要依赖未经验证的镜像默认 Entrypoint。执行非交互命令时显式使用 `--entrypoint /bin/bash <image> -lc "<命令>"`，并按任务挂载数据和工作目录。OE 3.7.0 CPU 镜像的 CLI help 已用该方式验证；GPU 镜像仍需在当前宿主机实测。

- 后续任务直接读取此文件，无需重复检测
- 如果 `EXECUTION_MODE=local`，不填写 Docker 相关字段

## 后续任务的使用方式

顶层 Skill 路由到子 Skill 后，子 Skill 在执行 CLI 命令前读取 `EXECUTION_MODE`：

- **`local`** → 直接在当前环境执行 CLI 命令
- **`docker`** → 读取 `DOCKER_EXEC_PREFIX`，拼接 CLI 命令：
  ```bash
  # 只读 CLI help 验证（OE 3.7.0 CPU 镜像已验证）
  docker run --rm --network none --read-only --tmpfs /tmp:rw,exec,nosuid,size=256m \
    --entrypoint /bin/bash "$DOCKER_IMAGE" -lc 'hb_compile --help'

  # 交互式（通过 run_docker.sh 启动 shell）
  bash <OE_DIR>/run_docker.sh ./data

  # 手动 docker run
  docker run -it --rm \
    -v <OE_DIR>:/open_explorer \
    -v ./dataset:/data/oe/data \
    <DOCKER_IMAGE>
  ```

## 注意事项

- OE 包版本决定了各组件的兼容版本，混用不同版本可能导致量化或编译失败
- 如果用户更换了 OE 包或升级了组件，需要删除 `.drobotics-s/.env.oe-package` 重新检测
- 使用 `run_docker.sh` 时按脚本设置挂载 OE 包；直接 `docker run` 时必须显式挂载到 `/open_explorer`，命令中使用容器内路径
