---
name: x5-router
description: 路由 X5 OE 环境、PTQ、Plugin QAT、Runtime、板端 Python 和诊断请求；通用量化默认优先 PTQ，只有明确要求 QAT 或 PTQ 评测确认无法达到目标时才进入 QAT；不执行 HAT、X3 或 S 系列工作流。
version: 1.1.0
license: Apache-2.0
---

# X5 路由

## 目标与边界

- 本 Skill 是 X5 OE Pack 的唯一入口。路由前读取 `.drobotics-x5/platforms/x5/skill-index.json`，按其中的 `routing_policy`、`intents`、`accepts` 和 `handoffs` 决定主流程；不要从 Skill 名称猜用途。
- 按顺序识别目标芯片、用户意图、模型/产物格式、环境和操作风险。出现“X 系列”但型号不明时，先确认 X5 或 X3。
- 本 Pack 只覆盖 X5。HAT、HAT config、Trainer、Model Zoo、`tools/compile_perf.py`、X3 和 S100/S100P/S600 工作流都不在范围内。
- X5 PTQ 使用 CLI/YAML `bayes-e` 并生成 `.bin`；X5 Plugin QAT 使用 `March.BAYES_E` 并产生 Plugin 编译合同。`March.BAYES` 属于 J5，不能用于 X5。
- 路由时只选一个主 Skill；连续阶段写入有序 handoff。开始执行前先读主 Skill 的 `SKILL.md`。

## 输入合同

- 用户的结果目标、目标芯片、模型/代码路径和期望产物。
- 已知模型框架、导出格式、输入输出合同、环境和板端事实。
- 量化方式是否由用户明确指定，PTQ 评测是否已有实际精度/性能证据。
- 是否允许安装、训练、生成模型、上传或覆盖文件。

## 前置检查

1. 用型号、来源信息、明确工具或模型元数据确认目标芯片。`.bin` 后缀不能单独证明模型属于 X5。
2. 识别目标是量化编译、环境准备、Runtime、板端 Python 还是已有故障诊断。
3. 量化方式按下方决策表确定。仅有 PyTorch 源码或 `.pt/.pth` 不能推断用户要求 QAT。
4. 环境未知时先选 `x5-environment-probe`。OE Mapper 默认优先使用匹配版本的 X5 Docker；宿主机缺少 `hb_mapper` 不代表已配置 Docker 中的工具链不可用。
5. 运行板端任务前确认真实 X5 板卡信息；缺失时先询问，不猜 IP、版本或架构。

## 执行步骤

### PTQ 与 QAT 决策

OE X5 官方手册建议先尝试 PTQ，评估精度和性能；只有精度问题确实无法通过 PTQ 解决时再切到 QAT。遵循注册表中的 `routing_policy.quantization`：

| 用户输入/证据 | 主 Skill | 路由行为 |
| --- | --- | --- |
| 明确要求 PTQ；或未指定量化方式且已有 ONNX/Caffe 浮点模型 | `x5-ptq-deploy` | 默认 PTQ。handoff 为预检 → 校准数据 → 配置 → 编译 → 验证。 |
| 明确要求 X5 Plugin QAT | `x5-qat-deploy` | 尊重明确选择；不强制先跑 PTQ。 |
| 只有 PyTorch 源码或 `.pt/.pth`，未指定 QAT，也没有可用 ONNX/Caffe | 暂停路由并澄清 | 询问能否导出 ONNX 先走 PTQ，或是否确实要 Plugin QAT；不得仅因框架是 PyTorch 自动选择 QAT。 |
| 已完成 PTQ 但评测未达到目标 | `x5-accuracy-diagnostics` | 先定位首次精度差异并确认 PTQ 限制；确需训练时再与用户确认 QAT 计划。 |
| QAT 训练产物可导出 ONNX，且后续目标是常规 X5 `.bin` | `x5-ptq-deploy` | 走 ONNX PTQ/Docker 编译流程；只有用户要求 Plugin QAT 编译产物时才走 QAT 编译。 |

PTQ/QAT 简介：[OE X5 官方手册](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/faststart/ptq_qat_overview.html)。PTQ 支持的输入格式和转换流程按对应版本的 OE 手册核对，不从其他芯片推断。

### 主流程选择

| 用户目标 | 主 Skill | handoff |
| --- | --- | --- |
| 准备或检查 X5 OE 环境 | `x5-environment-setup` / `x5-environment-probe` | probe → 经确认后 install |
| ONNX/Caffe PTQ 到 X5 `.bin` | `x5-ptq-deploy` | preflight → calibration → config → compile → Runtime/accuracy evaluation |
| 明确指定 Plugin QAT | `x5-qat-deploy` | adaptation → training → compile → consistency/runtime |
| 已有 X5 `.bin` 的 C/C++/上板/性能任务 | `x5-runtime-deploy` | C++ → perf → board monitor |
| X5 板端 `HB_HBMRuntime` Python | `x5-bpu-python-api` | environment probe / diagnostics |
| 用户提供失败日志或收据 | `x5-model-diagnostics` | accuracy / consistency / performance diagnosis |

将候选、拒绝理由、主 Skill 和有序 handoff 写入运行目录的 `route.json`。泛化量化请求默认 PTQ 时，在 `rejections` 记录未选 QAT 的理由；明确 QAT 时记录为何未选 PTQ。需要澄清模型格式时先提问，不伪造路由结果。

### 环境选择

X5 OE 官方环境手册强烈建议 Docker。环境探测优先检查用户配置的本地 X5 OE image，并在无网络、只读容器和临时 `/tmp` 中检查 `hb_mapper`/`hb_model_info`；不执行 `docker pull`，不挂载用户目录。只有用户已配置本地 OE host 环境并选择 host 模式时，才用宿主机 CLI 作为回退。Docker 文档：[OE X5 环境部署](https://developer.d-robotics.cc/oe_x5_doc/cn/oe_mapper/source/env_install/env_deploy.html)。

若要在容器内运行 Pack 脚本，需使用官方推荐的 Docker 启动方式，并确认模型、校准数据、配置和运行目录都位于容器可见的挂载路径；不要直接把宿主机绝对路径传入容器命令。

## 产物与完成标准

- `route.json` 符合 `.drobotics-x5/platforms/x5/schemas/route.schema.json`，且 `selected_skill` 在 X5 索引中注册。
- 路由只选择一个主 Skill；拒绝的相邻路径有简短理由，handoff 顺序与主流程一致。
- 环境探测记录 Docker/host 选择。仅宿主机没有 `hb_mapper` 时，不把已验证的 Docker 工具链标记为缺失。
- 环境、输入或授权不足时只交接预检/探测，不能声称执行成功。

## 风险与确认

路由和只读探测为低风险。不得把用户对“分析”的同意解释为对安装、QAT 长时间训练、覆盖、上传或停止进程的授权。QAT 需要训练计划、资源成本和可回滚输出目录。

## 失败与交接

- 芯片不明：只问一个最小问题“目标板卡是 X5、X3 还是其他型号？”
- PyTorch 模型没有 ONNX/Caffe 输入且用户未指定 QAT：询问能否导出 ONNX，或是否明确要 QAT。
- PTQ 精度未达标：先交 `x5-accuracy-diagnostics`，基于评测证据再决定是否转 QAT。
- Docker image 未配置或容器探测失败：报告缺失证据；不得自动拉镜像或切换共享宿主机环境。
- HAT 请求：说明当前 Pack 排除 HAT，不迁移其配置。
- 无合法候选：保存拒绝理由并以 `blocked` 结束。

## 按需参考

- `.drobotics-x5/platforms/x5/skill-index.json`
- `.drobotics-x5/platforms/x5/policies/compatibility.md`
- `.drobotics-x5/platforms/x5/policies/risk-policy.md`
- `.drobotics-x5/platforms/x5/references/run-contract.md`
