---
name: x5-environment-setup
description: 编排 X5 工具链环境探测和经确认的安装；当用户希望准备 OE Mapper、Plugin、Runtime 或板端 Python 环境时使用。先只读探测，再生成安装计划，只有明确授权后才交给 x5-environment-install；不安装 HAT。
version: 1.0.0
license: Apache-2.0
---

# X5 环境准备

## 目标与边界

把“环境准备”拆成事实探测和有审批的安装两个阶段。此兼容入口不把命令缺失自动解释为允许下载、安装、升级或替换共享 Runtime。

## 输入合同

- 目标工作流：PTQ、QAT、Runtime、Python API 或诊断。
- 发布包、容器、SDK、离线制品或板端连接信息（如已知）。
- 目标环境范围、可接受副作用、回滚要求和授权状态。

## 前置检查

1. 先读取 X5 Pack 的兼容矩阵和风险策略。
2. 确认目标是 X5；出现 X3、S 系列或 HAT 环境时停止混用。
3. 默认调用 `x5-environment-probe`，不直接运行安装命令。

## 执行步骤

1. 运行只读探测并生成 `environment.json`。
2. 若状态为 `ready`，直接交接目标工作流。
3. 若状态为 `degraded`，说明哪些能力可用、哪些仅缺可选工具。
4. 若状态为 `blocked`，生成安装计划：制品来源、哈希、安装位置、空间、权限、副作用、验证和回滚。
5. 只有用户明确确认计划后，交接 `x5-environment-install`；安装后必须重新 probe。

## 产物与完成标准

- `environment.json` 来自真实探测，不是根据手册推断。
- 安装计划可审阅，包含来源与回滚；未授权时没有环境写入。
- 最终状态为 `ready`、`degraded` 或带明确缺失项的 `blocked`。

## 风险与确认

- probe 为低风险。
- 用户级安装为中风险；系统包、共享容器、Runtime 替换为高风险。
- HAT 包和 HAT Docker 环境不属于当前安装计划。

## 失败与交接

同一安装方案最多尝试两次。第二次失败后保存日志、包版本和回滚状态，交接 `x5-model-diagnostics` 或保持 `blocked`。

## 按需参考

- `.drobotics/platforms/x5/policies/compatibility.md`
- `.drobotics/docs/offline-artifact-delivery.md`
