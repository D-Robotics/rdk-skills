# Conversion Failure Triage — 板端报错反推转换侧问题

本文件帮助 rdk-model-deploy 在板端把"模型加载/推理失败"归因到转换侧（开发机
`hb_mapper` / 工具链）或板端环境，避免用户在错误的一侧反复排查。
模型格式与架构事实来自本仓库既有 references 与官方文档；工具链细节以
`rdk_x_doc/docs/07_Advanced_development/04_toolchain_development/` 与
`rdk_x_doc/docs/08_FAQ/05_toolchain.md` 为准。

## 归因决策表

| 板端现象 | 最可能原因 | 归属侧 | 下一步 |
| --- | --- | --- | --- |
| `model_info` 解析失败 / 加载即报错 | 模型架构与板卡 BPU 不匹配（march 错误） | 转换侧 | 核对下表架构标签；用对应板卡重新转换或下载对应 Model Zoo 发布物 |
| X 系列板卡上加载 `.hbm` / S 系列上加载 `.bin` | 模型格式与系列不符 | 转换侧 | `.bin`=X 系列、`.hbm`=S 系列，不可互换 |
| 输出全零 / 乱码但加载成功 | 输入前处理不符（NV12/RGB 排布、量化系数） | 板端集成 | 对照 Model Zoo 参考实现核对前处理 |
| `ion alloc failed` | 板端 CMA/ION 余量不足 | 板端环境 | 交接 rdk-memory-audit |
| 精度明显劣于浮点模型 | 量化校准问题 | 转换侧 | 指引官方 PTQ 精度调优文档（开发机侧） |

## 架构标签对照（转换时的 march 参数必须与板卡一致）

| 板卡 | BPU 架构 | 模型格式 |
| --- | --- | --- |
| RDK X3 | Bernoulli | .bin |
| RDK X5 | Bayes-e | .bin |
| RDK Ultra | Bayes | .bin |
| RDK S100 / S100P | Nash-e（模型名含 `nashe`） | .hbm |
| RDK S600 | Nash-p（模型名含 `nashp`） | .hbm |

## 边界声明

- 模型转换/量化本身（`hb_mapper` 及参数调优）在**开发机侧**执行，超出本
  设备侧技能范围；定位为转换侧问题后，指引用户查阅
  `07_Advanced_development/04_toolchain_development` 与 FAQ `05_toolchain.md`，
  用 rdk-docs-reference 检索并引用原文。
- 本表仅覆盖板端可观察的证据映射，不背诵工具链参数。
