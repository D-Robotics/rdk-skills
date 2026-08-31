---
name: x5-qat-compile
description: 对 X5 Plugin 定点模型执行 trace、check_model 和 compile_model/export_hbir；当 quantized 指标已达标，需要生成 .hbm 或 .hbir 与编译报告时使用。禁止输出伪装的 .bin 或自动调用 hb_mapper makertbin。
version: 1.0.0
license: Apache-2.0
---

# X5 QAT 模型检查与编译

## 目标与边界

把已验证定点模型转换为 Plugin 编译产物。`.hbm`/`.hbir` 不等同于 OE Mapper `.bin`；Runtime 是否可加载由匹配发布包实测决定。

## 输入合同

- 已达标 quantized 模型、example inputs、评价指标和源码。
- `March.BAYES_E` 环境、输出 `.hbm` 或 `.hbir` 路径、编译选项。
- 新输出目录和 Runtime 兼容性验证计划。

## 前置检查

1. 模型和 example inputs 放到手册要求的设备（通常 trace 时为 CPU）。
2. 再次验证 quantized 指标和模型哈希。
3. 输出后缀必须与 API 合同一致：`compile_model` → `.hbm`，`export_hbir` → `.hbir`。

## 执行步骤

1. 用真实 example inputs `torch.jit.trace` 并保存可复现 TorchScript。
2. 运行 `check_model(script_model, [example_input])`，保存完整检查日志。
3. 选择一个输出路径：`compile_model(..., hbm="model.hbm")` 或 `export_hbir(...)`。
4. 运行源码合同检查：

~~~bash
python .drobotics/platforms/x5/scripts/check_qat_target.py \
  --source <compile.py> --stage compile --report <compile-check.json>
~~~

5. 记录编译选项、产物哈希、性能估计和 warning。

## 产物与完成标准

- TorchScript、`check_model` 通过证据、`compile-check.json` 和编译日志。
- `.hbm` 或 `.hbir` 存在、非空、哈希已登记；没有 `.bin` 伪装。
- 源码证明 `March.BAYES_E` 且无 HAT/`hb_mapper makertbin`。
- Runtime 兼容性未实测时收据必须标记限制。

## 风险与确认

生成新产物为中风险；覆盖模型或复用旧编译目录前确认。不得通过改后缀绕过 Runtime 格式检查。

## 失败与交接

模型检查失败交接 `x5-consistency-diagnostics`；目标或环境错误交接 `x5-environment-probe`。同一编译配置最多两次。

## 按需参考

- `_sources/plugin/source/api_reference/apis/compiler.rst.txt`
- `_sources/plugin/source/quick_start/quick_start.ipynb.txt`
