---
name: oe-package-detection
description: 当用户明确选择本机 local 执行，或任务必须读取 OE 包内部资产时使用；普通 PTQ 的默认 Docker 缓存镜像探测不需要 OE_DIR 或 .env.oe-package。
version: 1.1.1
license: Apache-2.0
---

# OE 包环境检测

## 何时使用

- 用户明确要求在宿主机执行工具链命令。
- 任务需要使用本机 OE 包内部的样例、脚本、资源或安装器。
- 默认 Docker 探测已阻塞，且用户决定改用 local 模式。

普通 PTQ 默认使用 Docker 缓存镜像，不因 `.drobotics-s/.env.oe-package` 或 `OE_DIR` 缺失而中断，也不自动派发本 Skill。

## 默认 Docker 路径

从项目根目录运行以下探测。普通 PTQ 使用 `ptq`；明确 QAT 请求使用 `qat`：

```bash
python3 .drobotics-s/scripts/probe_environment.py --workflow ptq
```

探测默认选择 Docker，检查本机缓存的允许镜像，并在不联网、只读的容器中检查相关工具。它不拉取镜像、不要求本机 OE 包，也不要求 `.env.oe-package`。只读取脚本约定的镜像和版本配置键；不要自己猜镜像名或版本。

结果是单个 JSON 对象：

- `status=ready`：使用返回的 `image` 字段运行本任务；仅挂载本次需要的数据和工作目录。
- `status=blocked`：向用户说明 `missing` 中的项目。不要静默改用 local、臆测其他镜像或自动拉取镜像。

此探测只验证本机 Docker 镜像与基础工具可用性。具体命令、参数、API 和版本兼容性仍须按顶层规则从官方文档 MCP 检索核实。

## 仅需 OE 包内资产

如果任务只需要读取 OE 包内的样例、脚本或资源，而工具仍应在 Docker 中运行：

- 只取得完成该任务所需的 `OE_DIR`，并核对所需资产确实存在；路径来自用户、`OE_DIR` 环境变量或 `.drobotics-s/.env.oe-package`，不要扫描无关目录猜路径。
- 普通 PTQ 仍运行默认 Docker 探测 `python3 .drobotics-s/scripts/probe_environment.py --workflow ptq`；显式 QAT 使用 `--workflow qat`。
- 只在容器内任务确实需要这些资产时挂载 OE 包目录。不要因为需要本地路径就设 `EXECUTION_MODE=local` 或传 `--execution-mode local`。

## 显式 local 路径

只有用户明确选择在宿主机执行工具链命令时，才使用本节流程。先从用户提供的路径、`OE_DIR` 环境变量或 `.drobotics-s/.env.oe-package` 中取得 `OE_DIR`。如果路径只在本轮对话中提供，可仅作为探测子进程的 `OE_DIR` 环境变量传入，无须持久写入配置。然后执行：

```bash
python3 .drobotics-s/scripts/probe_environment.py --workflow ptq --execution-mode local
```

明确 QAT 请求将 `--workflow ptq` 改为 `--workflow qat`。脚本会检查 OE 目录标志文件、版本信息和本机命令；QAT 还会检查相关 Python 包。探测为 blocked 时，按 JSON `missing` 逐项补齐或报告阻塞，不得根据旧版本地手册猜测版本或依赖。

`OE_DIR` 缺失时，请用户提供 OE 包目录。不要通过扫描无关目录或从其他项目配置中猜测路径。只在确实需要持久保存本机 OE 配置时写入 `.drobotics-s/.env.oe-package`；Docker 默认执行不需要生成该文件。
