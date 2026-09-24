---
name: x5-environment-probe
description: 只读探测 X5 OE Docker/host 工具链、Plugin、Runtime、Python 和可选板端事实并生成 environment.json；当执行任何 X5 工作流前环境未知、版本不明或需要 ready/degraded/blocked 结论时使用。不得安装、升级或修改设备。
version: 1.1.1
license: Apache-2.0
---

# X5 环境探测

## 目标与边界

记录真实环境事实，不修复环境。OE 官方强烈建议 Docker，X5 OE Mapper 应优先检查已配置的 Docker image。探测器不查询或检查文档目录；HAT 可见不代表 HAT 在范围内。

## 输入合同

- `--workflow environment|ptq|qat|runtime|python-api|diagnose`。
- 可选的旧版 `--docs-root`（兼容参数，会忽略）、板卡型号、`/etc/version`、架构与可达性事实。
- 输出路径，通常是运行目录的 `environment.json`。
- 可选 `--docker-image <本地 X5 OE image>`；也可设置 `OE_DROBOTICS_DOCKER_IMAGE`。PTQ 使用匹配版本的 CPU image，例如 `openexplorer/ai_toolchain_ubuntu_20_x5_cpu:<version>`；QAT 使用 GPU image，例如 `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_gpu:<version>`。
- 默认执行模式为 Docker；只有用户明确选择 `--execution-mode host`（或设置 `OE_DROBOTICS_EXECUTION_MODE=host`）时才检查并使用宿主机工具链。

## 前置检查

- 板卡事实必须来自实际命令或用户提供的可审计证据。

## 执行步骤

~~~bash
python .drobotics-x5/platforms/x5/scripts/probe_environment.py \
  --workflow ptq \
  --docker-image openexplorer/ai_toolchain_ubuntu_20_x5_cpu:<version> \
  --output <run-root>/environment.json
~~~

QAT 探测应改用 GPU image：

~~~bash
python .drobotics-x5/platforms/x5/scripts/probe_environment.py \
  --workflow qat \
  --docker-image registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_gpu:<version> \
  --output <run-root>/environment.json
~~~

探测只检查本地 image，不拉取镜像。容器 smoke 使用无网络、只读 rootfs 和临时 `/tmp`，通过 `/bin/bash` 入口检查容器内 `hb_mapper` help 与 `hb_model_info`。没有宿主机 `hb_mapper` 不会覆盖已验证的 Docker 结果。

QAT 使用匹配版本的 GPU image；probe 会用 Docker `--gpus all` 启动只读容器，并验证 Plugin、`March.BAYES_E` 和 `torch.cuda.is_available()`。这只证明容器能看见 CUDA 设备，不证明训练脚本、收敛或训练性能可用。Host QAT 同样要求快照中的 `toolchain.cuda.available: true`。

只有用户已配置匹配的本地 OE host 环境并明确选择 host 模式时，才添加 `--execution-mode host`。缺少 Docker image 不会自动切换到宿主机。

Runtime/Python 请求如需板端事实，追加 `--board-chip X5 --board-architecture aarch64 --board-version <version> --board-reachable --require-board`。

## 产物与完成标准

- `ready`：目标工作流所需工具和已声明的板端条件齐全；这不表示已执行官方文档核验。
- `degraded`：缺少可选能力，但能安全进入有限工作流。
- `blocked`：缺少必需工具、版本输入、板端或芯片事实。
- 快照通过 `environment.schema.json` 校验并明确 `hat_in_scope: false`。

## 风险与确认

只读命令和写入新快照为低风险。不得在 probe 中调用 pip、apt、dpkg、docker pull、镜像导入或远端写入。Docker 检查不得挂载用户目录。

## 失败与交接

- 必需项缺失：交接 `x5-environment-install`，但仅生成计划。
- 芯片不为 X5：返回 `blocked` 并交给顶层路由。
- 工具版本无法读取：保留命令路径和限制，不猜版本。
- 默认 Docker image 不存在或 help 检查失败：报告缺项，不自动拉取镜像或切换 host。只有用户明确选择 host 模式并确认本地 OE 环境后才探测宿主机。

## 按需参考

- `.drobotics-x5/platforms/x5/schemas/environment.schema.json`
- `.drobotics-x5/platforms/x5/references/manual-map.md`
- 具体命令、API 与版本支持按 `.drobotics-x5/docs/local-document-retrieval.md` 的官方 MCP 合同核验
- [OE X5 官方环境部署手册](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/env_install/env_deploy.html)
