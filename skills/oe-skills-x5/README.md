# X5 Skill Pack V2

X5 Pack 以“S 系列的实战深度 + V2 的模块化、脚本化和机器可验证合同”为完成标准。入口为 `x5-router`，详细注册表为 `.drobotics/platforms/x5/skill-index.json`。

## 能力模块

| 模块 | Skills | 可验证承诺 |
| --- | --- | --- |
| Router | `x5-router` | 单一主路由、拒绝理由与 `route.json` |
| Environment | `x5-environment-setup`、`x5-environment-probe`、`x5-environment-install` | 真实环境快照、审批后安装与重新探测 |
| PTQ | `x5-ptq-deploy`、`x5-model-preflight`、`x5-calibration-data-prepare`、`x5-ptq-config-authoring`、`x5-ptq-compile` | `bayes-e` YAML、checker、`.bin`、模型信息和 Runtime 验证 |
| Plugin QAT | `x5-qat-deploy`、`x5-qat-adaptation`、`x5-qat-training`、`x5-qat-compile` | `March.BAYES_E`、分阶段指标、`check_model`、`.hbm/.hbir` |
| Runtime | `x5-runtime-deploy`、`x5-runtime-cpp-infer`、`x5-runtime-perf-eval`、`x5-board-monitor`、`x5-bpu-python-api` | 模型/I/O/板端正确性、性能和资源证据 |
| Diagnose | `x5-model-diagnostics`、`x5-accuracy-diagnostics`、`x5-consistency-diagnostics`、`x5-performance-diagnostics` | 首次失败阶段、证据、单变量恢复实验与合法 handoff |

## 强制边界

- PTQ：`hb_mapper`、`bayes-e`、`.bin`。
- Plugin QAT：`March.BAYES_E`、`check_model`、`compile_model`/`export_hbir`、`.hbm/.hbir`。
- HAT、HAT config、Trainer、Model Zoo、`tools/compile_perf.py` 全部排除。
- `March.BAYES` 属于 J5，不得复制到 X5。
- X3、S 系列模型、Runtime、wheel/DEB 和命令不得复用。

## 运行合同

实际运行使用 `.drobotics/platforms/x5/scripts/run_contract.py` 管理 `input.json`、`environment.json`、`route.json`、`plan.json`、`run-state.json`、`events.ndjson`、`artifacts.json`、`verification.json` 和 `receipt.json`。

## 验收

~~~bash
python .drobotics/scripts/validate_x5_skills.py
python .drobotics/scripts/validate_bpu_python_api_skills.py
python .drobotics/scripts/validate_release_artifacts.py
~~~

静态验收通过不代表真实工具链/开发板 smoke 已通过；发布记录必须区分两者。
