# S100 12V GMSL 转接板 硬件约束

> 从 s100_board.md 拆分。本文件仅含 12V GMSL 转接板专属信息；末尾「公用信息」为两种转接板共用的通用约束。每条约束标注来源。


---

## 1. 12V GMSL 转接板 — CSI 端口分配

| MIPI RX | Lane 数 | 接口类型 | 解串器编号 | GMSL link 数 |
|----|----|----|----|----|
| RX0 | 4 lane | GMSL | **DES3** | 4 路（VC0\~VC3） |
| RX1 | 4 lane | GMSL | **DES2** | 4 路（VC0\~VC3） |
| RX4 | 4 lane | GMSL | **DES1** | 4 路（VC0\~VC3） |

* 每个 RX 端口各挂 1 个 MAX96712，共 **3 个解串器**
* 每个解串器独立管理 4 路 GMSL link，各自有 VC0\~VC3
* 理论最大连接 **12 路 GMSL sensor**

> 来源：PDF `S100 引脚对应信息.pdf` "S100 12v gmsl 转接板" 表格


---

## 2. 12V GMSL 转接板 — I2C Bus 映射

| MIPI RX | 解串器编号 | 接口类型 | I2C Bus | 解串器地址 | 解串器 PWDN | POC 地址 | POC power | POC int | POC map | sensor power | LPWM |
|----|----|----|----|----|----|----|----|----|----|----|----|
| RX0 4lane | **DES3** | GMSL | **i2c3** (bus=3) | MAX96712@0x29 | GPIO 432 | POC@0x28 | GPIO 419 | GPIO 451 | 0x1320 | - | GPIO_CAM_3 / MFP5 / lpwm0_3 |
| RX1 4lane | **DES2** | GMSL | **i2c2** (bus=2) | MAX96712@0x29 | GPIO 435 | POC@0x28 | GPIO 418 | GPIO 450 | 0x1320 | - | GPIO_CAM_2 / MFP5 / lpwm0_2 |
| RX4 4lane | **DES1** | GMSL | **i2c1** (bus=1) | MAX96712@0x29 | GPIO 452 | POC@0x28 | GPIO 433 | GPIO 506 | - | - | GPIO_CAM_1 / MFP5 / lpwm0_1 |

* **3 个 MAX96712 地址相同（0x29）**，但分别在不同 I2C bus 上，不会冲突
* 每个 DES 的 4 路 serializer 地址也是 0x40\~0x44，在不同 bus 上也不冲突
* **DES1 (RX4) 的 poc_map 为空**，说明 DES1 不通过 POC 供电，直接由 12V 电源供电

> 来源：PDF `S100 引脚对应信息.pdf` "S100 12v gmsl 转接板" 表格


---

## 3. 12V GMSL 转接板 — POC 配置（3 个解串器各不同）

| 解串器 | POC 地址 | POC power GPIO | POC int GPIO | POC map | 供电方式 |
|----|----|----|----|----|----|
| DES1 (RX4) | 0x28 | 433 | 506 | **空** ⚠️ | 直接 12V 供电，不走 POC |
| DES2 (RX1) | 0x28 | 418 | 450 | 0x1320 | POC 供电 |
| DES3 (RX0) | 0x28 | 419 | 451 | 0x1320 | POC 供电 |

* **⚠️ DES1 不使用 POC**，由 12V 电源直接供电，poc_map 为空
* DES2 和 DES3 使用 POC，poc_map = 0x1320
* poc_map 0x1320 是位掩码，控制哪些 GMSL link 使能 POC 供电

> 来源：PDF `S100 引脚对应信息.pdf` "S100 12v gmsl 转接板" 表格


---

## 4. 12V GMSL 转接板 — LPWM / Trigger 配置

| 解串器 | GPIO_CAM | MFP | LPWM 通道 |
|----|----|----|----|
| DES1 (RX4) | GPIO_CAM_1 | MFP5 | lpwm0_1 |
| DES2 (RX1) | GPIO_CAM_2 | MFP5 | lpwm0_2 |
| DES3 (RX0) | GPIO_CAM_3 | MFP5 | lpwm0_3 |

* 12V GMSL 转接板使用 **LPWM → MAX96712 MFP5** 方式实现同步触发
* 每个 DES 独立使用 1 个 LPWM 通道

> 来源：PDF `S100 引脚对应信息.pdf` "S100 12v gmsl 转接板" 表格


---

# 公用信息（两种转接板共用）

> 以下为两种转接板共用的通用约束，6V 默认转接板与 12V GMSL 转接板均适用。


---

## 0. 转接板类型概览

S100 有两种物理转接板，硬件拓扑完全不同：

| 特性 | 默认转接板 | 12V GMSL 转接板 |
|----|----|----|
| MAX96712 数量 | **1 个**（在 RX4） | **3 个**（DES1/DES2/DES3，分别在 RX4/RX1/RX0） |
| 最大 GMSL sensor 数 | 4 路（1 个解串器 × 4 link） | **12 路**（3 个解串器 × 4 link） |
| RX0 用途 | 纯 MIPI（无解串器） | GMSL（DES3） |
| RX1 用途 | 单路 GMSL（无解串器） | GMSL（DES2） |
| RX4 用途 | GMSL（唯一解串器） | GMSL（DES1） |

> 来源：PDF `sensor_kb/board/s100/S100 引脚对应信息.pdf` 两页表格

**⚠️ 添加新 sensor 前，必须先确认使用的是哪种转接板！**


---

## 1. SoC 可用 MIPI RX CSI Host

| MIPI Host | 基地址 | PHY 基地址 | 最大 Lane 数 | CPE 域 |
|----|----|----|----|----|
| mipi_host0 | 0x37420000 | 0x37200000 | 2 lane | CPE0 |
| mipi_host1 | 0x37620000 | 0x37240000 | 2 lane | CPE1 |
| mipi_host4 | 0x37C20000 | 0x37280000 | 4 lane | CPE_LITE |

* mipi_host0 / mipi_host1：仅支持 **2-lane** D-PHY
* mipi_host4：支持 **4-lane** D-PHY
* **不存在 RX2 / RX3**，SoC 未引出

> 来源：DTS `drobot-camsys-base.dtsi`；MAX96712 FDS.pdf Page 1


---

## 2. SoC I2C 控制器

| I2C Bus | 基地址 | 时钟频率 | SCL Pin (cam_port0) | SDA Pin | 域 |
|----|----|----|----|----|----|
| i2c0 | 0x39420000 | 400 kHz | 8 | 9 | 摄像头 |
| i2c1 | 0x39430000 | 400 kHz | 10 | 11 | 摄像头 |
| i2c2 | 0x39440000 | 400 kHz | 12 | 13 | 摄像头 |
| i2c3 | 0x39450000 | 400 kHz | 14 | 15 | 摄像头 |
| **i2c4** | 0x39460000 | **100 kHz** ⚠️ | 16 | 17 | 摄像头 |
| i2c5 | 0x39470000 | 400 kHz | 15 (peri_port0) | 16 (peri_port0) | 外设 |

* **⚠️ i2c4 时钟频率仅 100 kHz**，其余为 400 kHz，GMSL sensor 通信需注意时序

> 来源：DTS `drobot-s100-soc.dtsi`；`drobot-s100-pinctrl.dtsi`


---

## 3. DTS 中的 I2C Bus 号（按 PCB 版本差异）

PDF 中标注的 I2C bus 号是物理连接号，DTS 中的 bus 号取决于 PCB 版本：

### V1.2 / V1.21 PCB（rdk-camsys-v1.dtsi）— 对应默认转接板

| VCON | I2C Bus (DTS) | MIPI Host | 摄像头类型 |
|----|----|----|----|
| vin_vcon0 | **i2c2** (bus=2) | mipi_host0 | MIPI 直连 |
| vin_vcon1 | **i2c3** (bus=3) | mipi_host1 | MIPI 直连 |
| vin_vcon4 | **i2c4** (bus=4) | mipi_host4 | GMSL (MAX96712) |

### V0P5 / V0P6 / V1P0 / V1P1 PCB（rdk-camsys-v0p5.dtsi）— 含 S100P — 对应 12V GMSL 转接板

| VCON | I2C Bus (DTS) | MIPI Host | 摄像头类型 |
|----|----|----|----|
| vin_vcon0 | **i2c1** (bus=1) | mipi_host0 | MIPI 直连 / GMSL |
| vin_vcon1 | **i2c2** (bus=2) | mipi_host1 | MIPI 直连 / GMSL |
| vin_vcon4 | **i2c3** (bus=3) | mipi_host4 | GMSL (MAX96712 DES1) |

**⚠️ 关键区别**：

* V1.x PCB：GMSL 解串器挂在 **i2c4 (100 kHz)** ⚠️
* V0p5 系列 PCB：GMSL 解串器挂在 **i2c3 (400 kHz)**

> 来源：DTS `rdk-camsys-v1.dtsi` 和 `rdk-camsys-v0p5.dtsi` 中 vin_vcon 的 bus 属性


---

## 4. 解串器与串行器约束

### 4.1 MAX96712 解串器规格

| 属性 | 值 |
|----|----|
| GMSL Link 数 | 4 (Link A/B/C/D) |
| GMSL2 前向速率 | 3Gbps 或 6Gbps |
| GMSL2 反向速率 | 187.5 Mbps |
| CSI 输出 | 2x4 Lane / 1x4+2x2 Lane / 4x2 Lane |
| VC 支持 | D-PHY 16 个 / C-PHY 32 个 |
| 数据格式 | RAW8/10/12/14/16/20, RGB565/666/888, YUV422 8/10-bit |

> 来源：MAX96712 FDS.pdf Page 1 "Benefits and Features"

### 4.2 MAX96712 I2C 地址映射（每个解串器内部）

每个 MAX96712 通过控制通道代理转发 I2C 请求到远端：

| 设备 | I2C 地址（7-bit） | 说明 |
|----|----|----|
| MAX96712 自身 | 0x29 | 解串器（本地总线） |
| POC 芯片 | 0x28 | POC 控制（本地总线） |
| MAX9295 主 (prim) | 0x40 | 串行器广播地址（远端） |
| MAX9295 Link A | 0x41 | Link A 串行器（远端） |
| MAX9295 Link B | 0x42 | Link B 串行器（远端） |
| MAX9295 Link C | 0x43 | Link C 串行器（远端） |
| MAX9295 Link D | 0x44 | Link D 串行器（远端） |
| Sensor | 依型号而异 (0x10\~0x36 等) | 远端，通过 MAX96712 代理访问 |
| EEPROM | 依模组而异 (0x50\~0x53 等) | 远端，通过 MAX96712 代理访问 |

* **默认转接板**：1 个 MAX96712 → 所有 sensor/serializer/EEPROM 在同一 I2C bus 上
* **12V GMSL 转接板**：3 个 MAX96712 → 分别在 i2c1/i2c2/i2c3 上，地址虽相同但 bus 不同，不冲突

> 来源：DTS `rdk-camsys-v1.dtsi` 中 max9295 定义；MAX96712 FDS.pdf Page 57 "I2C/UART Control Routing"

### 4.3 支持的串行器型号

| 串行器 | GMSL 模式 | Pipeline 数 | 特点 | S100 使用 |
|----|----|----|----|----|
| MAX9295A | GMSL2 3G/6G | 2 (X/Y) | MIPI + DVP 输入 | 是 |
| MAX9295E | GMSL2 3G/6G | 4 (X/Y/Z/U) | 多 VC 双目 | 是（ov2312） |
| MAX9295D | GMSL2 3G/6G | 2 | 双 CSI 输入 | 否 |
| MAX96717 | GMSL2 3G/6G | 1 | 小尺寸 | 否 |
| MAX96717F | GMSL2 3G | 1 | 低速 | 否 |
| MAX96705 | GMSL1 3.12G | 1 | 兼容 | 否 |

> 来源：MAX96712 FDS.pdf Page 46-49；GMSL2 User Guide_v22.pdf；DTS `camera_mod_sensor_data.h`


---

## 5. POC 通用约束

* POC reset 后 link 稳定可能需要更长时间（LINK_LOCK_TIMEOUT 可能需从 200ms 调到 1600ms）
* 部分模组需要 `serial_rclk_out=1` 以提供 reverse clock 作为时钟源给 sensor

> 来源：mini212g2 \[4167aa8\] timeout 调整；isx031 模组2 \[93b9be8\] rclk_out 配置


---

## 6. LPWM 控制器

| LPWM | 基地址 | 最大通道数 |
|----|----|----|
| lpwm0 | 0x370f0000 | 4 (chn0\~3) |
| lpwm1 | 0x370f1000 | 4 (chn0\~3) |
| lpwm2 | 0x370f2000 | 4 (chn0\~3) |

> 来源：DTS `drobot-camsys-base.dtsi`


---

## 7. CIM（Camera Input Module）

| CIM | 基地址 | 关联 VCON | 关联 MIPI Host |
|----|----|----|----|
| cim0 | 0x37430000 | vin_vcon0 | mipi_host0 |
| cim1 | 0x37630000 | vin_vcon1 | mipi_host1 |
| cim4 | 0x37C30000 | vin_vcon4 | mipi_host4 |

> 来源：DTS `drobot-camsys-base.dtsi`


---

## 8. CSI TX 接口（输出方向）

| 设备 | 基地址 | VCON | 方向 |
|----|----|----|----|
| mipi_dev0 (CSI-TX) | 0x37E10000 | vcon6 (tx_phy link0) | 输出 |
| mipi_dev1 (CSI-TX) | 0x37E20000 | vcon7 (tx_phy link1) | 输出 |

> 来源：DTS `drobot-camsys-base.dtsi`


---

## 9. 添加新 Sensor 时的硬件约束速查

### 9.1 先确认转接板类型

| 问 | 默认转接板 | 12V GMSL 转接板 |
|----|----|----|
| 想接 MIPI 直连 sensor？ | ✅ RX0/RX1 可用 | ❌ RX0/RX1 也是 GMSL，无纯 MIPI 口 |
| 想接 ≤4 路 GMSL sensor？ | ✅ RX4 的 1 个 MAX96712 | ✅ 任选 1 个 DES |
| 想接 >4 路 GMSL sensor？ | ❌ 仅 1 个解串器 | ✅ 最多 12 路（3 个 DES） |
| GMSL I2C bus | bus=2 (i2c2, 400kHz) | bus=1/2/3 (i2c1/2/3, 400kHz) |

### 9.2 MIPI 接口约束

* RX0/RX1 最多 **2 lane**（默认转接板用于 MIPI 直连）
* RX4 支持 **4 lane**（两种转接板都用于 GMSL）
* 12V GMSL 转接板的 RX0/RX1 也改为 4 lane GMSL

### 9.3 I2C Bus 约束

* **⚠️ i2c4 仅 100 kHz**，默认转接板 V1.x PCB 的 GMSL 挂在 i2c4 上需注意
* 每个 VCON 绑定一条 I2C bus，不能混用
* DTS bus 号取决于 PCB 版本（见公用信息「DTS 中的 I2C Bus 号」）

### 9.4 GMSL Link 约束

* 每个 MAX96712 最多 **4 个 GMSL link**（VC0\~VC3）
* serializer 地址：0x40\~0x44（0x40 广播，0x41\~0x44 Link A\~D）
* emode_data 中的 serial_addr 通常填 0x40

### 9.5 POC 约束

* 默认转接板：POC map = 0x1320
* 12V GMSL 转接板 DES1：**不走 POC**（12V 直供），poc_map 为空
* 12V GMSL 转接板 DES2/DES3：POC map = 0x1320
