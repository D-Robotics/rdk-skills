# RDK 摄像头检测与出图验证参考

> 信息来源（官方文档）：
> - `rdk_x_doc/docs/01_Quick_start/hardware_introduction/rdk_x5.md`（X5 I2C 总线与 GPIO 使能）
> - `rdk_x_doc/docs/08_FAQ/01_hardware_and_system.md`（X3 I2C 总线）
> - `rdk_x_doc/docs/03_Basic_Application/04_vision/RDK_X5/mipi_camera.md`（MIPI 示例与 lightdm）
> - `rdk_x_doc/docs/03_Basic_Application/04_vision/RDK_X5/usb_camera.md`（USB 示例）

## 官方适配的 MIPI 摄像头（X5）

| 摄像头 | 像素 | 典型 I2C 地址 |
| --- | --- | --- |
| IMX219 | 800W | 0x10 |
| OV5647 | 500W | — |
| IMX477 | 1230W | — |

连接方式：22pin 同向排线，金属面背对黑色卡扣插入连接器。

## X5 的 I2C 探测步骤（官方原文步骤）

靠近网口的 mipi_host0 接口（总线 6）：

```bash
echo 353 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio353/direction
echo 0 > /sys/class/gpio/gpio353/value
sleep 0.1
echo 1 > /sys/class/gpio/gpio353/value

i2cdetect -y -r 6
```

远离网口的 mipi_host2 接口（总线 4）：GPIO 换为 351，总线换为 4。

成功时输出中会出现 sensor 地址（IMX219 为 `10`）。

## X3 的 I2C 探测（官方 FAQ）

```bash
sudo i2cdetect -y -r 1  # 扫描 i2c-1 总线
sudo i2cdetect -y -r 2  # 扫描 i2c-2 总线
```

## 出图验证路径

| 场景 | 官方示例 | 说明 |
| --- | --- | --- |
| MIPI 无显示器验证 | `/app/pydev_demo/08_mipi_camera_sample/02_mipi_camera_dump.py` | 保存 1920x1080 YUV 文件 |
| MIPI 实时检测 | `.../01_mipi_camera_yolov5s.py` | YOLOv5 推理 + HDMI 显示 |
| USB 摄像头 | `/app/pydev_demo/07_usb_camera_sample/` | 设备节点通常为 `/dev/video0` |

**Desktop 版系统 + HDMI 显示**必须先关闭桌面服务（官方要求）：

```bash
sudo systemctl stop lightdm
```

## 扫不到地址时的排查顺序（官方 FAQ）

1. 排线方向是否正确（金属面背对卡扣）。
2. `i2cdetect` 的总线号是否与摄像头实际连接的 MIPI 接口对应。
3. 是否为官方适配的摄像头型号。
