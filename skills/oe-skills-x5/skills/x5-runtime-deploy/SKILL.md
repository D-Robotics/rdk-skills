---
name: x5-runtime-deploy
description: 编排 X5 Runtime 模型门禁、板端上传、命令行/C++ 推理、正确性、性能与资源验证；当用户要上板运行 X5 .bin、使用 hrt_model_exec 或 BPU SDK 时使用。Plugin .hbm/.hbir 只有在实际 Runtime 兼容证据充分时才接收；不使用 S 系列 UCP。
version: 1.0.0
license: Apache-2.0
---

# X5 Runtime 部署工作流

## 目标与边界

完成“模型可被目标 Runtime 加载、输入正确、输出正确、性能有证据”的板端闭环。当前 Runtime 手册主路径是 X5 `.bin`；Plugin `.hbm/.hbir` 不得未经验证直接送入 `.bin` API。

## 输入合同

- 模型、来源/哈希、模型 I/O 和可复现输入/参考输出。
- 板卡标识、镜像/Runtime 版本、架构、连接方式和新部署目录。
- 选择命令行、C++、Python（应转 `x5-bpu-python-api`）或性能目标。

## 前置检查

1. `.bin` 先用 `hb_model_info` 证明 `BPU march: bayes-e`。
2. Plugin `.hbm/.hbir` 必须有当前 Runtime API/工具明确支持的证据；`.hbir` 通常仍是中间产物，证据不足即 `blocked`。
3. 板卡必须是 X5/aarch64，连接可达，目标路径不会覆盖业务文件。
4. 输入 layout、dtype、对齐、色彩和前处理责任必须来自模型信息与编译合同。

## 执行步骤

1. 记录板端版本、模型信息和部署计划。
2. 上传到新目录并回读大小/哈希；不替换系统 Runtime。
3. 快速验证时按本地手册使用 `hrt_model_exec`，不得凭记忆补参数。
4. C++ 应用交接 `x5-runtime-cpp-infer`；板端 Python 交接 `x5-bpu-python-api`。
5. 用固定输入比较 Runtime 与参考输出；再交接性能和监控 Skills。
6. 保存命令、板端日志、输出文件和验证结果。

## 产物与完成标准

- 模型格式/Runtime 兼容证据、板端回读哈希和执行日志。
- 模型 I/O、输入样本、输出 shape/dtype 与正确性比较明确。
- 功能通过后才记录性能；板端不可用时不得宣称部署成功。

## 风险与确认

上传到新目录为中风险；覆盖模型、替换 Runtime、停止进程、修改系统配置或清理目录为高风险并需明确确认。当前 Pack 不执行烧录/分区。

## 失败与交接

环境/加载 → `x5-environment-probe`；输出不一致 → `x5-consistency-diagnostics`；性能异常 → `x5-performance-diagnostics`。同一部署修复最多两次。

## 按需参考

- `_sources/runtime/source/runtime_dev.rst.txt`
- `.drobotics/platforms/x5/policies/risk-policy.md`
