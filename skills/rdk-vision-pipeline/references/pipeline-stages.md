# Vision Pipeline Stages — 官方出处

本文件记录 rdk-vision-pipeline 技能所依据的官方文档路径与关键事实。
所有事实均来自本仓库 `.refs/` 下的官方文档克隆，不做二次推断。

## Web 展示链路（camera → 推理 → 浏览器）

- DocScope: `rdk_x_doc/docs/03_Basic_Application/03_pydev_demo_sample/RDK_X5/09_web_display_camera_sample.md`
- 关键事实：
  - 示例目录内含 `start_nginx.sh`；运行示例前先执行它启动 Web 服务。
  - 浏览器访问 `http://<开发板 IP>`；文档示例默认 IP 为 `http://192.168.127.10`。
  - 示例默认模型：`/app/model/basic/yolov5x_672x672_nv12.bin`（`--model-path` 参数）。

## 预置模型目录

- DocScope: `rdk_x_doc/docs/03_Basic_Application/03_pydev_demo_sample/RDK_X5/07_usb_camera_sample.md`
  （FAQ："可在 `/app/model/basic` 下查找对应模型"）
- DocScope: `rdk_x_doc/docs/03_Basic_Application/06_multi_media_sp_dev_api/RDK_X5/pydev_multimedia_api_x5/pydev_hbdnn_demo.md`
  （`/opt/hobot/model/<soc>/basic/...`，示例含 x5 与 s100 路径）
- 模型缺失时按示例文档指引从 [rdk_model_zoo](https://github.com/D-Robotics/rdk_model_zoo)
  或 [hobot_model](https://github.com/D-Robotics/hobot_model) 获取。

## C 语言链路（VIO + BPU + 编码）

- DocScope: `rdk_x_doc/docs/03_Basic_Application/06_multi_media_sp_dev_api/RDK_X5/cdev_multimedia_api_x5/cdev_demo.md`
- 关键事实：`/app/cdev_demo/bpu/src/bin/sample -f /app/model/basic/<model>.bin -m <mode>`
  提供摄像头/回灌两种模式的 C 版端到端示例。

## HDMI 显示

- DocScope: `rdk_x_doc/docs/01_Quick_start/display_use/`（按板卡查阅，如 display_rdkx5.md）
- Desktop 版系统运行独占显示的示例前需 `sudo systemctl stop lightdm`（官方要求，
  与 rdk-camera-setup / rdk-headless-mode 中的说明一致）。

## 断点与交接映射

| pipeline_check.sh 断点 | 交接 |
| --- | --- |
| camera | rdk-camera-setup |
| model | rdk-model-deploy |
| bpu | rdk-diagnostic |
| output（display+web 均失败） | display_use 文档 / start_nginx 流程 |
| 卡顿但各段 pass | rdk-model-benchmark（量化单帧延迟）、rdk-diagnostic（降频/CPU） |
| 浏览器访问不了板卡 IP | rdk-network-remote |
