# Changelog

## 2.0.0

- 明确排除 HAT 框架、HAT config、HAT Trainer 和 HAT Model Zoo。
- 将 OE Mapper PTQ `.bin` 与 Plugin QAT `.hbm/.hbir` 拆分为独立合同。
- 固化 X5 Plugin march 为 `March.BAYES_E`，禁止复制 J5 的 `March.BAYES` 示例。
- 引入 V2 skill index，并将 Router、Environment、PTQ、QAT、Runtime 和 Diagnose 拆分为 22 个 Workflow/原子 Skill。
- 增加 8 个 JSON Schema 与 `input/environment/route/plan/state/artifacts/verification/receipt` 运行合同。
- 增加环境探测、PTQ 配置生成/校验/执行、QAT 目标检查、运行收据和 `hrut_somstatus` 解析脚本。
- 增加 ONNX/Caffe PTQ YAML、Runtime C++ 工程模板，以及覆盖全部 Skill 和 HAT/J5/S/X3 隔离的 Eval 矩阵。
- 增加假工具链 PTQ、QAT 隔离、审批门禁、产物哈希、schema 和本地手册检索 smoke；真实 X5 SDK/开发板验证仍需单独记录。
