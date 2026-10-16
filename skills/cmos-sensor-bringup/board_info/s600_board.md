# S600 板端硬件约束

> 从 sensor_kb/board/s600/ 文档（s600 引脚.png）归纳，每条约束标注来源。DTS 相关字段待源码交叉验证补充。


---

## 0. 转接板类型概览

S600 仅一种转接板（"S600 默认转接板"），含 6 个 MIPI RX 接口，i2c bus 0-5 各对应一个 RX：

| MIPI RX | i2c bus | 接口类型 | Lane | PHY | 用途 |
|----|----|----|----|----|----|
| RX0 (J12) | 0 | GMSL | 4 lane | DPHY | MAX96712 解串器，4 路 GMSL link |
| RX1 (J12) | 1 | GMSL | 4 lane | CPHY | MAX96712 解串器，4 路 GMSL link |
| RX2 (J14) | 2 | GMSL | 4 lane | DPHY | MAX96712 解串器，4 路 GMSL link |
| RX3 (J14) | 3 | GMSL | 4 lane | CPHY | MAX96712 解串器，4 路 GMSL link |
| RX4 (J11) | 4 | 纯 MIPI | 4 lane | DPHY | 纯 MIPI 直连，无解串器 |
| RX5 (J13) | 5 | 纯 MIPI | 4 lane | DPHY | 纯 MIPI 直连，无解串器 |

* 纯 MIPI 接口：RX4、RX5（无解串器、无 POC）
* GMSL 接口：RX0、RX1、RX2、RX3（各挂 1 个 MAX96712）
* RX1/RX3 标 CPHY，RX0/RX2/RX4/RX5 标 DPHY

> 来源：PNG `s600 引脚.png`

**⚠️ 添加新 sensor 前，必须先确认接入的 RX 接口类型（纯 MIPI 还是 GMSL）！**


---

## 1. CSI 接口定义

### 1.1 MIPI RX 接口（默认转接板）

| MIPI RX | Lane 数 | 接口类型 | PHY |
|----|----|----|----|
| RX4 (J11) | 4 lane | 纯 MIPI 直连 | DPHY |
| RX5 (J13) | 4 lane | 纯 MIPI 直连 | DPHY |
| RX0 (J12) | 4 lane | GMSL（MAX96712） | DPHY |
| RX1 (J12) | 4 lane | GMSL（MAX96712） | CPHY |
| RX2 (J14) | 4 lane | GMSL（MAX96712） | DPHY |
| RX3 (J14) | 4 lane | GMSL（MAX96712） | CPHY |

> 来源：PNG `s600 引脚.png`

### 1.2 SoC 可用 MIPI RX CSI Host

> 待 DTS `drobot-camsys-base.dtsi` 交叉验证补充（PNG 未给出 Host 基地址/PHY/Lane 上限）。


---

## 2. I2C 总线映射

### 2.1 I2C Bus（默认转接板）

| MIPI RX | i2c bus |
|----|----|
| RX0 | 0 |
| RX1 | 1 |
| RX2 | 2 |
| RX3 | 3 |
| RX4 | 4 |
| RX5 | 5 |

* GMSL 接口（RX0-RX3）：i2c bus 0-3，经 MAX96712 解串器
* 纯 MIPI 接口（RX4/RX5）：i2c bus 4-5，直连 sensor

> 来源：PNG `s600 引脚.png`


---

## 3. 解串器与串行器约束

### 3.1 MAX96712 解串器规格

* 4 个 GMSL 接口（RX0/RX1/RX2/RX3）各挂 1 个 MAX96712，每个聚合 4 路 GMSL link
* 最大 GMSL sensor 数：16 路（4 个解串器 × 4 link）

> 来源：PNG `s600 引脚.png`

### 3.2 MAX96712 I2C 地址与 PWDN 引脚

| MIPI RX | 解串器型号 | 解串器地址 | 解串器 PWDN 引脚 |
|----|----|----|----|
| RX0 (J12) | MAX96712 | 0x29 | 406 |
| RX1 (J12) | MAX96712 | 0x29 | 407 |
| RX2 (J14) | MAX96712 | 0x29 | 408 |
| RX3 (J14) | MAX96712 | 0x29 | 409 |

> 来源：PNG `s600 引脚.png`

### 3.3 支持的串行器型号

> 待补充（PNG 未给出支持的串行器型号清单）。


---

## 4. POC（Power over Coax）约束

### 4.1 默认转接板 — POC 配置（4 个 GMSL 解串器）

| MIPI RX | poc addr | poc power | poc int | poc map |
|----|----|----|----|----|
| RX0 (J12) | 0x28 | 362 | 374 | 0x0213 |
| RX1 (J12) | 0x28 | 363 | 373 | 0x3210 |
| RX2 (J14) | 0x28 | 364 | 371 | 0x0213 |
| RX3 (J14) | 0x28 | 365 | 370 | 0x3210 |

* ⚠️ `poc power` 列值为 0x28（4 个解串器均同），与 S100 板「POC power GPIO=数字编号」形式不同；该列具体含义（POC 控制器地址 / 供电标识）PNG 未解释，待 DTS 交叉验证
* ⚠️ `poc int` / `poc map` 列值为 GPIO 编号（362\~365 / 370\~374），列含义参照 S100 板推断（int=中断 GPIO、map=地址映射），待 DTS 验证

> 来源：PNG `s600 引脚.png`；列含义参照 `s100_board.md` §4

### 4.2 POC 通用约束

> 待 DTS / experience 交叉验证补充。


---

## 5. GPIO / LPWM 约束

### 5.1 纯 MIPI 接口 — Sensor Power / LPWM（RX4/RX5）

| MIPI RX | sensor power EN | EN 引脚 | peri_port | LPWM |
|----|----|----|----|----|
| RX4 (J11) | CAM_CON0_EN | EMMC_DATA7 | peri_port0_9 (411) | CAM_CON0_LPWM (LPWM1_DOUT2) |
| RX5 (J13) | CAM_CON1_EN | EMMC_DATA_A_STRB | peri_port0_10 (412) | CAM_CON1_LPWM (LPWM1_DOUT3) |

> 来源：PNG `s600 引脚.png`

### 5.2 GMSL 接口 — LPWM / Trigger 配置（RX0/RX1/RX2/RX3）

| MIPI RX | MFP | CAM PWM | LPWM 通道 |
|----|----|----|----|
| RX0 (J12) | MFP5 | CAM0_PWM | LPWM0_DOUT0 |
| RX0 (J12) | MFP7 | CAM1_PWM | LPWM0_DOUT1 |
| RX1 (J12) | MFP5 | CAM2_PWM | LPWM0_DOUT2 |
| RX1 (J12) | MFP7 | CAM3_PWM | LPWM0_DOUT3 |
| RX2 (J14) | MFP5 | CAM4_PWM | LPWM3_DOUT0 |
| RX2 (J14) | MFP7 | CAM5_PWM | LPWM3_DOUT1 |
| RX3 (J14) | MFP5 | CAM6_PWM | LPWM3_DOUT2 |
| RX3 (J14) | MFP7 | CAM7_PWM | LPWM3_DOUT3 |

* GMSL 接口使用 **LPWM → MAX96712 MFP5/MFP7** 方式实现同步触发
* 每个 GMSL 解串器占 2 个 LPWM 通道（MFP5 + MFP7）

> 来源：PNG `s600 引脚.png`

### 5.3 LPWM 控制器

> 待 DTS `drobot-camsys-base.dtsi` 交叉验证补充（PNG 未给出 LPWM 控制器基地址；通道名含 LPWM0/LPWM1/LPWM3）。


---

## 6. 添加新 Sensor 时的硬件约束速查

### 6.1 先确认接入的 RX 接口类型

* 纯 MIPI sensor（如 IMX219 等小分辨率）→ 接 RX4 或 RX5（DPHY，4 lane，无解串器）
* GMSL sensor（SerDes camera）→ 接 RX0/RX1/RX2/RX3（各 1 个 MAX96712，4 link）

### 6.2 I2C Bus 约束

* GMSL 接口 i2c bus：RX0=0、RX1=1、RX2=2、RX3=3（经 MAX96712）
* 纯 MIPI 接口 i2c bus：RX4=4、RX5=5（直连 sensor）

### 6.3 解串器地址约束

* 4 个 MAX96712 解串器地址均为 0x29

### 6.4 POC 约束

* 4 个 GMSL 解串器 poc power 均为 0x28；poc int / poc map 见 §4.1

### 6.5 LPWM 约束

* 纯 MIPI（RX4/RX5）：CAM_CONx_LPWM
* GMSL（RX0-RX3）：MFP5/MFP7 → LPWM 通道，见 §5.2

> 来源：PNG `s600 引脚.png`
