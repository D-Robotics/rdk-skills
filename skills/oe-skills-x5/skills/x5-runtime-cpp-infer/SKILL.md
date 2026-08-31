---
name: x5-runtime-cpp-infer
description: 生成或审查 X5 BPU SDK C++ 推理工程；当用户有 X5 .bin、I/O 合同和 Runtime SDK，需要实现模型加载、张量内存、hbDNNInfer、输出回读与释放时使用。模板只覆盖单输入已对齐 raw tensor，多输入或图像前处理必须按模型合同扩展。
version: 1.0.0
license: Apache-2.0
---

# X5 Runtime C++ 推理

## 目标与边界

基于 X5 Runtime 手册创建可审阅的 CMake 工程。不得把示例中硬编码的 `224x224 nv12` 当成任意模型的通用输入。

## 输入合同

- 经过验证的 X5 `.bin`、模型名称和所有 I/O properties。
- X5 DNN SDK 根、Arm GNU Toolchain 根和目标板端 Runtime 版本。
- 可复现输入、预处理/对齐方法和参考输出。

## 前置检查

1. `hb_model_info` 证明 `bayes-e` 并记录输入顺序。
2. 使用 `hbDNNGetInput/OutputTensorProperties` 获取 shape、layout、dtype 和 `alignedByteSize`。
3. 明确 cache flush、量化输出解析和多输入内存责任。

## 执行步骤

1. 复制 `.drobotics/platforms/x5/assets/runtime-cpp/` 到新的工程目录。
2. 模板只接受一个已经按 `alignedByteSize` 排列的 raw 输入；若模型多输入或需要 NV12 padding，先实现并单测专用 packing。
3. 构建：

~~~bash
export LINARO_GCC_ROOT=<arm-toolchain-root>
export X5_DNN_ROOT=<x5_aarch64/dnn>
bash build.sh <new-build-dir>
~~~

4. 上板运行前检查动态库路径；执行后保存每个输出 tensor raw 文件。
5. 用离线参考程序按 dtype/quantization/layout 解析并比较输出。

## 产物与完成标准

- C++/CMake/build 脚本、构建日志和交叉编译器版本。
- 所有 API 返回码被检查，输入/输出内存和 task/model handle 被释放。
- 板端运行成功且输出与参考在定义容差内一致。

## 风险与确认

生成代码为中风险；上传/执行到新目录为中风险。覆盖板端二进制、修改库或环境变量全局配置前必须确认。

## 失败与交接

编译/API 问题交接 `x5-model-diagnostics`；输出问题交接 `x5-consistency-diagnostics`。不要用硬编码 shape 绕过模型属性。

## 按需参考

- `_sources/runtime/source/runtime_dev.rst.txt`
- `_sources/runtime/source/bpu_sdk_api/bpu_sdk_api.rst.txt`
