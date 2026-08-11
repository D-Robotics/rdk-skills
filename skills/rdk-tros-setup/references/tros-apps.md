# TROS Apps — 官方出处

本文件记录 rdk-tros-setup 技能"跑应用"路径所依据的官方文档与关键事实。
所有事实均来自本仓库 `.refs/` 下的官方文档克隆，不做二次推断。

## launch 文件位置（FAQ Q1）

- DocScope: `rdk_x_doc/docs/08_FAQ/06_tros_ros.md`（Q1）
- TROS 功能包的 launch 文件通常位于
  `/opt/tros/<tros_distro>/share/<package_name>/launch/`
  （例如 `/opt/tros/humble/share/mipi_cam/launch/`）。

## 运行前的确定性检查顺序（FAQ Q1）

1. 已 `source /opt/tros/setup.bash`（或对应发行版路径）。
2. `ros2 pkg list | grep <pkg>` 确认功能包存在。
3. 按官方文档把示例 config（模型与回灌图片）拷贝到工作目录。

## WebSocket 浏览器可视化排查链（FAQ Q9）

- DocScope: `rdk_x_doc/docs/08_FAQ/06_tros_ros.md`（Q9）
- 排查顺序：
  1. 图像发布节点在发布话题（`mipi_cam` / `usb_cam` / 回放节点）；
  2. WebSocket 节点（`hobot_websocket` 或类似）正常运行；
  3. 电脑与板卡在同一局域网；
  4. AI 结果不显示时检查 WebSocket 节点参数与 AI 消息同步配置。

## 摄像头标定提示（FAQ Q8）

- 启动 USB/MIPI 摄像头节点后提示"标定数据不存在"
  （如 `[usb_camera_calibration.yaml] does not exist!`）属正常现象，
  不影响图像发布。

## 具体应用（人体检测等 NodeHub 应用）

- 各应用的包名、模型与启动命令随板卡与 tros 版本变化；引用前用
  rdk-docs-reference 检索 `05_Robot_development` 与对应 FAQ 原文，
  逐字引用命令并标注 DocScope，不凭记忆拼写包名。
- 源码索引（FAQ Q4）：TROS 功能包源码见 D-Robotics 官方 GitHub 组织。
