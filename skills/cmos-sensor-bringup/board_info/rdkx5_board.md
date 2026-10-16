# RDK X5 板端硬件映射

> RDK X5（X5 MD：RDK X5 Module + IO 载板）两路 22pin MIPI CSI。来源：X5 芯片用户手册 2.0.0《X5 MD 开发板使用指南》摄像头接口表；`x5-rdk.dtsi` 的 `mipi_host` / `lpwm1` 节点。手册未给出单独的 power/pwd GPIO，本表不填。

| 座子 | mipi_host | lane | i2c bus | reset 引脚 (gpio_oth / sensor reset-gpios) | lpwm trigger | MCLK |
|------|-----------|------|---------|--------------------------------------------|--------------|------|
| CAM1（接口 10） | mipi_host0、mipi_host1 共用 | 4 lane（CSI0&1） | i2c6 | LSIO_GPIO1_06 = GPIO 353 | LSIO_LPWM1_0（lpwm1_ch0，lpwm_chn=4）→ LSIO_SPI3_SCLK | LSIO_SENSOR0_MCLK |
| CAM2（接口 9） | mipi_host2、mipi_host3 共用 | 4 lane（CSI2&3） | i2c4 | LSIO_GPIO1_04 = GPIO 351 | LSIO_LPWM1_1（lpwm1_ch1，lpwm_chn=5）→ LSIO_SPI3_SSN | LSIO_SENSOR1_MCLK |

## 约束

- `x5-rdk.dtsi`：`&lpwm1` 使能 `pinctrl_lpwm1_0`、`pinctrl_lpwm1_1`。mipi_host0 与 mipi_host1 共用一组 MCLK 和 GPIO；mipi_host2 与 mipi_host3 共用另一组。
- 默认 MCLK 不由 SoC snrclk 输出。`mipi_host0` / `mipi_host2` 注释为外部有源晶振，节点不配置 `snrclk-idx`。22pin 模组（IMX219、IMX477、OV5647）IO 电平选 3.3V，MCLK 在座子上。22pin 转 24pin 转接板自带 24M 有源晶振，IO 电平选 1.8V，用于对接 SC230AI、SC132gs、IMX415 等 EVB 模组。模组或转接板自带 24MHz 时，不改 `x5-rdk.dtsi`，也不写 `snrclk_en`。sensor 手册只写 INCK=24MHz，不能当成要改 DTS。
- 例外：必须由 SoC 提供 MCLK，且接上后 `i2cdetect` 扫描不到外设时，只改本次接入的那一个 `mipi_host`（`arch/arm64/boot/dts/hobot/x5-rdk.dtsi`）。四项缺一不可，不得改其它 host：

  | 节点 | pinctrl-0（enable） | pinctrl-1（disable） | snrclk-idx |
  |---|---|---|---|
  | `mipi_host0` | `pinctrl_sensor0_mclk` | `lsio_gpio0_24` | 0 |
  | `mipi_host1` | `pinctrl_sensor1_mclk` | `lsio_gpio0_25` | 1 |
  | `mipi_host2` | `pinctrl_sensor2_mclk` | `lsio_gpio0_26` | 2 |
  | `mipi_host3` | `pinctrl_sensor3_mclk` | `lsio_gpio0_27` | 3 |

  节点同时写 `pinctrl-names = "enable", "disable"`。改完后在 `rdk-x5-bsp` 根目录执行 `sudo ./mk_kernel.sh`，再执行 `sudo ./mk_debs.sh hobot-dtb`。安装该 deb 与重启前必须先向用户确认。新 DTB 生效后，只对这一路写 sysfs：`echo <MCLK_Hz> > /sys/class/vps/mipi_hostN/param/snrclk_freq`，然后 `echo 1 > /sys/class/vps/mipi_hostN/param/snrclk_en`。
- lpwm 物理脚与 `lpwm_chn` 来自 X5 LPWM 映射：LPWM1 ch0 = `pinctrl_lpwm1_0` = LSIO_SPI3_SCLK = lpwm_chn 4；LPWM1 ch1 = `pinctrl_lpwm1_1` = LSIO_SPI3_SSN = lpwm_chn 5。
