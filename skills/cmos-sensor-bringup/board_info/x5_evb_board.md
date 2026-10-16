# X5_EVB 板端硬件映射

> X5_EVB 板端 mipi_host 与 i2c bus、电源/pwd 引脚、reset 引脚、lpwm trigger 物理引脚的对应关系。

| mipi_host | i2c bus | 电源 power/pwd 引脚 (lpwm0 通道) | reset 引脚 (gpio_oth / sensor reset-gpios) | lpwm trigger (PWM输出物理引脚) |
|-----------|---------|----------------------------------|--------------------------------------------|--------------------------------|
| mipi_host0 | i2c4 | LSIO_GPIO1_00 = GPIO 347 (= lpwm0_ch0) | AON_GPIO0_00 = GPIO 498 | lpwm0_ch0 → LSIO_SPI5_SCLK (pin 347) |
| mipi_host1 | i2c0 | LSIO_GPIO1_00 = GPIO 347 (= lpwm0_ch0) | AON_GPIO0_00 = GPIO 498 | lpwm0_ch0 → LSIO_SPI5_SCLK (pin 347) |
| mipi_host2 | i2c2 | LSIO_GPIO1_02 = GPIO 349 (= lpwm0_ch2) | AON_GPIO0_04 = GPIO 502 | lpwm0_ch2 → LSIO_SPI5_MISO (pin 349) |
| mipi_host3 | i2c7 | LSIO_GPIO1_03 = GPIO 350 (= lpwm0_ch3) | LSIO_GPIO1_06 = GPIO 353 | lpwm0_ch3 → LSIO_SPI5_MOSI (pin 350) |
