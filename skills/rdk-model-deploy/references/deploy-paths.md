# RDK 模型部署路径参考

> 信息来源（官方文档）：
> - `rdk_x_doc/docs/04_model_zoo_intro.md`（Model Zoo 概述）
> - `rdk_x_doc/docs/03_Basic_Application/03_pydev_demo_sample/RDK_X5/`（pydev_demo 示例）
> - `rdk_x_doc/docs/07_Advanced_development/04_toolchain_development/`（工具链）
> - `rdk_s_doc/docs/04_Algorithm_Application/`（S 系列 .hbm 模型与示例）

## RDK Model Zoo（官方定义）

RDK Model Zoo 是 D-Robotics 面向 RDK 系列开发板提供的 BPU 模型示例与工具集合，
收录图像分类、目标检测、实例分割、姿态估计、OCR、多模态等领域的 BPU 可运行模型，
并提供 **原始模型（PyTorch/ONNX）→ 定点量化转换 → 推理运行 → 结果解析 → 示例验证**
的完整参考实现。

- GitHub 仓库：https://github.com/D-Robotics/rdk_model_zoo
- 用户手册：https://developer.d-robotics.cc/model_zoo_doc/model_zoo_intro
- 社区开源共建项目，接受 PR 贡献。

## 板端 Python 示例（官方镜像内置）

`/app/pydev_demo/` 下按序号组织（X5 版）：

| 目录 | 任务 |
| --- | --- |
| 01_classification_sample | 图像分类 |
| 02_detection_sample | 目标检测 |
| 03_instance_segment_sample | 实例分割 |
| 04_pose_sample | 姿态估计 |
| 06_segment_sample | 语义分割 |
| 07_usb_camera_sample | USB 摄像头推理 |
| 08_mipi_camera_sample | MIPI 摄像头推理 |
| 09_web_display_camera_sample | Web 端显示 |

## 部署路径决策

```
有标准视觉任务需求
 ├─ 是 → Model Zoo 有对应模型？
 │        ├─ 是 → 用 Model Zoo 发布物 + 参考实现（最快路径）
 │        └─ 否 → 开发机侧 hb_mapper 转换自有模型（工具链文档）
 └─ 只想学 API → /app/pydev_demo 示例起步
```

## 关键约束

- 模型与 BPU 架构强绑定，互不通用：X 系列 `.bin`（Bernoulli / Bayes-e / Bayes），
  S 系列 `.hbm`（Nash-e / Nash-p，模型名含 `nashe` / `nashp` 标签，如
  `yolo11n_detect_nashe_640x640_nv12.hbm`）。
- X 系列模型文件官方建议放 `/userdata`；S 系列官方预置模型位于 `/opt/hobot/model/`，
  Model Zoo 发布物按板卡分目录（archive.d-robotics.cc/downloads/rdk_model_zoo/
  rdk_s100 与 rdk_s600）。
- 部署验证工具：`hrt_model_exec model_info`（接口信息）与 `perf`（性能，
  见 rdk-model-benchmark）。
