# Sensor 代码编写规律

---

## 0.2 待提取参数（参数提取总纲）

提取参数时，逐参数对照本节填写。每参数三要素：含义 / 提取规律（如何从文档取值）/ 确认判据（什么情况下需用户确认）。出确认清单前，按 SKILL.md『入清单前的过滤判据』逐点回查本节——"确认判据"写"不确认"的按"提取规律"直接填值不进清单；写明需确认情况的，仅在命中且文档确无此信息时才进清单询问。

§0.2.2 是封闭白名单:白名单外的参数一律不提取、不询问。没有判据等于无此参数,不是待确认。向用户确认的唯一来源是白名单内某参数的"确认判据"明写需确认、且文档确无该信息。

### 0.2.1 类型校验（提取参数前首条执行）
用户在入口已指定 camera 类型为 SerDes。提取参数时校验文档内容是否相符：文档须含 Serializer 芯片描述（如 MAX9295/MAX96717/MAX96793 等）。若文档无 Serializer 芯片描述，则停下询问用户（类型与文档不符），不得自动改类型。

### 0.2.2 待提取参数逐项

#### VENDOR
- 含义：供应商
- 提取规律：文档直读（如 BLDCAS/OFILM/MINGMO 等）
- 确认判据：未提取到VENDOR时→向用户确认

#### K{X} 加串器大类
- 含义：加串器芯片大类，对应 `camera_serial_kind_t`，取值：K0=MAXIM(美信), K1=TI(德州仪器), K2=RLC(仁若)
- 提取规律：MAX9295/MAX967xx→K0(MAXIM)；TI 系列→K1；RLC→K2。判据由 serializer 型号决定
- 确认判据：未提取到加串器大类时→向用户确认

#### M{XX} 输入主频(MCLK)
- 含义：输入主频 MCLK=XXMHz，**Sensor 输入时钟频率（XCLK）= Serializer 输出的 MCLK 频率**，两者是同一路时钟信号
- 提取规律：从模组文档提取 Sensor 输入时钟频率（XCLK）=MCLK，按优先级查找：①文档直接标注 Sensor 输入时钟/XCLK→直接使用；②文档标注 Serializer 输出时钟（MCLK/MFP 输出时钟，如"MFP4 输出时钟 24MHz"）→该值即为 XCLK=MCLK。编码 M{XX}（24MHz→M24）。
- 确认判据：未提取到加串器类时→向用户确认

#### F{XXX} FoV
- 含义：水平视场角
- 提取规律：文档直读水平方向 FoV（如 H:195→F195）
- 确认判据：未提取到FoV时→向用户确认

#### D{XX} DataType
- 含义：输出数据类型，对应 `camera_sensor_emode_datatype_t`，取值：D4=YUV422 8bit(0x12), D8=RAW8(0x2A), D10=RAW10(0x2B), D12=RAW12(0x2C)
- 提取规律：YUV422 8bit→D4(0x12)；RAW8→D8(0x2A)；RAW10→D10(0x2B)；RAW12→D12(0x2C)
- 确认判据：未提取到DataType时→向用户确认

#### B{X} Bayer
- 含义：Bayer Pattern，对应 `camera_sensor_bayer_t`，取值：B0=RGGB, B1=RCCC, B2=RCCG, B3=RCCB, B4=CCCC, B5=RGBIR_2X2, B6=RGBIR_4x4, B7=RYYCy, B8=RGBW
- 提取规律：仅 RAW(D8/D10/D12)适用，按 datasheet 确认 Bayer 序列(B0=RGGB 等)；D4(YUV422)及内置 ISP/已去马赛克输出→**不配 B**，不列为缺失、不询问
- 确认判据：RAW(D8/D10/D12) 并且 未提取到Bayer时→向用户确认

#### P{X} 存储类型
- 含义：内部存储硬件类型，取值：P0=FLASH, P1=EEPROM
- 提取规律：文档有 EEPROM I2C 地址/EEPROM → P1(EEPROM)；有 FLASH I2C 地址/描述→P0(FLASH)；均无→不配 P。不得因文档未单独标"存储类型"字样而列为缺失
- 确认判据：不确认

#### S{X} 加串器型号
- 含义：串行器芯片型号，对应 `camera_serial_types_t`，取值：S0=MAX9295A, S1=MAX96717, S2=MAX96717F, S3=MAX96793, S4=MAX9295E
- 提取规律：MAX9295A→S0；MAX96717→S1；MAX96717F→S2；MAX96793→S3；MAX9295E→S4
- 确认判据：未提取到加串器型号时→向用户确认

#### R{X} Reset PIN
- 含义：ResetPIN=MFPX，连接 Sensor 复位所用的 PIN
- 提取规律：文档"MFPx reset/输出复位信号"→R{x}。
- 确认判据：未提取到Reset PIN时→需向用户确认复位所接 MFP 编号

#### T{X} Trig PIN
- 含义：TrigPIN=MFPX，连接 Sensor 同步所用的 PIN
- 提取规律：文档"MFPx 输出触发信号"→T{x}；同时附：有 MFP 触发信号→需配置硬件触发同步曝光(LPWM+trigger setting)，见 §0.2.3。文档无触发引脚描述→不配触发，需用户确认是否无触发
- 确认判据：未提取到Trig PIN时→需向用户确认是否无触发

#### L{X} GMSL 速率
- 含义：GMSL 速率编码，取值：L3=GMSL2 3Gbps, L6=GMSL2 6Gbps
- 提取规律：文档"GMSL2 3Gbps"→L3；"6Gbps"→L6。文档明确标注时必填，不可因参照旧 emode 无 L 而省略
- 确认判据：未提取到GMSL 速率时→向用户确认

#### E{X} 错误 PIN
- 含义：连接 Sensor 错误所用的 PIN 编号（不是 EEPROM 地址）
- 提取规律：文档"MFPx 输出错误信号"→E{x}。文档无错误引脚描述→不配 E，需用户确认
- 确认判据：未提取到错误 PIN时→需向用户确认是否确无错误引脚

#### A{X} EEPROM 内参布局
- 含义：EEPROM 内参读取地址布局，由 `vin_sensor_emode_parse(si, 'A')` 解析为 `address_width`，用于 `get_intrinsic_params_from_flash()` 中 switch 选择从 EEPROM 哪个基址读取 sensor 内参标定数据。取值：A1=FLASH_ADDR1, A2=FLASH_ADDR2, A3=FLASH_ADDR3，其他值走 default 报错返回 -1
- 提取规律：文档须明确给出 EEPROM 烧录布局才能填(A1/A2/A3)；文档无 EEPROM 烧录布局描述→**不配 A**，不得参照其他模组推断添加
- 确认判据：不确认

#### serial_addr
- 含义：串行器 I2C 地址(7bit)
- 提取规律：文档 8bit 地址右移1位(0x80→0x40)
- 确认判据：未提取到serial_addr时→向用户确认

#### sensor_addr
- 含义：sensor I2C 地址(7bit)
- 提取规律：文档 8bit 地址右移1位(0x34→0x1A)
- 确认判据：未提取到sensor_addr时→向用户确认

#### eeprom_addr
- 含义：EEPROM I2C 地址(7bit)
- 提取规律：文档 8bit 地址右移1位(0xa0→0x50)；无 EEPROM→不配
- 确认判据：不确认

#### serial_rclk_out / rclk_mfp
- 含义：串行器反向时钟使能/引脚
- 提取规律：文档有 MFP 引脚输出时钟 XXMHz→serial_rclk_out=1、rclk_mfp=MFP 编号；否则=0。该 XXMHz 同时满足 M{XX} 取值，同一条信息不得只用于一个参数
- 确认判据：未提取到serial_rclk_out / rclk_mfp时→向用户确认

#### ext_trig_mfp
- 含义：额外触发引脚(驱动自定义)
- 提取规律：文档标注多个 trigger MFP→按 nibble 编码；单个 trigger MFP则ext_trig_mfp=0；没有trigger MFP则ext_trig_mfp=0
- 确认判据：不确认

#### sensor
- 含义：sensor 名称（驱动目录名 / SENSOR_NAME，如 isx031std）
- 提取规律：对应 driver 中 sensor 名称(SENSOR_MNAME)
- 确认判据：未提取到 sensor 名称时→向用户确认

#### sensor_mode
- 含义：sensor 运行模式
- 提取规律：固定 NORMAL_M(1)。触发同步由 config_index 触发位承载，不用 SLAVE_M
- 确认判据：不确认

#### fps
- 含义：帧率
- 提取规律：文档直读(如 30fps)
- 确认判据：未提取到fps时→向用户确认

#### width/height
- 含义：分辨率
- 提取规律：文档直读
- 确认判据：不确认

#### config_index
- 含义：功能配置位掩码
- 提取规律：文档中没有标注sync MFP或trigger MFP→config_index=0, 文档中标注一个sync MFP或一个trigger MFP→config_index=512, 文档标注2以上个 sync MFP或两个以上trigger MFP→config_index=512。
- 确认判据：没有根据提取规律获取到值→向用户确认

#### calib_lname
- 含义：标定库名
- 提取规律：标定团队提供；无→"disable"
- 确认判据：不确认

#### poc addr/map
- 含义：POC 地址/映射
- 提取规律：来自板级文档(如 s100_6v: addr=0x28, map=0x1320)
- 确认判据：未提取到poc addr/map时→向用户确认

#### deserial name/addr
- 含义：解串器名称/地址
- 提取规律：来自板级文档(如 max96712@0x29)
- 确认判据：未提取到deserial name/addr时→向用户确认

#### link_desp
- 含义：link 描述
- 提取规律："name:extra_mode@config_index" 格式
- 确认判据：不确认

#### linelenth
- 含义：行长度=HTS
- 提取规律：从 init 序列 HTS 寄存器取(或公式计算)；与 sensor HTS 寄存器一致
- 确认判据：不确认

#### framelenth
- 含义：帧长度=VTS
- 提取规律：从 init 序列 VTS 寄存器取；与 sensor VTS 寄存器一致
- 确认判据：不确认


#### chip_id_reg / chip_id
- 含义：芯片ID寄存器/期望值
- 提取规律：必须从当前 sensor datasheet 确认，不参考其他 sensor。文档无→询问用户；用默认 0xA55A 跳过检测须用户确认
- 确认判据：未提取到chip_id_reg/chip_id→须用户确认是否使用默认 0xA55A 跳过检测

### 0.2.3 触发同步曝光附加动作
当 T 字段判据命中（文档有 MFP 触发信号）时，除填 T{x} 外，还须在 vp_sensor 配置中：
1. 依据 fps 在 `vin_node_attr.lpwm_attr.lpwm_chn_attr[]` 使能并增加各 link 的 LPWM 配置：`period`=1s/fps 取整(30fps→33333us)；`offset`=1000000us−(period×fps)(30fps→10us)；`duty_time`=默认100us
2. 在 `deserial_config.gpio_mfp[CAMERA_DES_GPIO_TRIG0]` 增加 DES 触发 GPIO 映射(如 0x5)
触发模式由 config_index 触发位(如 TRIG_SHUTTER_SYNC=512)承载，sensor_mode 用 NORMAL_M(1)而非 SLAVE_M

---


## 23. 常见遗漏点清单 *(新增)*

| # | 遗漏项 | 后果 |
|---|--------|------|
| 1 | 忘记在 `vp_sensors.c` 中 extern 声明和数组注册 | 用户态找不到该 sensor |
| 2 | 忘记在 `sensor_emode[]` 中添加 `SENSOR_EMADD` | 运行时匹配不到 emode 数据 |
| 3 | 忘记在 `emode_data[]` 中添加条目 | data 指针为空/未初始化 |
| 4 | 双目模组忘记配置 vc1 override | 右目数据丢失 |
| 5 | DVP_NEXT 忘记在 `camera_mod_sensor_data.h` 添加枚举 | 编译不过或运行时接口类型不识别 |
| 6 | 新串行器型号忘记在 `max_common.c` 添加 `gmsl_modes_table` | 串行器初始化失败 |
| 7 | 新串行器型号忘记在 `max_serial_pipeline_init()` 添加 case | pipeline 未初始化 |
| 8 | 双目 `vin_ichn_attr.width` 未翻倍 | 只显示左目图像 |
| 9 | 新供应商 AWB 参数未添加 | 颜色偏差 |
| 10 | 忘记设置 `serial_rclk_out=1` / `rclk_mfp`（文档有MFP输出时钟标注时） | Sensor无MCLK导致I2C不通 |
| 11 | 触发模式写完寄存器后忘记 `usleep` | 触发不稳定 |
| 12 | 新模组供应商忘记添加标定库 `.so` 文件 | 标定流程失败 |
| 13 | 新模组供应商忘记更新 `tuning_menu.sh` 菜单 | 调优工具中不可选 |
| 14 | MAX96712 DT overwrite mask 设置错误（0xF3 vs 0xFC） | 数据类型解析错误 |
| 15 | DVP pipe 编号与 link 不对应（先统计后统一配置） | 多路 DVP sensor 数据混乱 |
| 16 | 初始化序列末尾包含 stream-on 命令（如 0x0100=0x01） | 系统就绪前 sensor 输出数据 |
| 17 | HTS 寄存器修改后忘记同步更新 vp_sensor linelenth | MIPI 接收器配置不匹配，帧率异常 |
| 18 | MIPI host MCLK 未在 I2C 探测前启用 | 需要时钟的 sensor（如 imx586）无法被 I2C 检测 |
| 19 | Gain LUT 的 gain_max 值与实际 LUT 结构不匹配 | AE 增益控制异常 |
| 20 | lines_per_second/exposure_time_max 计算使用了错误 VTS | AE 曝光控制异常 |
| 22 | CV4006 等 sensor stream on/off 值方向与 OV 系列相反 | stream 控制反向 |
| 23 | AF VCM 初始化未在 sensor_init 中调用 | 自动对焦不工作 |
| 24 | PDAF 输出寄存器未在 init 序列中启用 | PDAF 数据不输出 |
| 25 | `support_sensor_mode` 字段缺失 | 不支持的 sensor_mode 导致程序崩溃 |
| 26 | 非 DOL2 sensor 错误设为在线模式 | 多路冲突 |
| 27 | 无 T 字段命中或 config_index 未含触发位时误启用 LPWM | 误触发同步曝光 |
| 28 | Serializer 双目 pipe 只配置单 VC | 右目数据丢失 |

---


## 1. 必须修改的文件列表及顺序

新增 sensor 按「驱动库 → vp_sensor 配置 → 解串器/串行器（SerDes 特有）」三阶段依次修改。文件路径 = 项目根目录 + project_info/<项目名>_project.conf 中的相对路径 + 下表路径。

### 阶段一：sensor 驱动库（`drivers/sensor/<sensor>std/`）

| 序号 | 文件 | 操作 | 说明 |
|------|------|------|------|
| 1 | `drivers/sensor/<sensor>std/Makefile` | 新建 | 模板化，TARGET 自动取目录名 |
| 2 | `drivers/sensor/<sensor>std/version.mk` | 新建 | 版本号，默认 1.0.0 |
| 3 | `drivers/sensor/<sensor>std/inc/<sensor>std_setting.h` | 新建 | emode 枚举、init 序列、stream on/off、触发序列、gain LUT、AWB 标定宏 |
| 4 | `drivers/sensor/<sensor>std/<sensor>std_utility.c` | 新建 | emode_data、SENSOR_EMADD 注册、config_index_funcs、sensor_init/start/stop、模块注册 |

### 阶段二：vp_sensor 配置（`src/vp_sensors/<sensor>/`）

| 序号 | 文件 | 操作 | 说明 |
|------|------|------|------|
| 5 | `src/vp_sensors/<sensor>/linear_<width>x<height>_<format>_<fps>fps[_<lane>lane].c` | 新建 | 每个分辨率/帧率组合一个配置文件，内含 8 个结构体 + 顶层 vp_sensor_config_t |
| 6 | `src/vp_sensors/vp_sensors.c` | 修改 | extern 声明 + vp_sensor_config_list[] 数组项 |

### 阶段三：解串器/串行器配置（SerDes 特有，按需）

| 序号 | 文件 | 操作 | 触发条件 |
|------|------|------|------|
| 7 | `drivers/deserial/max96712/max96712_setting.h` | 修改 | YUV 双目（加 vc1 override 表）/ POC reset 后需更长 lock（改 LINK_LOCK_TIMEOUT） |
| 8 | `drivers/deserial/max96712/max96712_utility.c` | 修改 | YUV 双目 vc 路由 / DVP pipe 编号修复 |
| 9 | `drivers/sensor/serial/max_serial_utility.c` | 修改 | 新串行器型号（加 pipeline_init + case）/ 新接口类型（加 DVP_NEXT 分支） |
| 10 | `drivers/inc/develop/camera_mod_sensor_data.h` | 修改 | 新串行器型号（camera_serial_types_t 加枚举）/ 新接口类型（camera_sensor_inf_type_t 加枚举） |
| 11 | `drivers/deserial/_common/max_common.c` | 修改 | 新串行器型号（gmsl_modes_table 加条目） |

### 配套文件（非代码模板，列出供完整）

| 文件 | 说明 |
|------|------|
| `sensor_calibration/lib_<VENDOR>_<xxx>.so` | 新供应商标定库，文件名 = SENSOR_EMADD 第3参 calib_lname |
| `tuning_tool/cfg/matrix/tuning_<sensor>_<vendor>_*/` | tuning 配置目录（hb_j6dev.json / lpwm_<fps>fps.json / vpm_config.json / sensor_debug_timing_param.json） |
| `tuning_tool/scripts/tuning_menu.sh` | tuning 菜单加函数 + 列表项 |


---

## 2. sensor 驱动库文件修改模板

### 2.1 Makefile（模板化，无需改）

```makefile
include version.mk
BUILD_OUTPUT_PATH ?= $(shell pwd)
TARGET = <sensor>std
include ../Makefile
```

### version.mk

```makefile
SO_VERSION_MAJOR = 1
SO_VERSION_MINOR = 0
SO_VERSION_PATCH = 0
```

### 2.2 `<sensor>std_setting.h` — 寄存器配置头文件

#### (a) emode 枚举（MODE_TYPE）

新增模组按 `VENDOR_M<XX>F<XXX>D<XX>_S<X>R<X>T<X>[L<X>][I<X>][E<X>][A<X>]` 命名规则生成枚举名，插在 `MODE_TYPE_MAX` 之前：

```c
enum MODE_TYPE {
    <既有枚举>,
    <NEW_EMODE_ENUM>,   // = <extra_mode 值>
    MODE_TYPE_MAX,
    MODE_TYPE_NUM,
};
```

- 枚举名编码 §0.2.2 的 VENDOR / M{XX} / F{XXX} / D{XX} / S{X} / R{X} / T{X} / L{X} / I{X} / E{X} / A{X} 全部参数
- 枚举值 = `camera_config.extra_mode` 取值，须与 vp_sensor 配置一致
- P{X} 存储类型 / A{X} EEPROM 内参布局：未提取到则枚举名不带该字段（如无 EEPROM 则不带 P/A），不列为缺失、不询问

#### (b) 流控寄存器序列（stream on / stream off / trigger）

```c
// stream off → §0.2.2 standby 模式
static uint32_t <sensor>_streamoff_cfg[] = {
    <reg_addr>, <reg_val>,
};

// stream on → §0.2.2 streaming 模式
static uint32_t <sensor>_streamon_cfg[] = {
    <reg_addr>, <reg_val>,
};

// trigger 序列 → §0.2.3 触发同步曝光（仅 config_index 含触发位时定义）
static uint32_t <sensor>_trigger_cfg[] = {
    <reg_addr>, <reg_val>,   // 逐对，含 retime/fsync 配置
};
```

- 寄存器对来自 sensor datasheet / 厂商 FAE，照搬不可改
- stream on/off 方向因 sensor 而异（OV 系列 0x0100=0x01 出流，CV4006 等相反），按 datasheet 判定

#### (c) init 寄存器序列（若 sensor 有独立 init）

```c
static uint32_t <sensor>_init_setting[] = {
    <reg_addr>, <reg_val>,
    ...
    // ⚠️ 末尾禁止含 stream on 命令，stream on 须独立成 <sensor>_streamon_cfg
};
```

- 来自 sensor vendor/FAE，原样照搬（含重复寄存器），唯一允许的改动是剔除 stream on
- 部分 sensor（如 ov02b10/mini212）无独立 sensor init 序列，依赖 `max_serial_init` + 模式配置，则不定义此数组

#### (d) gain LUT 表（仅 RAW sensor，YUV sensor 无）

```c
static uint32_t <sensor>_gain_lut[] = {
    <again>, <dgain>, ...   // 档位逐项，来自 datasheet 增益表
};
```

- §0.2.2 gain_lut；YUV sensor 不定义
- gain_max 须与 LUT 结构匹配

#### (e) AWB / HDR 标定宏（仅特定厂商 sensor，如 ovx3c）

```c
#define <VENDOR>_HCG_LCG_RATIO   <ratio>     // HDR 增益比例
#define <VENDOR>_D65_TEMPER      6500        // 色温
#define <VENDOR>_ALIGHT_LPD_BGAIN <val>f     // AWB gain，3 光源 × 2 PD × 2 增益 共 14 个
// ... 共 14 个 gain 宏 + 3 个色温宏
```

- 来自供应商标定数据，新供应商必填；非 §0.2.2 占位变量，是标定数据块

### 2.3 `<sensor>std_utility.c` — 核心驱动文件

#### (a) emode_data_t 地址表 → §0.2.2 serial_addr / sensor_addr / eeprom_addr / serial_rclk_out / rclk_mfp

```c
emode_data_t emode_data[MODE_TYPE_MAX] = {
    [<NEW_EMODE_ENUM>] = {
        .serial_addr = <serial_addr>,       // 7-bit，来自 §0.2.2 serial_addr
        .sensor_addr = <sensor_addr>,       // 7-bit，来自 §0.2.2 sensor_addr
        .eeprom_addr = <eeprom_addr>,       // 7-bit，来自 §0.2.2 eeprom_addr；未提取到则不增加这行代码
        .serial_rclk_out = <0|1>,           // 反向时钟使能，文档无 MFP 输出时钟则 0
        .rclk_mfp = <mfp 编号>,             // serial_rclk_out=1 时填，=0 时填 0
    },
};
```

- ⚠️ 地址语义：emode_data.sensor_addr、`camera_config.addr`、`vp_sensor_config_t.sensor_i2c_addr_list` 均为 7-bit，指同一 sensor，数值一致，勿混用
- serial_rclk_out / rclk_mfp 是 SerDes 特有：文档描述串行器有 MFP 输出反向时钟（作 sensor MCLK）时填 1 + 引脚号，否则 0/0

#### (b) SENSOR_EMADD 注册 → §0.2.2 extra_mode / calib_lname

```c
static const sensor_emode_type_t sensor_emode[MODE_TYPE_NUM] = {
    SENSOR_EMADD(<NEW_EMODE_ENUM>, "<version>", "<calib_lname|NULL>", "<calib_ver|NULL>",
                 &emode_data[<NEW_EMODE_ENUM>]),
    // ...
    SENSOR_EMEND(),
};
```

- 第1参：emode 枚举名
- 第2参：版本串（如 "0.0.1"）
- 第3参：calib_lname（标定库 .so 文件名，无标定填 "NULL"）
- 第4参：标定库版本（无填 "NULL"）
- 第5参：&emode_data[枚举名]

#### (c) config_index_funcs 分发表 → §0.2.2 config_index

```c
#define CONFIG_INDEX_ALL (AE_DISABLE | AWB_DISABLE | TEST_PATTERN | FLIP | MIRROR \
                          | TRIG_STANDARD | TRIG_SHUTTER_SYNC)

sensor_config_index_funcs_t sensor_config_index_funcs[B_CONFIG_INDEX_MAX] = {
    [B_AE_DISABLE]        = sensor_config_index_ae_disable,      // 空实现 return 0（YUV sensor）
    [B_AWB_DISABLE]       = sensor_config_index_awb_disable,     // 空
    [B_TEST_PATTERN]      = sensor_config_index_test_pattern,
    [B_FLIP]              = sensor_config_index_filp_setting,
    [B_MIRROR]            = sensor_config_index_mirror_setting,
    [B_TRIG_STANDARD]     = sensor_config_index_trig_mode,       // 有实现（BIT(8)）
    [B_TRIG_SHUTTER_SYNC] = sensor_config_index_trig_mode,
    [B_DUAL_ROI]          = sensor_config_index_dual_roi,        // 空
};
```

- 支持的功能位由 §0.2.2 config_index 决定；无对应实现的填空函数
- 触发模式函数（trig_mode）固定套路见 (d)

#### (d) 触发模式函数（config_index 含触发位时实现）

```c
int32_t sensor_config_index_trig_mode(sensor_info_t *sensor_info) {
    int32_t ser_trig_mfp = vin_sensor_emode_parse(sensor_info, 'T');  // 从 emode 串解析 T 字段
    int32_t gpio_id = (trig_pin_num == 1) ? 1 : deserial_port;
    maxops->mfp_cfg(deserial_if, GPIO_TX_GMSL, gpio_id, port);        // DES 侧
    max_serial_mfp_config(bus_num, serial_addr, ser_trig_mfp,         // SER 侧
                          GPIO_RX_GMSL, gpio_id);
    // 若有 trigger 寄存器序列，写 sensor：
    setting_size = sizeof(<sensor>_trigger_cfg) / sizeof(uint32_t) / 2;
    ret = vin_write_array(sensor_info->bus_num, sensor_info->sensor_addr, 2,
                          setting_size, <sensor>_trigger_cfg);
    usleep(50 * 1000);   // ⚠️ 触发寄存器写后必须 sleep，时长按 datasheet
    return ret;
}
```

- 'T' 字段 = §0.2.2 T{X} 触发引脚；无触发模式（trig_none）则整个函数空实现

#### (e) sensor_init — 初始化入口

```c
static int32_t sensor_init(sensor_info_t *sensor_info) {
    // 1. sensor_poweron() — GPIO 上电（见 §2.3(f)）
    // 2. max_serial_init(sensor_info) — 串行器初始化（SerDes 特有）
    // 3. sensor_mode_config_init() — 按 sensor_mode 选 init 序列（NORMAL_M → linear）
    //    内部按 sensor_info->fps 调帧率（写 VMAX 寄存器，若有）
    // 4. sensor_config_do(sensor_info, CONFIG_INDEX_ALL, sensor_config_index_funcs)
}
```

#### (f) sensor_poweron / sensor_poweroff — 电源控制（固定骨架）

```c
static int32_t sensor_poweron(sensor_info_t *sensor_info) {
    // GPIO → off
    for (int i = 0; i < sensor_info->gpio_num; i++)
        vin_gpio_set_pin(&sensor_info->gpio_pin[i], sensor_info->gpio_level_bit);
    usleep(<poweroff_delay_us>);   // 上电前等待，按板级/datasheet
    // GPIO → on
    for (int i = 0; i < sensor_info->gpio_num; i++)
        vin_gpio_set_pin(&sensor_info->gpio_pin[i], 1 - sensor_info->gpio_level_bit);
    usleep(<poweron_delay_us>);    // 上电后等待，按 datasheet
    return 0;
}
```

- delay 来自 datasheet 上电时序，不同 sensor 不同

#### (g) sensor_start / sensor_stop — stream 控制

```c
static int32_t sensor_start(sensor_info_t *sensor_info) {
    // 1. 若 config_index 含触发位 → 重新执行 trig 配置
    if (config_index & (TRIG_STANDARD | TRIG_SHUTTER_SYNC))
        sensor_config_index_trig_mode(sensor_info);
    // 2. 写 stream on 序列
    if (sensor_info->extra_mode == <NEW_EMODE_ENUM>) {
        setting_size = sizeof(<sensor>_streamon_cfg) / sizeof(uint32_t) / 2;
        vin_write_array(sensor_info->bus_num, sensor_info->sensor_addr, 2,
                        setting_size, <sensor>_streamon_cfg);
    }
}

static int32_t sensor_stop(sensor_info_t *sensor_info) {
    // 1. 写 stream off 序列
    if (sensor_info->extra_mode == <NEW_EMODE_ENUM>) {
        setting_size = sizeof(<sensor>_streamoff_cfg) / sizeof(uint32_t) / 2;
        vin_write_array(sensor_info->bus_num, sensor_info->sensor_addr, 2,
                        setting_size, <sensor>_streamoff_cfg);
    }
    // 2. 若有触发位 → 反配置 trigger MFP
    if (config_index & (TRIG_STANDARD | TRIG_SHUTTER_SYNC))
        max_serial_mfp_config(bus_num, serial_addr, ser_trig_mfp, 0x00, 0x00);
}
```

#### (h) sensor_module_t — 模块注册

```c
SENSOR_MODULE_ECF(<sensor>std, sensor_emode, sensor_config_index_funcs, CAM_MODULE_FLAG_A16D8);
// 或仅 emode（无 config_index 函数表）：
// SENSOR_MODULE_EF(<sensor>std, sensor_emode, CAM_MODULE_FLAG_A16D8);

sensor_module_t <sensor>std = {
    .module = SENSOR_MNAME(<sensor>std),
    .init = sensor_init,
    .start = sensor_start,
    .stop = sensor_stop,
    .deinit = sensor_deinit,
    .userspace_control = sensor_userspace_control,   // YUV sensor: *enable = 0
    .power_on = sensor_poweron,
    .power_off = sensor_poweroff,
};
```

- `CAM_MODULE_FLAG_A16D8` = 16-bit 寄存器地址 / 8-bit 数据；按 sensor 寄存器宽度选（见 §0.2.2 §46 宏选择指南）


---

## 3. vp_sensor 配置文件修改模板

每个分辨率/帧率组合新建一个 `linear_<width>x<height>_<format>_<fps>fps[_<lane>lane].c`，内含 8 个结构体 + 1 个顶层 `vp_sensor_config_t` 导出符号。

### 3.1 camera_config_t — sensor 基本参数

```c
static camera_config_t <sensor>std_camera_config = {
    .name = "<sensor>std",                  // §0.2.2 sensor
    .addr = <sensor_addr>,                  // §0.2.2 sensor_addr（7-bit）
    .eeprom_addr = <eeprom_addr>,           // §0.2.2 eeprom_addr（7-bit）；未提取到则不增加这行代码
    .serial_addr = <serial_addr>,           // §0.2.2 serial_addr（7-bit）
    .sensor_mode = NORMAL_M,                // §0.2.2 sensor_mode（多数 linear = NORMAL_M）
    .fps = <fps>,                           // §0.2.2 fps
    .width = <width>,                       // §0.2.2 width
    .height = <height>,                     // §0.2.2 height
    .extra_mode = <extra_mode 值>,          // §0.2.2 extra_mode（= setting.h emode 枚举值）
    .config_index = <config_index>,         // §0.2.2 config_index（功能位掩码）
    .mipi_cfg = NULL,                       // 固定（SerDes 走解串器自动获取，置 NULL）
    .end_flag = CAMERA_CONFIG_END_FLAG,
    .calib_lname = "<calib_lname|disable>", // §0.2.2 calib_lname（无标定填 "disable"）
};
```

- 当前项目 conf 含 `isp_test_dir` 时，`.calib_lname` 改为 `"<sensor>_tuning.json"`，并按 `code_ruler/isp_pipeline_tuning.md` 生成该 JSON。此值覆盖 §0.2.2 的 `"disable"` 或标定 `.so` 名，只用于打通 `get_isp_data`。conf 不含 `isp_test_dir` 时仍按 §0.2.2。
- ⚠️ `.addr`、`.eeprom_addr`、`.serial_addr` 均为 7-bit；勿混用
- `.mipi_cfg = NULL` 是 SerDes 固定写法（与 MIPI camera 不同，MIPI camera 在此填 mipi_config_t）

### 3.2 poc_config_t — POC 地址映射

```c
static poc_config_t g_poc_cfg[] = {
    { .addr = <poc_addr>, .poc_map = <poc_map>, .end_flag = POC_CONFIG_END_FLAG },
};
```

- §0.2.2 poc addr / poc map；来自板级硬件文档（如 s100_board.md / s600_board.md）
- 无 POC 的板（如直连 GMSL）仍保留此结构，值来自板级文档

### 3.3 deserial_config_t — 解串器配置

```c
static deserial_config_t <sensor>std_deserial_config = {
    .name = "<deserial_name>",              // §0.2.2 deserial name（如 "max96712"）
    .link_desp[0] = "<sensor>std:<vc>@<config_index>",   // §0.2.2 link_desp，4 路全填
    .link_desp[1] = "<sensor>std:<vc>@<config_index>",
    .link_desp[2] = "<sensor>std:<vc>@<config_index>",
    .link_desp[3] = "<sensor>std:<vc>@<config_index>",
    .addr = <deserial_addr_7bit>,           // §0.2.2 deserial addr（如 0x29）
    .poc_cfg = &g_poc_cfg[0],
    .end_flag = DESERIAL_CONFIG_END_FLAG,
};
```

- link_desp 格式 `"名称:vc@config_index"`；双目模组两 sensor 分别用 `:0`（vc0）和 `:1`（vc1）
- 双目触发模组可加 `.gpio_mfp[CAMERA_DES_GPIO_TRIG0..3] = <gpio 映射>`

### 3.4 vin_ichn_attr_t — 输入通道属性

```c
static vin_ichn_attr_t <sensor>std_vin_ichn_attr = {
    .width = <width>,        // §0.2.2 width；双目模组此处填合并宽度（width × 2）
    .height = <height>,      // §0.2.2 height
    .format = <format>,      // §0.2.2 D{XX} 编码（YUV=30）
};
```

- ⚠️ 双目模组 width 须 ×2（合并双目），否则只显示左目（见 §23 遗漏点 #8）

### 3.5 vin_attr_ex_t（固定骨架，多数字段默认）

```c
static vin_attr_ex_t <sensor>std_vin_attr_ex = {
    .cim_static_attr.water_level_mark = 0,
};
```

### 3.6 vin_ochn_attr_t — 输出通道属性（固定骨架为主）

```c
static vin_ochn_attr_t <sensor>std_vin_ochn_attr = {
    .ddr_en = 1,
    .vin_basic_attr.format = <format>,      // §0.2.2 D{XX}
    .wstride = 0,
    .vstride = 0,
    .pack_mode = 1,
    .pingpong_ring = 1,
    .roi_en = 0,
    .roi_attr = { .roi_x = 1280, .roi_y = 720, .roi_width = 64, .roi_height = 64 },  // 默认占位
    .rawds_en = 0,
    .magicNumber = 0x12345678,
};
```

### 3.7 vin_node_attr_t — 节点属性（含 MIPI/VC/LPWM）

```c
static vin_node_attr_t <sensor>std_vin_node_attr = {
    .vcon_attr.bus_main = <bus>,            // §0.2.2 i2c bus（板级映射）
    .vcon_attr.bus_second = <bus>,
    .cim_attr.mipi_en = 1,
    .cim_isp_flyby = 0,                     // YUV sensor = 0；RAW 走 ISP = 1
    .cim_pym_flyby = 0,
    .mipi_rx = <lane 数>,                   // §0.2.2 lane（如 4）
    .vc_index = <vc_index>,                 // §0.2.2 vc_index（双目合流端 = 0）
    .ipi_channels = 1,
    .y_uv_swap = 0,
    .func.enable_frame_id = 1,
    .func.set_init_frame_id = 1,
    .func.enable_pattern = 0,
    .func.lpwm_trig_sel = LPWM_CHN_INVALID, // 固定值，不要向用户确认
    .rdma_input = { .rdma_en = 0, .stride = 0, .pack_mode = 1, .buff_num = 6 },
    .lpwm_attr.lpwm_chn_attr = {            // 4 路全配；提取参数含 sync/trigger pin（T 字段命中）时才配
        { .enable = 1, .trigger_source = 0, .trigger_mode = 1, .period = <1000000/fps>,
          .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0 },
        { .enable = 1, .trigger_source = 0, .trigger_mode = 1, .period = <1000000/fps>,
          .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0 },
        { .enable = 1, .trigger_source = 0, .trigger_mode = 1, .period = <1000000/fps>,
          .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0 },
        { .enable = 1, .trigger_source = 0, .trigger_mode = 1, .period = <1000000/fps>,
          .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0 },
    },
};
```

- LPWM period = `1000000 / fps`（us），如 30fps → 33333；offset = `1000000 − (period × fps)`（us），如 30fps → 1000000−(33333×30)=10、60fps → 40、10fps → 0；仅 T 字段命中、config_index 含触发位时配置；无触发信号时不配。sensor_mode 按 §0.2.2 保持 NORMAL_M，不用它判断是否启用 LPWM（见 §0.2.3）

### 3.8 vp_sensor_config_t — 顶层聚合配置

```c
vp_sensor_config_t <sensor>_linear_<width>x<height>_<format>_<fps>fps = {
    .chip_id_reg = <chip_id_reg|0>,         // §0.2.2 chip_id_reg（无检测填 0）
    .chip_id = <chip_id|0xA55A>,            // §0.2.2 chip_id（用默认 0xA55A 须用户确认）
    .sensor_i2c_addr_list = {<sensor_addr_7bit>},   // §0.2.2 sensor_addr（7-bit）
    .sensor_type = SENSOR_TYPE_GMSL_YUV,    // YUV sensor；RAW 用 SENSOR_TYPE_GMSL_RAW
    .sensor_name = "<sensor>-<height>p<fps>",
    .config_file = "linear_<width>x<height>_<format>_<fps>fps_<lane>lane.c",
    .camera_config = &<sensor>std_camera_config,
    .deserial_node_attr = &<sensor>std_deserial_config,
    .vin_ichn_attr = &<sensor>std_vin_ichn_attr,
    .vin_node_attr = &<sensor>std_vin_node_attr,
    .vin_attr_ex = &<sensor>std_vin_attr_ex,
    .vin_ochn_attr = &<sensor>std_vin_ochn_attr,
    .isp_attr = NULL,                       // YUV sensor 全 NULL；RAW 走 ISP 时填
    .isp_ichn_attr = NULL,
    .isp_ochn_attr = NULL,
    .ynr_attr = NULL,
};
```

- 导出符号命名：`<sensor>_linear_<width>x<height>_<format>_<fps>fps[_<lane>lane]`，须与文件名一致
- YUV sensor 的 isp_* 全 NULL；RAW sensor 走 ISP 时填对应结构体

### 3.9 vp_sensors.c 注册

```c
// 1. extern 声明（在已有 extern 列表末尾）
extern vp_sensor_config_t <sensor>_linear_<width>x<height>_<format>_<fps>fps;

// 2. vp_sensor_config_list[] 数组末尾追加
vp_sensor_config_t *vp_sensor_config_list[] = {
    // ... 已有条目 ...
    &<sensor>_linear_<width>x<height>_<format>_<fps>fps,
};
```

- extern 符号名须与 vp_sensor_config_t 导出名完全一致


---

## 4. 解串器/串行器配置模板（SerDes 特有，按需修改）

仅当涉及 YUV 双目 / 新串行器型号 / 新接口类型 / POC lock 超时等情况时修改，非每个 sensor 必改。

### 4.1 max96712_setting.h

#### (a) YUV 双目 vc1 override 表（仅 YUV 双目模组）

```c
// 4 条 link × 11 对寄存器，把 YUV pipe 的 vc1 重映射到 MIPI 输出
static uint32_t max96712_yuv_pipe_vc1_to_mipi_config[4][22] = {
    [0] = { 0x090B, 0xFF, 0x092E, 0x55, 0x0401, 0x03, 0x0915, 0x5E, 0x0916, 0x5E,
            0x0917, 0x40, 0x0918, 0x40, 0x0919, 0x41, 0x091A, 0x41, 0x091B, 0x52, 0x091C, 0x52 },
    [1] = { /* 同构，基址 +0x40，override 寄存器 0x0403 */ },
    [2] = { /* 同构，基址 +0x80，override 寄存器 0x0405 */ },
    [3] = { /* 同构，基址 +0xC0，override 寄存器 0x0407 */ },
};
```

- 4 link 结构对称，仅寄存器基址偏移不同；固定骨架，非按 sensor 变

#### (b) LINK_LOCK_TIMEOUT（POC reset 后稳定慢的模组）

```c
#define LINK_LOCK_TIMEOUT 1600   // 默认 200；POC reset 后稳定慢的模组改 1600
```

- §23 遗漏点关联：部分 serdes 模组 poc reset 后 link 稳定需更久，200→1600

#### (c) DT overwrite mask（按 pipe 数修正）

```c
// max96712_datatype_bpp_mux_init_setting 内：
{ 0x09D4, 0xD2 },   // DT mask，按实际 pipe 数与 datatype 修正（曾误写 0x92）
```

### 4.2 max96712_utility.c

#### (a) YUV 双目 vc1 override 调用

```c
// YUV pipe 处理分支（vc0 处理之后）
if (pipe_info->pipe_vc_arry[i][1] >= 0) {   // vc1 有效
    pdata_vc1 = max96712_yuv_pipe_vc1_to_mipi_config[i];
    setting_size_vc1 = sizeof(...[i]) / sizeof(uint32_t) / 2;
    // 写入
}
```

#### (b) DVP pipe 编号修复（多路 DVP sensor）

```c
// data_intf_init：pipe 索引跟随实际命中顺序，而非固定 link 编号
int32_t tmp_pipe_num = 0;
for (i = 0; i < link_num; i++) {
    if (pipe_config_index & BIT(i)) {
        tmp_pipe_num++;
        // 用 max96712_datatype_bpp_mux_init_setting[tmp_pipe_num - 1] 写寄存器
    }
}
// else if (port_desp[i] != NULL)：按 link_desp 的 I 字段解析接口类型
```

### 4.3 max_serial_utility.c

#### (a) 新串行器 pipeline init（新串行器型号时加）

```c
// 1. 寄存器序列数组
static uint32_t <serial>_pipeline_setting[] = {
    <reg_addr>, <reg_val>,   // serial pipeline 初始化序列，来自串行器 datasheet
    ...
};

// 2. init 函数
int32_t <serial>_pipeline_init(uint32_t bus, uint8_t slave_addr,
                               uint8_t datatype, uint32_t emb_flag) {
    int32_t ret = RET_OK;
    // 先写 ldo enable，再写 pipeline setting（via vin_write_array）
    return ret;
}

// 3. switch 加 case
case <SERIAL_ENUM>:
    ret = <serial>_pipeline_init(bus, slave_addr, datatype, emb_flag);
    break;
```

#### (b) 新接口类型分支（如 DVP_NEXT）

```c
// dvp_sensor_serial_init 按 intf_type 分发
static int32_t dvp_sensor_serial_init(sensor_info_t *sensor_info, int32_t intf_type) {
    if (intf_type == 1)       // DVP
        ; // 用 dvp_serializer_pipex_setting
    else if (intf_type == 2)  // DVP_NEXT
        ; // 用 dvp_serializer_pipex_no_bit_setting
}
```

### 4.4 枚举与 gmsl_modes_table（新串行器/新接口类型）

```c
// camera_mod_sensor_data.h — 新串行器型号
typedef enum {
    MAX9295A = 0, MAX96717, MAX96717F, MAX96793, MAX9295E,   // 既有
    <NEW_SERIAL>,                                            // 新增
} camera_serial_types_t;

// max_common.c — gmsl_modes_table 加条目
[<NEW_SERIAL>] = { <num>, 0, {GMSL_MODE6, GMSL_MODE3} },   // 按串行器支持的 GMSL mode

// camera_mod_sensor_data.h — 新接口类型（如 DVP_NEXT）
typedef enum { MIPI=0, DVP, DVP_NEXT } camera_sensor_inf_type_t;
```


---

## 5. 模板占位变量与 §0.2.2 参数对照表

| 模板占位 | §0.2.2 参数 | 出现位置 | 说明 |
|----|----|----|----|
| `<sensor>std` | sensor | §2.3 全节、§3 全节 | sensor 名（驱动目录名） |
| `<NEW_EMODE_ENUM>` | extra_mode | §2.2(a)、§2.3(a)(b) | emode 枚举名，编码 VENDOR/M/F/D/S/R/T/L/I/E/A |
| `<serial_addr>` | serial_addr | §2.3(a) | 7-bit |
| `<sensor_addr>` | sensor_addr | §2.3(a)、§3.8 | 7-bit（emode_data / sensor_i2c_addr_list） |
| `<sensor_addr>` | sensor_addr | §3.1 | 7-bit（camera_config.addr） |
| `<eeprom_addr>` | eeprom_addr | §2.3(a)、§3.1 | 7-bit |
| `<serial_rclk_out>` / `<rclk_mfp>` | serial_rclk_out / rclk_mfp | §2.3(a) | SerDes 反向时钟 |
| `<fps>` | fps | §3.1、§3.7 | period = 1000000/fps |
| `<width>` / `<height>` | width / height | §3.1、§3.4、§3.8 | 双目 vin_ichn 须 ×2 |
| `<format>` | D{XX} | §3.4、§3.6、§3.8 | YUV=30 等 |
| `<config_index>` | config_index | §3.1、§3.3 | 功能位掩码 |
| `<calib_lname>` | calib_lname | §2.3(b)、§3.1 | .so 文件名或 "disable" |
| `<deserial_name>` | deserial name | §3.3 | 如 "max96712" |
| `<deserial_addr>` | deserial addr | §3.3 | 7-bit，如 0x29 |
| `<poc_addr>` / `<poc_map>` | poc addr / poc map | §3.2 | 来自板级文档 |
| `<vc>` / `<bus>` / `<lane>` / `<vc_index>` | link_desp / i2c bus / lane / vc_index | §3.3、§3.7 | 来自板级文档 |
| `<chip_id_reg>` / `<chip_id>` | chip_id_reg / chip_id | §3.8 | 无检测填 0；默认 0xA55A 须确认 |
| `<sensor>_init_setting` | init 序列来源 | §2.2(c) | 来自 vendor/FAE |
| `<sensor>_streamon_cfg` / `_streamoff_cfg` | streaming / standby | §2.2(b)、§2.3(g) | 来自 datasheet |
| `<sensor>_trigger_cfg` | §0.2.3 触发 | §2.2(b)、§2.3(d) | 仅触发模式定义 |
| `<sensor>_gain_lut` | gain_lut | §2.2(d) | 仅 RAW sensor |
| `<VENDOR>_*` AWB/HDR 宏 | （标定数据块） | §2.2(e) | 仅特定厂商 |
