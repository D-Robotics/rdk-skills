---
name: x5-qat-adaptation
description: 将浮点 PyTorch 模型适配为 X5 Plugin QAT 模型；当需要设置 March.BAYES_E、量化边界、可量化算子、prepare 和 fake-quant 状态入口时使用。只处理 horizon_plugin_pytorch，不处理 HAT 或 J5 March.BAYES。
version: 1.0.0
license: Apache-2.0
---

# X5 QAT 模型适配

## 目标与边界

让模型能进入 Plugin calibration/QAT/convert，同时尽量保持浮点语义。优先使用文档推荐的 FX 路径；只有现有模型确实依赖 eager 时才采用 eager 合同。

## 输入合同

- 模型源码、构建函数、浮点 checkpoint 和 example inputs。
- Plugin/PyTorch 版本、目标输入色彩/布局和部署边界。
- 浮点参考输出与最小单元测试。

## 前置检查

1. 在模型构建/prepare 前执行 `set_march(March.BAYES_E)`。
2. 通用 quick start 的 `March.BAYES` 是 J5 示例，不能照抄。
3. 识别函数式算子、动态控制流、共享 QuantStub、原地操作和无法 trace 的路径。
4. 不导入 `hat`，不使用 HAT config 或 Trainer。

## 执行步骤

1. 在真实部署输入边界插入独立 `QuantStub`，在最终浮点输出边界插入 `DeQuantStub`。
2. 对不支持的函数式算子按 Plugin 手册改为可量化 module；不要为通过 prepare 任意改变数学语义。
3. 配置 qconfig，并用真实 example inputs 执行 prepare。
4. 定义 calibration/QAT/validation 的 `set_fake_quantize` 状态入口。
5. 重新加载浮点权重并对比适配前后浮点输出。
6. 运行静态合同检查：

~~~bash
python .drobotics/platforms/x5/scripts/check_qat_target.py \
  --source <adapted.py> --stage adaptation --report <adaptation-check.json>
~~~

## 产物与完成标准

- 适配源码、模型结构差异、example inputs 和浮点一致性报告。
- `adaptation-check.json` 证明 `March.BAYES_E`、`set_march` 和 prepare 存在，无 HAT/J5/PTQ 混用。
- 适配模型可完成一次 calibration forward，且无未解释的 shape/dtype 变化。

## 风险与确认

修改模型源码为中风险；默认新建分支/文件，不覆盖用户原始模型。结构性改动需展示 diff。

## 失败与交接

一次只修一类不支持模式。两次仍无法 prepare 时保存最小复现，交接 `x5-model-diagnostics`，不要切换到 HAT。

## 按需参考

- `_sources/plugin/source/user_guide/float_model_requirements.md.txt`
- `_sources/plugin/source/terminology/terminology.md.txt`
