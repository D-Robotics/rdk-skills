---
name: x5-environment-probe
description: 只读探测 X5 手册、OE Mapper、Plugin、Runtime、Python 和可选板端事实并生成 environment.json；当执行任何 X5 工作流前环境未知、版本不明或需要 ready/degraded/blocked 结论时使用。不得安装、升级或修改设备。
---

# X5 环境探测

## 目标与边界

记录真实环境事实，不修复环境。手册基线是 `OE Mapper v1.2.8 / Python 3.10`；HAT 可见不代表 HAT 在范围内。

## 输入合同

- `--workflow environment|ptq|qat|runtime|python-api|diagnose`。
- 可选文档根、板卡型号、`/etc/version`、架构与可达性事实。
- 输出路径，通常是运行目录的 `environment.json`。

## 前置检查

- 文档解析优先级：显式路径 → `OE_DROBOTICS_DOC_ROOT` → `OE_X_SERIES_DOC_ROOT` → 工作区相对发现。
- 板卡事实必须来自实际命令或用户提供的可审计证据。

## 执行步骤

~~~bash
python .drobotics/platforms/x5/scripts/probe_environment.py \
  --workflow ptq \
  --output <run-root>/environment.json
~~~

Runtime/Python 请求如需板端事实，追加 `--board-chip X5 --board-architecture aarch64 --board-version <version> --board-reachable --require-board`。

## 产物与完成标准

- `ready`：目标工作流的必需工具、手册和板端条件齐全。
- `degraded`：缺少可选能力，但能安全进入有限工作流。
- `blocked`：缺少必需工具、手册、版本、板端或芯片事实。
- 快照通过 `environment.schema.json` 校验并明确 `hat_in_scope: false`。

## 风险与确认

只读命令和写入新快照为低风险。不得在 probe 中调用 pip、apt、dpkg、docker pull、镜像导入或远端写入。

## 失败与交接

- 必需项缺失：交接 `x5-environment-install`，但仅生成计划。
- 芯片不为 X5：返回 `blocked` 并交给顶层路由。
- 工具版本无法读取：保留命令路径和限制，不猜版本。

## 按需参考

- `.drobotics/platforms/x5/schemas/environment.schema.json`
- `.drobotics/platforms/x5/references/manual-map.md`
