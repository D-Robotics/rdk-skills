---
name: x5-environment-install
description: 按已审阅计划安装或配置 X5 OE Mapper、Plugin、Runtime 或本地离线制品；仅当 environment.json 为 blocked、制品来源与回滚路径已明确且用户已确认副作用时使用。禁止安装 HAT 或把在线下载当作默认方案。
---

# X5 环境安装

## 目标与边界

执行最小、可回滚、来源可追溯的环境变更。只处理当前 X5 工作流所需组件，不顺带升级无关包。

## 输入合同

- `environment.json`、缺失项和目标工作流。
- 已审阅安装计划、制品路径/清单/哈希、目标目录和权限。
- 明确审批记录与回滚方案。

## 前置检查

1. 验证制品来自用户提供或已登记的离线发布物。
2. 检查架构、Python ABI、磁盘、现有版本和冲突包。
3. 确认计划不包含 HAT、S 系列包、X3 Runtime 或 PyPI 同名替代品。
4. 共享环境、系统包、Docker 镜像或 Runtime 替换必须有高风险确认。

## 执行步骤

1. 使用 `.drobotics/scripts/release_artifacts.py` 检查制品清单与哈希。
2. 记录安装前版本和恢复命令。
3. 执行计划中的最小变更；每个命令和返回码写入运行日志。
4. 不得在失败后切换到未经审阅的在线源。
5. 安装后重新执行 `x5-environment-probe`，用真实结果判断是否完成。

## 产物与完成标准

- 安装日志、制品哈希、前后版本和回滚记录完整。
- 新 `environment.json` 对目标工作流为 `ready` 或明确的 `degraded`。
- 仅安装计划内组件；没有隐式 HAT/S/X3 依赖。

## 风险与确认

任何系统包、共享 Python、容器导入、Runtime 或板端包变更都要在执行前展示目标、影响和回滚并取得确认。

## 失败与交接

同一策略最多两次；第二次失败立即停止，执行可行回滚并交接 `x5-model-diagnostics`。禁止靠删除环境重来掩盖证据。

## 按需参考

- `.drobotics/docs/offline-artifact-delivery.md`
- `.drobotics/platforms/x5/policies/risk-policy.md`
