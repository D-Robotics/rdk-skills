---
name: x5-bpu-python-api
description: 在 X5 板端使用 hbm_runtime.HB_HBMRuntime 加载 .bin、读取模型 I/O 并执行本地 Python 推理；当系统 /etc/version 不低于 3.5.0 且已有匹配 X5 libdnn 的本地 wheel/DEB 时使用。禁止安装 PyPI 同名 S 系列包，也不处理 C++ Runtime、.hbm 或 hbm_infer gRPC。
version: 1.0.0
license: Apache-2.0
---

# X5 BPU Python API

## 目标与边界

完成板端 Python 包门禁、模型元信息、输入构造、推理与输出验证。`HB_HBMRuntime` 是同名接口，不是跨 X5/S 的 ABI 合同。X5 C/C++ Runtime 请求转 `x5-runtime-deploy`；S 系列本地 Python 请求返回公共 Router 并选择 `s-bpu-python-api`。

## 输入合同

- X5 `.bin`、模型来源/哈希、I/O 与可复现输入。
- 板端 `cat /etc/version`、架构、Python ABI、现有包和 `libdnn` 信息。
- 用户提供的 X5 本地 wheel/DEB 或已登记离线制品；安装授权。

## 前置检查

1. 在板端执行：

~~~bash
cat /etc/version
python3 .drobotics/scripts/check_bpu_python_api_version.py --platform x5
~~~

2. 系统版本必须 `>= 3.5.0`，模型必须为 X5 `.bin`。
3. 禁止裸用 `pip install hbm_runtime`；PyPI 同名包是 S 系列实现。
4. wheel 的 cp tag、aarch64 架构和 X5 `libdnn` 必须匹配；安装前记录回滚。

## 执行步骤

1. 未安装时先生成计划，获确认后从本地路径使用 `pip --no-index` 或匹配 DEB。
2. 导入后记录 `HB_HBMRuntime.version` 和包来源。
3. 先读取 `model_names`、`input_names`、`input_shapes`、`input_dtypes`，与编译合同逐项核对。
4. 按参考手册构造 ndarray；多输入顺序、BPU core、priority 等不得凭经验补写。
5. 执行 `runtime.run(...)`，保存输出 shape/dtype/摘要和板端日志。
6. 与同一输入的参考结果比较，不以“能加载”作为正确性完成。

## 产物与完成标准

- 版本门禁、安装来源、Python ABI、`HB_HBMRuntime.version` 和模型 I/O 证据。
- 可运行脚本、输入哈希、输出文件与正确性比较。
- 收据明确该模型/包仅适用于当前 X5 环境。

## 风险与确认

读取和推理为低/中风险；安装 wheel/DEB、升级系统包或覆盖 Python 环境前必须明确确认。不得混装 S 系列包排障。

## 失败与交接

版本/ABI/导入问题 → `x5-environment-probe`；模型/输出问题 → `x5-model-diagnostics`。同一安装或运行策略最多两次。

## 按需参考

- `.drobotics/skills/x5-bpu-python-api/references/x5_bpu_pyapi.md`
