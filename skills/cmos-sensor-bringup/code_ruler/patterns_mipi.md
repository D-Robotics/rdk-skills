# Direct MIPI Camera 代码编写规律

---

## 0.6 待提取参数（参数提取总纲）

提取参数时，逐参数对照本节填写。每参数三要素：含义 / 提取规律（如何从文档/init setting 取值）/ 是否需用户确认。出确认清单前，按 SKILL.md『入清单前的过滤判据』逐点回查本节——能由规律闭环的参数直接填值，不进清单、不询问；只有"确认=是"或规律未定且文档缺失的才进清单。

### 0.6.1 类型校验（提取参数前首条执行）
用户在入口已指定 camera 类型为 Direct MIPI。提取参数时校验文档内容是否相符：文档须**不**含 Serializer 芯片描述（无 MAX9295/MAX96717 等）。若文档含 Serializer 芯片描述，则停下询问用户（类型与文档不符），不得自动改类型。

### 0.6.2 init setting 与 mipi_config 的职责分离（强制）
1. init setting 为厂商给定，**完全照搬，唯一允许的改动是剔除 stream on 命令**（见 §2.3），禁止为对齐 VTS/HTS 而增、删、改 init 中任何寄存器；
2. 本节提取/计算的 VTS、HTS，**用途仅是填入 mipi_config_t 的 framelenth/linelenth 字段**，与 init 寄存器序列解耦，不反改 init；
3. 当用户给定 VTS（或给定 HTS）时，直接以此给定值填入对应字段，并据此用公式计算另一项；用户给定的值不用于反改 init，init 仍照搬；
4. 方向单向：init 不可改 → mipi_config 的 framelenth/linelenth 按提取/计算/用户给定值独立填入。

### 0.6.3 待提取参数逐项

#### mipiclk总带宽
- 含义：MIPI 时钟，即所有使能 lane 合并速率（总带宽=单 lane 速率 × lane 数），单位 Mbps
- 提取规律：①init setting 注释显式给出（如 `// mipiclk = 2880MHZ`）→以注释值为准，不因寄存器推导值不符而改动；②注释未给→从寄存器推断：读 SYS_MODE 寄存器查单 lane data rate，mipiclk=data_rate×lane 数（lane 数从 LANEMODE 寄存器读取）；③均不可得→标"未找到"询问用户，禁止猜测。**向用户询问得到的 mipiclk 值即为总带宽（已含 lane 数，即所有使能 lane 合并速率），填入 mipi_config_t.mipiclk 字段时直接取该值，不再乘 lane 数**。注释值与寄存器推导值不一致时不询问，按优先级取注释值
- 确认判据：注释或寄存器任一可得 mipiclk→按优先级取值不确认（注释与寄存器推导值不一致也不确认，按优先级取注释值）；注释与寄存器均不可得→需向用户补充 mipiclk（草拟，待审定）

#### VTS（framelenth）
- 含义：帧长度，填入 mipi_config_t.framelenth
- 提取规律：从 init setting 寄存器配置值获取。framelenth 取 VTS 值。init setting 没有→标"未找到"询问用户
- 确认判据：init setting 寄存器配置值含 VTS→按寄存器取值不确认；init setting 无 VTS→需向用户补充 VTS（草拟，待审定）

#### format_bitwidth
- 含义：输出位深（RAW8/RAW10/RAW12 等）
- 提取规律：从 init setting / 文档获取。init setting 没有→标"未找到"询问用户
- 确认判据：init setting/文档含位深信息→按取值不确认；init setting 与文档均无位深→需向用户补充 format_bitwidth（草拟，待审定）

#### lane（MIPI Lane 数）
- 含义：MIPI CSI-2 通道数
- 提取规律：文档直读；或根据sensor手册中的LANECOUNT/LANEMODE 寄存器看init setting 配置的是多少lane
- 确认判据：没有获取到则加入清单找用户确认。init 未配 lane 寄存器但文档表有默认值+位定义时,init 沿用默认值=已获取到,按默认值取值不询问

#### datatype
- 含义：MIPI 数据类型
- 提取规律：按 format_bitwidth 对应：RAW8/RAW10/RAW12 等。从文档/init setting 获取
- 确认判据：不确认

#### mclk
- 含义：Sensor 输入主频（XCLK），单位 MHz
- 提取规律：按以下顺序取值，前序步骤取到值即闭环：
  ① 文档中找到 MCLK/XCLK/INCK 的直接赋值（形如 "= 24MHz"，或某频率被标 default/recommended）→ 用该值；
  ② 文档列出多个可选输入频率时，查 init 序列的时钟选择寄存器（SYS_MODE/INCKSEL 等）配置值，对照文档频率选择表得出实际频率 → 用该值；
  ③ 以上两步均无 → 标"未找到"进确认清单询问用户。
  注：文档"列出多个可选频率"不等于"已标注实际使用的值"——仅列出可选项而无选择依据时仍属未闭环，按③处理。
- 确认判据：①或②取到值→按取值不确认；①②均无→向用户确认

#### width / height
- 含义：分辨率
- 提取规律：文档直读
- 确认判据：不确认

#### fps
- 含义：帧率
- 提取规律：文档直读
- 确认判据：不确认

#### addr（I2C 7bit）
- 含义：sensor I2C 地址
- 提取规律：文档 8bit 地址右移1位。**文档以位表（逐位二进制，如 `0 0 1 1 0 1 0 R/W`）给出地址时**，必须逐位读出 bit7..bit1 组成 7bit 数值（bit0 是 R/W 方向位，不计入地址），禁止跳过逐位步骤、禁止凭"扫一眼"凑数值；若文档给的是数值形式的 8bit 地址，直接右移1位转 7bit。两种形式取值后均在参数表标注来源（位表行/数值行）。文档给出多个 I2C 地址时（如硬件引脚电平不同对应不同地址），各地址均按上述规则转 7bit 后全部填入 `sensor_i2c_addr_list`（已提取出地址，属"提取出 7bit 地址"情形，不询问用户用哪个，参照 sc231ai `{0x30,0x32}`）
- 确认判据：从文档中提取出 7bit 地址→按取值不确认；从文档中未提取出 7bit 地址→标注"未找到"并提供给用户确认

#### mipi_rx
- 含义：MIPI RX host 号（填入 vin_node_attr.cim_attr.mipi_rx，非 PHY 类型）
- 提取规律：来自板级文档（按 mipi_index 对应的 host）
- 确认判据：不确认

#### phy_type
- 含义：MIPI PHY 类型（0=D-PHY, 1=C-PHY），填入 mipi_config.rx_attr.phy
- 提取规律：从当前 sensor 文档提取。文档直写"D-PHY/C-PHY"字样 → 按字样取值；文档未直写 → 看 MIPI 接口示意图：有独立时钟通道（Clock+/- 差分对）+ 差分数据对（Data+/-）为 D-PHY，三通道 trio（A/B/C 三相、无独立 clock lane）为 C-PHY
- 确认判据：文档中提取到 PHY 类型 → 按取值不确认；文档中提取不到 → 用默认值 0（D-PHY），不确认

#### vc_index / ipi_channel
- 含义：VC 索引 / IPI 通道
- 提取规律：单 sensor 默认 vc_index=0、ipi_channel=1；双目特殊处理见 §3
- 确认判据：不确认

#### input_mode / cim_isp_flyby / ddr_en
- 含义：VIN-ISP 在线/离线模式三件套
- 提取规律：非 DOL2 默认离线（input_mode=DDR_MODE, cim_isp_flyby=0, ddr_en=1）；DOL2 强制在线（PASSTHROUGH_MODE, 1, 0）。详见 §5
- 确认判据：不确认

#### standby 模式
- 含义：standby 模式（部分 sensor 读 chip_id 前需先唤醒出 standby）
- 提取规律：必须从当前 sensor datasheet 确认，不参考其他 sensor。需确认两项：(a) standby 控制寄存器地址与位字段；(b) 该寄存器各数值含义（哪个值=进 standby、哪个值=退出 standby/Operating）。**只要提取到 standby 寄存器（地址+数值含义），就设置 read_chip_id_cb**；未提取到 standby 寄存器→不设 read_chip_id_cb，走框架默认读取。
- 确认判据：提取到 standby 寄存器→设 read_chip_id_cb，不询问用户；未提取到 standby 寄存器→不设 read_chip_id_cb，不询问用户。此判据由规律自动闭环，不询问用户

#### chip_id_reg / chip_id
- 含义：芯片ID寄存器/期望值
- 提取规律：必须从当前 sensor datasheet 确认，不参考其他 sensor。文档无→直接要求用户提供 chip_id 寄存器地址与期望值
- 确认判据：datasheet 明确给出芯片ID寄存器与期望值→按 datasheet 取值不确认；文档/datasheet 无芯片ID信息→进确认清单要求用户提供 chip_id 寄存器地址与期望值

#### settle
- 含义：避开脉冲信号的 settle 时间
- 提取规律：从文档中找，文档中找不到则向用户确认使用默认值 0 还是手动输入一个值
- 确认判据：文档中未提取到则需要向用户确认使用默认值 0 还是手动输入一个值

#### bayer start / pattern
- 含义：Bayer 填充两参，传入 `sensor_data_bayer_fill(<format_bitwidth>, <start>, <pattern>)` 与 `sensor_data_bits_fill(<format_bitwidth>)`。bit 不再单独提取/确认，直接引用本节 format_bitwidth 参数值
- 提取规律：bit 复用 format_bitwidth（由输出格式闭环，不作为 bayer 的待提取/待确认项，不单独询问）；仅 start、pattern 两参需从 sensor 文档获取，关键搜索像素阵列/Pixel Array等（第一个像素颜色格式）。仅 RAW(RAW8/RAW10/RAW12) sensor 适用；YUV422 / 内置 ISP / 已去马赛克输出 → 不调用 bayer 填充，三参均不配，不列为缺失、不询问
- 确认判据：bit 由 format_bitwidth 闭环不确认；RAW sensor 且文档未给出 start/pattern → 标"未找到"询问用户（仅问 start 与 pattern，不问 bit）；YUV / 内置 ISP → 不询问

#### HTS（linelenth）
- 含义：行长度，填入 mipi_config_t.linelenth
- 提取规律：优先从 init setting 寄存器配置值获取；init setting 无 HTS 时按公式计算：HTS = mipiclk × 10⁶ / (VTS × FPS × format_bitwidth)，计算结果向下取整。**公式中 mipiclk 取 mipi_config_t.mipiclk 字段值（总带宽=单 lane 速率 × lane 数，已含 lane，不再额外乘 lane 数）**。linelenth 取最终 HTS 值
- 确认判据：不确认

#### linear_gain_reg（NORMAL/linear 模式的增益寄存器）
- 含义：NORMAL/linear 模式的增益寄存器地址列表，填入 §2.4(a) 的 `<SENSOR>_REG_GAIN*` 宏与 §2.4(d) 代码模板主路径写入地址
- 提取规律：从 datasheet"增益寄存器控制"表的"线性/HDR 长曝光"行提取寄存器地址列表（命名按 datasheet 实际，可能是 ANA GAIN/ANA FINE GAIN/DIG GAIN/DIG FINE GAIN 或 HIGH/LOW 等，不写死术语；有几个提几个）
- 确认判据：datasheet 含增益寄存器控制表→提取，不询问；无→标"未找到"询问用户

#### hdr_gain_reg（HDR 模式的增益寄存器）
- 含义：HDR 模式的增益寄存器地址列表，填入 §2.4(d) 代码模板 HDR 段 `<SENSOR>_REG_S_*`。有此组→对应 config 的 sensor_mode 填 DOLx_M、§2.4(d) HDR 段启用；无→该 config 的 sensor_mode 填 NORMAL_M、HDR 段删除
- 提取规律：每个 setting 对应一个 vp_sensor config。先查各 setting 是否含 HDR/DOLx 信号——setting 文件名/序列名含 `dol1`/`dol2`/`dol3`/`hdr`（如 `xxx_dol2_init_setting`）且 init 序列出现 HDR 模式的增益寄存器地址。HDR 模式的增益寄存器地址靠 datasheet 增益寄存器控制表对照识别（init 里出现的地址，在 datasheet 表里查是否属"HDR 短曝光"行）。
- 确认判据：**此项必问，不论各 setting 有无 HDR/DOLx 信号，都要让用户确认后再继续，禁止查无信号就跳过**。三项由 AI 先查清再呈现给用户确认，不得反问用户去查：(1) 共有几个 setting、各自曝光模式（DOL1/DOL2/DOL3/linear，括号注明依据如"文件名含 `linear`→线性"）；(2) HDR 模式的增益寄存器——AI 对照 datasheet 增益表查 init 序列：查到则报"HDR 模式的增益寄存器为 0xXXXX，请确认"，未查到则报"未找到，需补充 HDR/DOL setting 及 HDR 模式的增益寄存器"。用户确认后据实填：dolx setting 对应的 config 的 sensor_mode 填 DOLx_M、§2.4(d) HDR 段启用且 S_ 寄存器填提取值；linear setting 对应的 config 的 sensor_mode 填 NORMAL_M、无 HDR 段。support_sensor_mode 列表汇总见 support_sensor_mode 条目。本字段确认结果是 sensor_mode/support_sensor_mode 的填写前置，未完成本字段确认不得填后续两字段。

#### sensor_mode 曝光模式
- 含义：config 运行模式（单值），填入 §3.2 camera_config 的 `.sensor_mode`
- 提取规律：每个 config 的 sensor_mode 按该 config 对应 setting 的曝光模式填（linear→NORMAL_M、DOL1→DOL1_M、DOL2→DOL2_M、DOL3→DOL3_M、DOL4→DOL4_M、PWL→PWL_M、MONO→MONO_M）。曝光模式仅限 linear/DOL1/DOL2/DOL3/DOL4/PWL/MONO（由 hdr_gain_reg 确认）。slave 的 sensor_mode 填 SLAVE_M(=6)（框架枚举含 SLAVE_M），§3.5 lpwm_attr.enable 由「slave触发模式」条目单独决定。曝光模式由 hdr_gain_reg 条目逐 setting 确认得到
- 确认判据：**填写前须先完成 hdr_gain_reg 的用户确认（三项结果），未完成不得填本字段**。setting 曝光模式由 hdr_gain_reg 找用户确认；本字段据确认结果填，不单独询问

#### support_sensor_mode 支持的曝光模式
- 含义：支持的曝光模式列表
- 提取规律：每个 config 的 support_sensor_mode 列表都按所有 setting 曝光模式追加填（各 config 共用同一列表）。如 sensor 有线性 + DOL2 两组 setting，则每个 config 的 support_sensor_mode 都填 {NORMAL_M, DOL2_M}。列表内容 = 所有 setting 曝光模式（不含 slave；slave 不计入本列表）。忘填会崩
- 确认判据：**填写前须先完成 hdr_gain_reg 的用户确认（三项结果），未完成不得填本字段**。setting 曝光模式由 hdr_gain_reg 条目（逐 setting 找用户确认）得到；本字段据汇总结果填，不单独询问

#### slave触发模式
- 含义：config 是否 slave 触发模式。用于 §3.5 lpwm_attr.enable 置 1
- 提取规律：①setting 名含 `slave`→slave；②查 setting 寄存器序列结合 datasheet 确认是否含 slave/trigger 同步配置→slave；③均无→默认 master
- 确认判据：规律自动闭环，不询问用户

#### gain_lut（again/dgain 档位表）
- 含义：增益档位查找表，index x = 0~255（x 上限 255，即最多 256 档；实际条目数取挑选结果，可 ≤256），每项编码该 x 对应的 again/dgain 寄存器写入值。寄存器地址已归 linear_gain_reg/hdr_gain_reg，本条目只提档位数值与形态
- 提取规律（**不逐档照抄 datasheet 增益表，按 ISP 索引 x 逐点从手册 LUT 表中挑选**）：ISP SoC 上报的 gain 单位是倍率，换算成 HBN ISP 索引 `x = 32 * log2(gain)`。x=0 对应 1x gain（`32*log2(1)=0`），x 递增至该 sensor 最大增益（x 上限 255）。对每个 x，目标倍率按公式 `gain(x) = round(2^(x/32), 3)` 算出，再**从当前 sensor datasheet 的增益 LUT 表中挑出最接近该目标倍率的那一档的寄存器值**填入（手册档不够密时，相邻 x 可挑到同一档、填相同寄存器值；不凭公式凭空换算寄存器值，只挑手册已有的档）。挑到多少档，gain_lut 条目数就是多少（≤256）。max_gain 取自 datasheet 标注的最大增益倍率（如 8x/16x/32x）。形态由 linear_gain_reg 的寄存器数判定（对应 §2.4(d) 排布表 3 种形态）：1 个→单字段；2 个（主+副）→2 字段(主+副)；4 个（again 主+副 + dgain 主+副）→again/dgain 分表。分表形态下 again/dgain 两表各按自己手册 LUT 独立挑选。32bit 字段排布（单表/分表、bit 位置）不在 datasheet 中，由 §2.4(d) pattern 规定。提取后参数表展示摘要（"gain_lut：按公式 gain(x)=round(2^(x/32),3) 从 datasheet LUT 逐 x 挑档，共 N 档(≤256)，形态=..."），不展开每一档数值；完整数值在第2步填入 setting.h 时逐项呈现（遵循 §2.3 gain_lut 单列呈现强制）。禁止从其他 sensor 驱动复制寄存器值
- 确认判据：datasheet 含增益 LUT 表（倍率↔寄存器值）→按公式逐 x 算目标倍率、从该表挑选最接近档直接填值，**结构形态由 linear_gain_reg 寄存器数机械判定、挑档结果按公式从 LUT 表挑选，均固定不询问用户**；datasheet 无增益 LUT 表→标"未找到"询问用户

#### 曝光寄存器及位段（shutter）
- 含义：aexp_line_control 写曝光行值所用的寄存器地址与位段定义，填入 §2.4(a) 的 `<SENSOR>_REG_SHUTTER*` 宏与 §2.4(e) 的位拆分
- 提取规律：从当前 sensor datasheet 的"曝光/快门寄存器"表提取——曝光值跨哪几个寄存器、每个寄存器对应曝光值的哪一段 bit。逐项记录：寄存器地址列表（按高位→低位顺序）、各寄存器承载的 bit 段（如 [19:16]/[15:8]/[3:0]）、最低位寄存器低 4 位是否为 fraction 位（若 datasheet 标注为 fraction 位，记录为"低 4 位 fraction"，位拆分时用 0xF0 清零不写）。参数表展示完整提取结果（寄存器地址+位段+fraction 标注），不展开写入代码。**所有 sensor 一律整行曝光**——即便 datasheet 标注「半行曝光/1/16 行」能力也不启用，sline 直接取整行（见 §2.4(e)）。禁止从其他 sensor 驱动复制地址与位段
- 确认判据：datasheet 含曝光寄存器表→提取并展示，不询问；datasheet 无明确位段定义→标"未找到"询问用户

---

## 1. 必须修改的文件列表及顺序

### 阶段一：sensor 驱动库（libcam 层）

| 序号 | 文件 | 操作 | 说明 |
|------|------|------|------|
| 1 | `libcam/src/sensor/<sensor>/Makefile` | 新建 | 模板化，TARGET 自动取目录名 |
| 2 | `libcam/src/sensor/<sensor>/version.mk` | 新建 | 版本号，默认 1.0.0 |
| 3 | `libcam/src/sensor/<sensor>/inc/<sensor>_setting.h` | 新建 | stream on/off、gain LUT、初始化序列 |
| 4 | `libcam/src/sensor/<sensor>/<sensor>_utility.c` | 新建 | 核心驱动逻辑 |

### 阶段二：vp_sensor 配置（platform_samples 层）

| 序号 | 文件 | 操作 | 说明 |
|------|------|------|------|
| 5 | `vp_sensors/<sensor>/linear_<width>x<height>_raw<format_bitwidth>_<fps>fps_<lane>lane.c` | 新建 | 每个分辨率/帧率组合一个配置文件 |
| 6 | `vp_sensors/vp_sensors.c` | 修改 | extern 声明 + vp_sensor_config_list 注册 |


---

## 2. sensor 驱动库文件修改模板

### 2.1 Makefile（模板化，无需修改）

```makefile
-include ./version.mk
# ... 标准模板 ...
TARGET = $(notdir $(shell pwd))   # 自动取目录名
include ../Makefile
```

### 2.2 version.mk（仅需改版本号）

```makefile
SO_VERSION_MAJOR = 1
SO_VERSION_MINOR = 0
SO_VERSION_PATCH = 0
```

新 sensor 初始版本均为 1.0.0。

### 2.3 <sensor>_setting.h — 寄存器配置头文件

包含四大部分：

#### (a) 流控寄存器

```c
#define <SENSOR>_REG_CTRL_MODE <reg_addr>
#define <SENSOR>_MODE_SW_STANDBY <reg_val>
#define <SENSOR>_MODE_STREAMING  <reg_val>

static uint32_t <sensor>_stream_on_setting[] = { <reg_addr>, <reg_val> };
static uint32_t <sensor>_stream_off_setting[] = { <reg_addr>, <reg_val> };
```

#### (b) gain LUT 表

不同厂商 sensor 的 gain_lut 编码方式不同（见 §2.4 增益控制差异）。单表形态只建 `<sensor>_gain_lut[]`（仅 again 或 主+副混排）；again/dgain 分表形态建两张独立表：

```c
static uint32_t <sensor>_gain_lut[] = {
    0x00,  // 1.0x
    ...
};
/* again/dgain 分表形态：dgain 单独建表，与 gain_lut 各自独立取值，档数不必相等 */
static uint32_t <sensor>_dgain_lut[] = {
    0x00,  // 1.0x
    ...
};
```

#### (c) 初始化寄存器序列

命名规则：`<sensor>_init_<width>x<height>_<lane>lane_linear_setting`

```c
static uint32_t <sensor>_init_1920x1080_2lane_linear_setting[] = {
    // MCLK=24MHz MIPI 2lane 1920*1080 30FPS 10bit
    0x3000, 0x01,
    0x3002, 0x01,
    0x3024, 0xCA,
    ...
};
```

**⚠️ init 寄存器序列格式与不可更改规则（通用，所有厂商 sensor）：**

处理流程分两步，严格按顺序执行：

**第一步：原样照搬**
1. **格式：强制每行一对寄存器**（地址, 值），每个寄存器地址与其写入值单独占一行，禁止将多对寄存器压缩到同一行。**该格式规则同样适用于 gain LUT 表**：LUT 表强制每行一个值（每个增益档位单独占一行），禁止每行塞多个值。
2. **内容：寄存器序列绝对不能更改**。从文档/厂商 init setting 搬运到驱动，必须原样照搬，禁止增、删、改、合并任何一项，**包括重复出现的寄存器**。即便同一寄存器在序列中出现多次（如先设初值后覆盖），也必须保留原顺序与原值，因为寄存器写入顺序与时序是 sensor 正常工作的必要条件。
   - **gain_lut 单列呈现强制**：gain_lut 表强制每行一个值（每个增益档位单独占一行），禁止每行塞多个值。此条与第一步格式规则同等强制，**生成 diff 呈现给用户确认时也必须单列展示，不得为压缩篇幅写成每行多值**，违反即为呈现违规。

**第二步：照搬完成后，检查并剔除 stream on**
- 对照搬完成的 init 序列检查其中是否包含 stream on 命令（按 experience 文件「如何判断 init 序列末尾 stream 命令是 on 还是 off」方法判定 on/off：on=出流方向，off=待机方向）。
- 有 stream on → 从 init 序列中去除，独立成 `stream_on_setting[]`，由 `sensor_start()` 调用。
- stream off → 保留在 init 序列中，不动。
- 第二步的剔除是照搬之后的定点处理，不违反第一步“不可更改”；第一步照搬时不得预先跳过任何寄存器。

即：**先完整照搬，再在照搬结果上检查剔除 stream on**，二者先后执行，不冲突。

**⚠️ SC 系列 sensor 注意**：初始化寄存器列表中**不应包含 stream on 命令**（如 `0x0100,0x01`），应使用独立的 `stream_on_setting[]`。包含 stream on 会导致数据溢出。


#### (d) 多分辨率/多帧率时需多个 init 序列

- 同分辨率不同帧率：仅 HTS/VTS 寄存器值不同，可用独立序列或在 sensor_init 中覆盖
- 不同分辨率且不同帧率：init 序列差异巨大，**必须使用独立完整序列**


### 2.4 <sensor>_utility.c — 核心驱动文件

**文件包含**（固定，A16D8 sensor 通用）：
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include "hb_cam_utility.h"
#include "hb_camera_data_config.h"
#include "inc/<sensor>_setting.h"
```

#### (a) 寄存器地址宏定义

```c
#define REG_WIDTH  2   // reg16 data8 → 使用 CAM_MODULE_FLAG_A16D8
#define <SENSOR>_REG_GAIN              <reg_addr>
// 曝光寄存器：地址与位段取自 §0.6「曝光寄存器及位段」从 datasheet 提取，禁止套用其它 sensor
// 寄存器个数与位段随 sensor 不同而异（典型 2~3 个，如高位/中位/低位），按 datasheet 实际补齐
#define <SENSOR>_REG_SHUTTER_<bit段标签>   <reg_addr>   // 承载曝光值 [?:?]，按 datasheet
#define <SENSOR>_FRAME_LENGTH          <VTS>
```

#### (b) sensor_init — 初始化入口

```c
static int sensor_init(sensor_info_t *sensor_info) {
    ret = sensor_poweron(sensor_info);
    switch(sensor_info->sensor_mode) {
        case NORMAL_M:
            if (sensor_info->fps == 30) {
                if(sensor_info->config_index == 0) {  // 2lane
                    setting_size = sizeof(<sensor>_init_WxH_2lane_linear_setting) / sizeof(uint32_t) / 2;
                    ret = vin_write_array(sensor_info->bus_num, sensor_info->sensor_addr,
                                          REG_WIDTH, setting_size,
                                          <sensor>_init_WxH_2lane_linear_setting);
                } else {  // 4lane
                    // ...
                }
                ret = <sensor>_linear_data_init(sensor_info);
            }
            break;
        default:
            break;
    }
}
```

**多分辨率/多模式 sensor 的分支逻辑**：外层按 `width + height` 选分辨率档，内层按 `fps` 区分 setting，每个 fps 分支内 `switch(sensor_mode)` 区分 config。`width/height/fps` 为 §0.6 白名单参数，`sensor_mode` 由 hdr_gain_reg 确认。**禁止用 `sensor_info->resolution`**（框架赋值为 height，语义模糊）**和 `sensor_info->config_index`**（数组下标，随注册顺序变动）做判据。slave 由「slave触发模式」条目确认，走 `switch` 的 `default` 分支（SLAVE_M 作 default），避免与 NORMAL_M/DOLx_M 等并列 case 冲突。占位由当前 sensor 的 §0.6 提取值替换：
```c
if (sensor_info->width == <width> && sensor_info->height == <height>) {  /* <width>/<height> = §0.6 提取值 */
    if (sensor_info->fps == <fps_1>) {  /* <fps_1> = §0.6 提取值 */
        switch (sensor_info->sensor_mode) {  /* <sensor_mode> = §0.6 由 hdr_gain_reg 确认得到 */
            case NORMAL_M:
                /* 写 <sensor>_init_<width>x<height>_<lane>lane_<fps_1>fps_<mode1>_setting */
                break;
            /* 同 fps 下其它曝光模式(NORMAL_M/DOLx_M/PWL_M/MONO_M 等)按需追加 case */
            default:
                /* SLAVE_M 作 default: 写 <sensor>_init_<width>x<height>_<lane>lane_<fps_1>fps_slave_setting */
                break;
        }
    } else if (sensor_info->fps == <fps_2>) {  /* <fps_2> = §0.6 提取值 */
        switch (sensor_info->sensor_mode) {
            case NORMAL_M:
                /* 写 <sensor>_init_<width>x<height>_<lane>lane_<fps_2>fps_<mode2>_setting */
                break;
            default:
                /* SLAVE_M 作 default: 写 <sensor>_init_<width>x<height>_<lane>lane_<fps_2>fps_slave_setting */
                break;
        }
    }
} else if (sensor_info->width == <width_b> && sensor_info->height == <height_b>) {  /* 另一分辨率档 */
    switch (sensor_info->sensor_mode) {
        case NORMAL_M:
            /* 写 <sensor>_init_<width_b>x<height_b>_<lane_b>lane_<fps_b>fps_linear_setting */
            break;
        default:
            break;
    }
}
```


#### (c) sensor_poweron / sensor_poweroff — 电源控制

通过 GPIO 控制，遍历 `sensor_info->gpio_pin[]` 数组，按 `gpio_num` 循环，每个 GPIO 用 `vin_power_ctrl()` 翻转电平。字段与 API 固定，不询问用户：
- **GPIO 编号**：遍历 `sensor_info->gpio_pin[gpio]`（不是只取 `gpio_pin[0]`），循环上限 `sensor_info->gpio_num`，前置 `if (gpio_num > 0)`
- **空值跳过**：`if (sensor_info->gpio_pin[gpio] != -1)` 跳过未配置的 GPIO
- **电平字段**：`sensor_info->gpio_level[gpio]`（按 gpio 索引的数组，不是 `gpio_level_bit` 单值）；off 值 = `gpio_level[gpio]`，on 值 = `!gpio_level[gpio]`（逻辑非取反）
- **API**：`vin_power_ctrl(gpio_pin[gpio], level)`，返回 <0 失败
- **延时**：每次 flip 后 `usleep(100 * 1000)`（100ms）

poweron flip 序列（所有 sensor 通用）：off → on，1 次 flip，各延时 100ms
```c
ret = vin_power_ctrl(sensor_info->gpio_pin[gpio], sensor_info->gpio_level[gpio]);
usleep(100 * 1000);
ret |= vin_power_ctrl(sensor_info->gpio_pin[gpio], !sensor_info->gpio_level[gpio]);
usleep(100 * 1000);
```

完整模板：
```c
static int sensor_poweron(sensor_info_t *sensor_info) {
    int gpio, ret = RET_OK;
    if (sensor_info->gpio_num > 0) {
        for (gpio = 0; gpio < sensor_info->gpio_num; gpio++) {
            if (sensor_info->gpio_pin[gpio] != -1) {
                /* off → on, 1 次 flip */
                ret = vin_power_ctrl(sensor_info->gpio_pin[gpio], sensor_info->gpio_level[gpio]);
                usleep(100 * 1000);
                ret |= vin_power_ctrl(sensor_info->gpio_pin[gpio], !sensor_info->gpio_level[gpio]);
                usleep(100 * 1000);
                if (ret < 0) { vin_err("vin_power_ctrl fail\n"); return -HB_CAM_SENSOR_POWERON_FAIL; }
            }
        }
    }
    return ret;
}

static int sensor_poweroff(sensor_info_t *sensor_info) {
    int gpio, ret = RET_OK;
    if (sensor_info->gpio_num > 0) {
        for (gpio = 0; gpio < sensor_info->gpio_num; gpio++) {
            if (sensor_info->gpio_pin[gpio] != -1) {
                ret = vin_power_ctrl(sensor_info->gpio_pin[gpio], sensor_info->gpio_level[gpio]);
                if (ret < 0) { vin_err("vin_power_ctrl fail\n"); return -HB_CAM_SENSOR_POWEROFF_FAIL; }
            }
        }
    }
    return ret;
}
```
poweroff 只写 off 值（`gpio_level[gpio]`，不取反），不 flip。


#### (d) 增益控制 — 按寄存器结构归纳（不区分厂商）

> 单寄存器读写 API（写 again/dgain/dgain_fine 等单寄存器时使用，签名固定，不询问用户）：
> ```c
> // 写单寄存器（reg16 地址 + 8bit 值，即 A16D8 模式）。返回 0 成功，<0 失败。
> vin_i2c_write8(bus, reg_width, sensor_addr, reg_addr, value)
> // 读单寄存器。返回值即读到的 8bit 数据（失败返回 <0）。
> vin_i2c_read8(bus, reg_width, sensor_addr, reg_addr)
> ```
>
> 寄存器数组批量写 API（写 init 序列 / stream on-off 序列时使用，签名固定，不询问用户）：
> ```c
> // 批量写寄存器数组（每对 = reg16 地址 + 8bit 值）。返回 0 成功，<0 失败。
> vin_write_array(bus, sensor_addr, reg_width, setting_size, setting_array)
> ```
> **参数顺序固定为 `(bus, sensor_addr, reg_width, setting_size, setting_array)`——setting_size 在前、setting_array(指针)在后**。底层定义为 `camera_reg_i2c_write_array`（见 `camera_reg.h`），sensor utility.c 默认可见。
> 参数顺序固定为 `(bus, reg_width, sensor_addr, reg_addr, value)`，其中 `reg_width` 对 A16D8 模式传 `16`。底层定义为 `camera_reg_i2c_write8/read8`（见 `camera_legacy.h`），无需包含额外头文件，sensor utility.c 默认可见。
> SC 系列"写 again + dgain + dgain_fine 三个寄存器"调用例：
> ```c
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_AGAIN,      again_val);
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_DGAIN,      dgain_val);
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_DGAIN_FINE, dgain_fine_val);
> ```

> gain_lut 按 ISP 索引 x 从手册 LUT 逐点挑档（x=0~255，条目数 ≤256），每档寄存器写入值按 §0.6「gain_lut」由 `gain(x)=round(2^(x/32),3)` 算目标倍率、从 datasheet 增益 LUT 表挑最接近档填入，禁止从其他 sensor 驱动复制寄存器值。

> gain_lut 每项 32bit 的字段排布与解包（pattern 按结构归纳，不区分厂商；**结构形态由 linear_gain_reg 寄存器数机械判定（1→单字段、2→主+副、4→again·dgain 分表）、挑档结果按公式从 datasheet LUT 表挑选，均固定不询问用户**；`vin_i2c_write8` 签名见 §2.4d 开头）：
>
> **gain_lut 32bit 字段排布形态（按结构归纳，不区分厂商；datasheet 的增益寄存器数/位宽决定选哪种；结构形态由 linear_gain_reg 寄存器数机械判定，固定不询问用户）**：
> | 形态 | 32bit 字段排布 | 解包式 | 写入寄存器数 | digital_gain_max |
> |---|---|---|---|---|
> | 单字段（单表） | `[7:0]again` | `&0xFF` | 1 | 0 |
> | 2 字段主+副（单表） | `[15:8]主 \| [7:0]副` | `>>8&0xFF`(主)、`&0xFF`(副) | 2 | 0 |
> | again/dgain 分表(主+副) | gain_lut `[15:8]主/[7:0]副` + 独立 dgain_lut `[15:8]主/[7:0]副` | 各表 `>>8&0xFF`(主)、`&0xFF`(副) | 4 | 三目式 |
>
> 命名（HIGH/LOW 或 GAIN/Fine GAIN 等）按 datasheet/驱动实际，模板不写死；同一结构不同厂商命名不同但解包相同。单表形态（单字段/2字段主+副）无 dgain_lut 表 → digital_gain_max=0；分表形态（4 字段）有独立 dgain_lut 表 → digital_gain_max 按三目式算。
>
> ```c
> static int sensor_aexp_gain_control(hal_control_info_t *info, uint32_t mode, uint32_t *again, uint32_t *dgain, uint32_t gain_num)
> {
> /* 32bit 排布按上表形态选定（由 linear_gain_reg 寄存器数机械判定，不询问用户）；不用的字段该字节填 0。
>    digital_gain_max：单表形态填 0 */
> /* analog_gain_max = (gain_lut 条目数 > 256) ? 255 : (gain_lut 条目数 - 1)。
>    index 越界保护：again[0] 即 ISP 索引 x，超过 gain_max 钳到 gain_max */
> if (again[0] > analog_gain_max)
>     again_index = analog_gain_max;
> else
>     again_index = again[0];
>
> /* —— 单表形态（仅 again 或 主+副）：所有字段从同一 gain_lut 取 —— */
> /* 字段数：仅 again = 1 个、主+副 = 2 个。单表形态 digital_gain_max=0。
>    分表形态（4 字段）走下一段 */
> <字段1>_reg_value = (<sensor>_gain_lut[again_index] >> <起始位1>) & 0xFF;   /* bit[?:?] */
> <字段2>_reg_value = (<sensor>_gain_lut[again_index] >> <起始位2>) & 0xFF;   /* bit[?:?]（仅 again 形态无此行） */
> /* 写入对应寄存器（地址取自 datasheet，用 vin_i2c_write8） */
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_<字段1>, <字段1>_reg_value);
> ...
>
> /* —— 分表形态（4 字段）：dgain 从独立 dgain_lut 取，两表各自独立取值 —— */
> /* digital_gain_max = (dgain_lut 条目数 > 256) ? 255 : (dgain_lut 条目数 - 1) */
> if (dgain[0] > digital_gain_max)
>     dgain_index = digital_gain_max;
> else
>     dgain_index = dgain[0];
> <again主>_reg_value = (<sensor>_gain_lut[again_index]  >> <主起始位>) & 0xFF;
> <again副>_reg_value = (<sensor>_gain_lut[again_index]  >> <副起始位>) & 0xFF;
> <dgain主>_reg_value = (<sensor>_dgain_lut[dgain_index] >> <主起始位>) & 0xFF;
> <dgain副>_reg_value = (<sensor>_dgain_lut[dgain_index] >> <副起始位>) & 0xFF;
> /* 写入四个寄存器（again 主/副 + dgain 主/副，地址取自 datasheet）。
>    命名按 datasheet/驱动实际：HIGH/LOW 或 GAIN/Fine GAIN 均可，模板不写死命名 */
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_<again主>, <again主>_reg_value);
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_<again副>, <again副>_reg_value);
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_<dgain主>, <dgain主>_reg_value);
> vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_<dgain副>, <dgain副>_reg_value);
> /* 单表与分表二选一，按排布表选定的形态保留对应段，删另一段 */
>
> /* HDR 双增益（仅 DOL2_M 模式）：短帧用 again[1]/dgain[1]，写 S_ 系列寄存器。
>    NORMAL_M 模式无此段。sensor 不支持 DOL2 时整段删除 */
> } else if (mode == DOL2_M) {
>     /* again[1]/dgain[1] 同样做 index 越界保护（s_again_index/s_dgain_index） */
>     s_<again主>_reg_value = (<sensor>_gain_lut[s_again_index]  >> <主起始位>) & 0xFF;
>     s_<again副>_reg_value = (<sensor>_gain_lut[s_again_index]  >> <副起始位>) & 0xFF;
>     s_<dgain主>_reg_value = (<sensor>_dgain_lut[s_dgain_index] >> <主起始位>) & 0xFF;  /* 分表形态 */
>     s_<dgain副>_reg_value = (<sensor>_dgain_lut[s_dgain_index] >> <副起始位>) & 0xFF;  /* 分表形态 */
>     /* 单表形态 s_dgain 从 gain_lut 取；分表从 dgain_lut 取 */
>     vin_i2c_write8(bus, 16, sensor_addr, <SENSOR>_REG_S_<again主>, s_<again主>_reg_value);
>     ...
> }
> ```
> NORMAL/linear 模式的增益寄存器地址取自 §0.6 linear_gain_reg，HDR 模式的增益寄存器地址取自 §0.6 hdr_gain_reg，档位数值与形态取自 §0.6 gain_lut——均自动判定，不询问用户。命名（HIGH/LOW 或 GAIN/Fine GAIN）按 datasheet/驱动实际，模板不写死。hdr_gain_reg 有提取值→HDR 段保留、S_ 寄存器填提取值、support_sensor_mode 含 DOL2_M；标"无"→HDR 段整段删除、不追加 DOL2_M。

**关键参数**（gain_lut/dgain_lut 按 ISP 索引 x 从手册 LUT 挑档，x 上限 255）：
- `analog_gain_max` / `digital_gain_max` 规则相同：有对应的 LUT 表 → (该表条目数 > 256) ? 255 : (该表条目数 - 1)；没有该表 → 0
- gain_lut 每档值按 §0.6 由公式 `gain(x)=round(2^(x/32),3)` 算目标倍率、从 datasheet 增益 LUT 表中挑选最接近档的寄存器值填入，不逐档照抄 datasheet 表

*(gain_lut 数值来源见 §0.6.4，须取自当前 sensor 手册)*

#### (e) 曝光行控制 — 统一整行曝光（不分厂商）

> **强制：所有 sensor 一律整行曝光**——`sline = line`，不半行、不写 fraction（低 4 位清零不写）。不按 OV/SC/IMX 厂商分支，不再有 `sline = 2*line` 半行换算、不再有 `(line<<4)` fraction 左移。曝光寄存器地址与位段仍取自 §0.6「曝光寄存器及位段」从当前 sensor datasheet 提取；datasheet 若标注「半行/fraction」能力，此处也不启用，仍按整行写。

| 项目 | 取值 |
|------|------|
| sline 换算 | `sline = line[0]`（直接整行，所有厂商统一） |
| 上限 | `sline_max = VTS - 5`（VTS 取 `<SENSOR>_FRAME_LENGTH` 宏值；与 §2.4(f) `exposure_time_max = VTS - 5` 同口径） |
| 下限 | `sline_min = 1` |
| 位拆分 | 按寄存器位段移位取值；若最低位寄存器低 4 位为 fraction 位，掩码取 0xF0（清零不写 fraction），保证只写整行部分 |

> 曝光寄存器地址与位段**取自 §0.6「曝光寄存器及位段」从当前 sensor datasheet 提取**，本节只给结构与算法，不写死任何地址/位段。

> aexp_line_control 结构模板（手写展开，对齐现有驱动写法；地址/位段占位取自 §0.6；`vin_i2c_write8` 签名见 §2.4d）：
> ```c
> static int sensor_aexp_line_control(hal_control_info_t *info, uint32_t mode, uint32_t *line, uint32_t line_num)
> {
>     uint32_t sline = 0;
>     uint8_t temp_hi, temp_mid, temp_lo;
>     if (mode == NORMAL_M) {
>         /* 整行曝光：sline 直接等于行值，不半行、不写 fraction */
>         sline = line[0];
>         /* 上下限截断：max = VTS - 5，min = 1 */
>         if (sline > <SENSOR>_FRAME_LENGTH - 5) sline = <SENSOR>_FRAME_LENGTH - 5;
>         if (sline < 1) sline = 1;
>
>         /* 位拆分写入：寄存器地址 <SENSOR>_REG_SHUTTER_* 与位段均取自 §0.6，按 datasheet 位段移位取值。
>            寄存器个数随 sensor（2~3 个）：3 寄存器 sensor 保留 hi/mid/lo 三行；2 寄存器 sensor 删 mid 行。
>            最低位寄存器若含 fraction 低 4 位，掩码用 0xF0 清零不写 fraction，只写整行部分。
>            不得套用其它 sensor 的地址或位段 */
>         temp_hi  = (sline >> <高位段起始位>) & <高位段掩码>;     /* 承载曝光值高位段 */
>         temp_mid = (sline >> <中位段起始位>) & <中位段掩码>;    /* 承载曝光值中位段，2 寄存器 sensor 删此行 */
>         temp_lo  = (sline >> <低位段起始位>) & <低位段掩码>;    /* 承载曝光值低位段；fraction 低 4 位用 0xF0 清零不写 */
>         vin_i2c_write8(info->bus_num, 16, info->sensor_addr, <SENSOR>_REG_SHUTTER_HI,  temp_hi);
>         vin_i2c_write8(info->bus_num, 16, info->sensor_addr, <SENSOR>_REG_SHUTTER_MID, temp_mid);  /* 2 寄存器 sensor 删此行 */
>         vin_i2c_write8(info->bus_num, 16, info->sensor_addr, <SENSOR>_REG_SHUTTER_LO,  temp_lo);
>     }
>     return 0;
> }
> ```
> 寄存器地址、位段起始位、掩码——全部以 §0.6 从 datasheet 提取的值为准填入占位符；sline 换算与上下限已固定为整行口径（`line[0]` / `VTS-5` / `1`），不再按厂商分支。2 寄存器 sensor 删 mid 行（temp_mid 赋值 + 对应 write8）；3 寄存器 sensor 保留三行。

> *(现有驱动均为手写展开，无表驱动/循环先例)*

**核心公式**：
- `lines_per_second = fps * vts`（vts 取 `<SENSOR>_FRAME_LENGTH` 宏值，即 init 序列写入 VTS 寄存器的同一个值；现有驱动不做运行时读 VTS 寄存器，直接用此常量）
- `exposure_time_max = vts - margin`（margin 一般为 5）
- `exposure_time_min = 1`


#### (f) linear_data_init — turning data 初始化

```c
static int <sensor>_linear_data_init(sensor_info_t *sensor_info) {
    turning_data.bus_num = sensor_info->bus_num;
    turning_data.bus_type = sensor_info->bus_type;
    turning_data.port = sensor_info->port;
    turning_data.reg_width = REG_WIDTH;
    turning_data.mode = sensor_info->sensor_mode;
    /* SLAVE_M 是触发模式非曝光模式, turning_data.mode 期望曝光模式, slave 时填 NORMAL_M */
    if (sensor_info->sensor_mode == SLAVE_M)
        turning_data.mode = NORMAL_M;
    turning_data.sensor_addr = sensor_info->sensor_addr;
    strncpy(turning_data.sensor_name, sensor_info->sensor_name, sizeof(turning_data.sensor_name));

    // sensor data
    turning_data.sensor_data.active_width = <width>;
    turning_data.sensor_data.active_height = <height>;
    // lines_per_second 用 <SENSOR>_FRAME_LENGTH 宏（= init 写入 VTS 寄存器的值）× fps，不运行时读寄存器（对齐现有驱动做法）
    turning_data.sensor_data.lines_per_second = <SENSOR>_FRAME_LENGTH * <fps>;
    turning_data.sensor_data.exposure_time_max = <SENSOR>_FRAME_LENGTH - 5;
    turning_data.sensor_data.exposure_time_min = 1;
    turning_data.sensor_data.analog_gain_max = (<gain_lut_count> > 256) ? 255 : (<gain_lut_count> - 1);
    turning_data.sensor_data.digital_gain_max = (<dgain_lut_count> == 0) ? 0 : ((<dgain_lut_count> > 256) ? 255 : (<dgain_lut_count> - 1));  // 无 dgain_lut 时 count=0，上限为 0
    turning_data.sensor_data.analog_gain_init = 32;
    turning_data.sensor_data.digital_gain_init = 0;
    turning_data.sensor_data.exposure_time_init = ((<SENSOR>_FRAME_LENGTH - 5) + 1) / 2;  // 取上下限中点，AE 从中点起步

    // bayer
    sensor_data_bayer_fill(&turning_data.sensor_data, <format_bitwidth>, <start>, <pattern>);
    sensor_data_bits_fill(&turning_data.sensor_data, <format_bitwidth>);

    // stream_ctrl
    turning_data.stream_ctrl.data_length = 1;
    memcpy(stream_on, <sensor>_stream_on_setting, ...);
    memcpy(stream_off, <sensor>_stream_off_setting, ...);

    // gain lut
    turning_data.normal.again_lut = malloc(<gain_lut_count> * sizeof(uint32_t));
    memcpy(turning_data.normal.again_lut, <sensor>_gain_lut, ...);

    ret = ioctl(sensor_info->sen_devfd, SENSOR_TURNING_PARAM, &turning_data);
}
```

#### (g) sensor_module_t — 驱动注册

```c
#ifdef CAMERA_FRAMEWORK_HBN
SENSOR_MODULE_F(<sensor>, CAM_MODULE_FLAG_A16D8);
sensor_module_t <sensor> = {
    .module = SENSOR_MNAME(<sensor>),
#else
sensor_module_t <sensor> = {
    .module = "<sensor>",
#endif
    .init = sensor_init,
    .start = sensor_start,
    .stop = sensor_stop,
    .deinit = sensor_deinit,
    .power_on = sensor_poweron,
    .power_off = sensor_poweroff,
    .aexp_gain_control = sensor_aexp_gain_control,
    .aexp_line_control = sensor_aexp_line_control,
    .userspace_control = sensor_userspace_control,
};
```

`CAM_MODULE_FLAG` 根据寄存器位宽选择：
- `A16D8`：16 位地址 8 位数据（绝大多数 sensor）
- `A8D8`：8 位地址 8 位数据

**userspace_control 实现**（声明 `*enable` 的控制位掩码，框架据此使能 AE 增益/曝光控制）：
```c
static int sensor_userspace_control(uint32_t port, uint32_t *enable)
{
    *enable = HAL_GAIN_CONTROL | HAL_LINE_CONTROL;
    return 0;
}
```
`HAL_GAIN_CONTROL`（增益）、`HAL_LINE_CONTROL`（曝光行）为框架标准控制位宏；有 AF 功能的 sensor 追加 `HAL_AF_CONTROL`。

**有 AF 功能的 sensor** 需额外添加：
```c
    .af_control = sensor_af_control,
```
并在 `userspace_control` 中加入 `HAL_AF_CONTROL`。


---

## 3. vp_sensor 配置文件修改模板

每个分辨率/帧率组合创建一个 `.c` 文件，包含 8 个配置结构体 + 1 个顶层注册结构体。

**配置文件数量规则（强制，不询问用户）**：用户在 init setting / 参数中给出几组分辨率×帧率×lane 组合，就生成几组 vp_sensor 配置文件（每组一个 `.c`），并在 vp_sensors.c 中注册对应数量的 extern 声明与数组项。用户给几组就生成几组，不得多生成、不得少生成、不得自行增减组合，不针对此规定询问用户或找用户确认。

### 3.1 mipi_config_t — MIPI 链路配置（MIPI Camera 核心）

```c
static mipi_config_t <sensor>_mipi_config = {
    .rx_enable = 1,
    .rx_attr = {
        .phy           = <phy_type>,       // MIPI PHY 类型: 0=D-PHY, 1=C-PHY(见 §0.6.3 phy_type)
        .lane           = <lane>,       // 从文档获取
        .datatype       = RAW10,              // 从文档获取：RAW8/RAW10/RAW12
        .fps            = <fps>,
        .mclk           = <mclk_mhz>,      // 从文档获取
        .mipiclk        = <mipiclk>,     // 从文档计算
        .width          = <width>,
        .height         = <height>,
        .linelenth      = <HTS>,              // 必须与 sensor 寄存器 HTS 值一致
        .framelenth     = <VTS>,              // 必须与 sensor 寄器 VTS 值一致
        .settle         = <settle>,           // 避开脉冲信号的 settle 时间，提取阶段确认的值
        .channel_num    = 1,
        .channel_sel    = {0},
    }
};
```

**rx_ex_mask / rx_attr_ex**：本模板不再配置。是否需要 rx_ex_mask/stop_check_instart 由规律自动判定，不询问用户。

### 3.2 camera_config_t — Sensor 配置

```c
static camera_config_t <sensor>_camera_config = {
    .name             = "<sensor>",
    .addr             = <addr>,
    .sensor_mode      = <本 config 对应 setting 的曝光模式>,  // linear→NORMAL_M, DOL1→DOL1_M, DOL2→DOL2_M（见 §0.6 hdr_gain_reg）
    .format           = <datatype>,  // 数据格式，与 mipi_config.datatype 一致（RAW8/RAW10/RAW12）；get_vin_data 依此字段决定 dump 格式
    .mipi_cfg         = &<sensor>_mipi_config,
    .gpio_enable_bit  = 0x01,
    .gpio_level_bit   = 0x00,
    .calib_lname      = "<calib_lname>",
};
```

**calib_lname**：当前项目 conf 含 `isp_test_dir` 时填 `"<sensor>_tuning.json"`，并按 `code_ruler/isp_pipeline_tuning.md` 生成该文件。这是打通 `get_isp_data` 的结构文件名。当前项目 conf 不含 `isp_test_dir` 时填 `"disable"`。

### 3.3 vin_attr_ex_t — MCLK 扩展配置

```c
static vin_attr_ex_t <sensor>_vin_attr_ex = {
    .vin_attr_ex_mask = 0x80,   /* VIN_STATIC_MCLK_ATTR: 使框架探测时使能 MCLK(见 §3.3 说明) */
    .mclk_ex_attr = {
        .mclk_freq = <mclk_hz>,    // 24MHz = 24000000
    },
};
```

### 3.4 vin_ichn_attr_t — VIN 输入通道属性

```c
static vin_ichn_attr_t <sensor>_vin_ichn_attr = {
    .width = <width>,
    .height = <height>,
};
```

### 3.5 vin_node_attr_t — VIN 节点属性

```c
static vin_node_attr_t <sensor>_vin_node_attr = {
    .cim_attr = {
        .mipi_rx      = <mipi_rx>,   // 从板端约束获取
        .vc_index     = 0,
        .ipi_channel  = 1,
        .cim_isp_flyby = 0,                 // 非 DOL2: offline=0
        .func = {
            .enable_frame_id    = 1,
            .set_init_frame_id  = 0,
            .hdr_mode           = NOT_HDR,
            .time_stamp_en      = 0,
        },
    },
    .lpwm_attr = {
        .enable = <lpwm_enable>,    // SLAVE_M: 1, 非 SLAVE_M(NORMAL_M/DOLx_M 等): 0
        .lpwm_chn_attr = {         // 4 通道, period/offset 按 fps 算, 其余取默认值(与 patterns_serdes §0.2.3 一致)
            { .trigger_source = 0, .trigger_mode = 0, .period = <1000000/fps>,
              .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0, },
            { .trigger_source = 0, .trigger_mode = 0, .period = <1000000/fps>,
              .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0, },
            { .trigger_source = 0, .trigger_mode = 0, .period = <1000000/fps>,
              .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0, },
            { .trigger_source = 0, .trigger_mode = 0, .period = <1000000/fps>,
              .offset = <1000000-(period*fps)>, .duty_time = 100, .threshold = 0, .adjust_step = 0, },
        },
    },
};
```

**lpwm_attr 配置规则（强制）**：
- `.enable`：按本 config 的 `camera_config.sensor_mode` 判定——`sensor_mode == SLAVE_M` 时 `enable = 1`（slave 模式需 LPWM trigger 同步出流），其余模式（NORMAL_M / DOLx_M 等）`enable = 0`（NORMAL_M 误启用会误触发同步曝光，见 §6 遗漏点）。
- `period = 1000000 / fps`（us），按本 config 的 fps 取整计算（如 30fps → 33333，60fps → 16666）。
- `offset = 1000000 − (period × fps)`（us），由 period 与 fps 推算（如 30fps：1000000−(33333×30)=10；60fps：1000000−(16666×60)=40；10fps：1000000−(100000×10)=0）。
- period/offset 公式与 patterns_serdes §0.2.3 口径一致。



### 3.6 vin_ochn_attr_t — VIN 输出通道属性

```c
static vin_ochn_attr_t <sensor>_vin_ochn_attr = {
    .ddr_en = 1,                            // 非 DOL2: offline 模式必须为 1
    .ochn_attr_type = VIN_BASIC_ATTR,
    .vin_basic_attr = {
        .format = RAW10,                    // 与 mipi_config datatype 一致
        .wstride = <width> * 2,      // RAW10/RAW12/RAW16: width * 2; RAW8: width * 1
    },
};
```

### 3.7 isp_attr_t — ISP 属性

```c
static isp_attr_t <sensor>_isp_attr = {
    .input_mode  = DDR_MODE,                // 非 DOL2: DDR_MODE(offline)
    .sensor_mode = ISP_NORMAL_M,
    .crop = { .x=0, .y=0, .h=<height>, .w=<width> },
};
```

### 3.8 isp_ichn_attr_t / isp_ochn_attr_t — ISP 通道属性

```c
static isp_ichn_attr_t <sensor>_isp_ichn_attr = {
    .width = <width>,
    .height = <height>,
    .fmt = FRM_FMT_RAW,
    .bit_width = <format_bitwidth>,
};

static isp_ochn_attr_t <sensor>_isp_ochn_attr = {
    .ddr_en = 1,
    .fmt = FRM_FMT_NV12,
    .bit_width = 8,
};
```

### 3.9 vp_sensor_config_t — 顶层注册结构体

```c
vp_sensor_config_t <sensor>_linear_<width>x<height>_raw<format_bitwidth>_<fps>fps_<lane>lane = {
    .chip_id_reg           = <chip_id_reg>,
    .chip_id               = <chip_id>,
    .read_chip_id_cb       = <sensor>_read_chip_id,  // 只要提取到 standby 寄存器(地址+数值含义)就设(见 §0.6.3 standby 模式);未提取到 standby 寄存器则不设,走框架默认读取。此字段是否设置由规律自动判定,不询问用户
    .sensor_i2c_addr_list  = {<addr>},  // 填入 §0.6.3 提取到的全部 7bit I2C 地址；文档给出多个地址时全部填入（如 {0x30,0x32}），框架自动探测
    .sensor_name           = "<sensor>-<module_id>",
    .config_file           = "linear_<width>x<height>_raw<format_bitwidth>_<fps>fps_<lane>lane",
    .camera_config         = &<sensor>_camera_config,
    .vin_ichn_attr         = &<sensor>_vin_ichn_attr,
    .vin_node_attr         = &<sensor>_vin_node_attr,
    .vin_attr_ex           = &<sensor>_vin_attr_ex,
    .vin_ochn_attr         = &<sensor>_vin_ochn_attr,
    .isp_attr              = &<sensor>_isp_attr,
    .isp_ichn_attr         = &<sensor>_isp_ichn_attr,
    .isp_ochn_attr         = &<sensor>_isp_ochn_attr,
    .support_sensor_mode   = {<所有 setting 曝光模式>},  // 各 config 共用同一列表；slave 不计入（见 §0.6 support_sensor_mode）
};
```

### 3.10 <sensor>_common.h / <sensor>_common.c — read_chip_id_cb 回调实现（有 standby 寄存器时新建）

当 §0.6.3 判定需设 read_chip_id_cb 时，回调实现沉淀到独立编译单元 `<sensor>_common.h` + `<sensor>_common.c`（放在 `vp_sensors/<sensor>/` 目录下，随该目录 .c 一并被 wildcard 编译进 get_vin_data），各 vp_sensor 配置 .c `#include "<sensor>_common.h"` 后引用 `.read_chip_id_cb = <sensor>_read_chip_id`，禁止把回调实现塞进某个配置 .c 或用跨文件 extern 引用。

**<sensor>_common.h：**

```c
#ifndef VP_SENSORS_<SENSOR>_COMMON_H_
#define VP_SENSORS_<SENSOR>_COMMON_H_
#include "vp_sensors.h"

int32_t <sensor>_read_chip_id(vcon_propertie_t vcon_props, void *sensor_config,
                              uint32_t addr, int32_t *chip_id);

#endif
```

**<sensor>_common.c — 回调内部动作（强制顺序，不得省略）：**

```c
#include "<sensor>_common.h"
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/i2c.h>
#include <linux/i2c-dev.h>
#include <string.h>
#include <stdint.h>

int32_t <sensor>_read_chip_id(vcon_propertie_t vcon_props, void *sensor_config,
                              uint32_t addr, int32_t *chip_id)
{
    vp_sensor_config_t *cfg = (vp_sensor_config_t *)sensor_config;
    uint16_t chip_id_reg = cfg->chip_id_reg;        /* 寄存器地址，来自 vp_sensor_config_t */
    int32_t expect = cfg->chip_id;                  /* 期望值，同时用于判读 1 或 2 字节 */
    int read_len = (expect >> 8 == 0) ? 1 : 2;      /* chip_id>>8==0 读 8 位，否则读 16 位（与框架默认 read_chip_id 分支一致） */

    /* 动作1: 写 standby 寄存器 = "退出 standby"值（地址+值来自 §0.6.3 提取的数值含义）。
       回调运行在 get_vin_data 进程内（无 sensor_info_t），此处不能用 vin_i2c_write8
       （那是 libcam 驱动内部的 API），须用裸 I2C_RDWR ioctl 自行组包写，写法见动作3的读范例 */

    /* 动作2: standby 取消后稳压器稳定延时。datasheet 给值 ≤ 100ms 取 100ms,> 100ms 按 datasheet 值 */

    /* 动作3: 读 chip_id_reg。I2C_RDWR 组装形式（照搬 vp_sensors.c 的 vp_i2c_read_reg16_data8/16，
       2 个 msg：先写 reg16 地址，再读 data8/data16）。vcon_props.bus 为 I2C bus 号，addr 为 sensor i2c 地址 */
    int file;
    char filename[20];
    uint8_t sendbuf[2] = {0};
    uint8_t readbuf[2] = {0};
    struct i2c_msg msgs[2];
    struct i2c_rdwr_ioctl_data data;
    int32_t ret;

    snprintf(filename, sizeof(filename), "/dev/i2c-%d", vcon_props.bus);
    file = open(filename, O_RDWR);
    if (file < 0) return -1;

    sendbuf[0] = (uint8_t)((chip_id_reg >> 8u) & 0xffu);   /* reg16 高字节 */
    sendbuf[1] = (uint8_t)(chip_id_reg & 0xffu);           /* reg16 低字节 */

    data.msgs = msgs;
    data.nmsgs = 2;
    data.msgs[0].len = 2;        data.msgs[0].addr = addr; data.msgs[0].flags = 0;        data.msgs[0].buf = sendbuf;
    data.msgs[1].len = read_len; data.msgs[1].addr = addr; data.msgs[1].flags = I2C_M_RD; data.msgs[1].buf = readbuf;

    ret = ioctl(file, I2C_RDWR, (uint64_t)&data);
    close(file);
    /* I2C_RDWR 成功返回 msg 数(正数), 失败返回 -1, 不返回 0; 判成功用 >=0, 禁止 ==0 */
    if (ret < 0) return -1;

    /* 动作4: 与 vp_sensor_config_t.chip_id 比较，匹配返回0，否则-1。
       读2字节拼接固定为 (readbuf[0] << 8) | readbuf[1]（先收到的字节放高位，照搬 vp_sensors.c 的 vp_i2c_read_reg16_data16 实现） */
    int32_t actual = (read_len == 1) ? (readbuf[0] & 0xFF) : ((readbuf[0] << 8) | readbuf[1]);
    if ((expect == 0x005A) || (expect == 0xA55A)) return 0;
    if ((actual & ((read_len == 1) ? 0xFF : 0xFFFF)) == (expect & ((read_len == 1) ? 0xFF : 0xFFFF)))
        return 0;
    return -1;
}
```

**回调内部动作规定（强制，写进模板代码注释，不询问用户）：**
1. 先写 standby 寄存器为"退出 standby"值（地址+值来自 §0.6.3 提取）
2. standby 取消后稳压器稳定延时:datasheet 给值 ≤ 100ms 取 100ms,> 100ms 按 datasheet 值
3. 读 chip_id_reg，按 chip_id 字段宽度读 1 或 2 字节（chip_id>>8==0 读 1 字节，否则读 2 字节）。**读 2 字节时固定拼接为 `value = (rbuf[0] << 8) | rbuf[1]`（先收到的字节放高位）**，不询问用户、不因 sensor 型号变化
4. 与 chip_id 比较，匹配返回 0，不匹配返回 -1。**ioctl 返回值判断：I2C_RDWR 成功返回传输的 msg 数（正数），失败返回 -1，不返回 0**；故判成功用 `>= 0` 或判失败用 `< 0`，禁止用 `== 0` 判成功

---

## 4. vp_sensors.c 注册

```c
// extern 声明
extern vp_sensor_config_t <sensor>_linear_<width>x<height>_raw<format_bitwidth>_<fps>fps_<lane>lane;

// vp_sensor_config_list 数组中添加
&<sensor>_linear_<width>x<height>_raw<format_bitwidth>_<fps>fps_<lane>lane,
```

---

## 5. Online/Offline 模式规则

| 模式 | cim_isp_flyby | ddr_en | input_mode | bind_channel | 适用场景 |
|------|--------------|--------|------------|-------------|---------|
| **Offline** | 0 | 1 | DDR_MODE | 0 | 非 DOL2（默认） |
| **Online** | 1 | 0 | PASSTHROUGH_MODE | 1 | DOL2 模式（强制） |

**强制约束**：
- DOL2 模式必须 Online 且单路 pipeline
- 多路 pipeline 必须全部 Offline
- MCM 模式仅用于调试，release 版本禁用

**运行时控制**：
- `-c vf`：Vin offline ISP（默认）
- `-c vo`：Vin online ISP
- `-c vf:if`：Vin offline + ISP offline VSE（默认）
- `-c vf:io`：Vin offline + ISP online VSE


---

## 6. 常见遗漏点

| 序号 | 遗漏点 | 后果 |
|------|--------|------|
| 1 | 修改 sensor HTS/VTS 寄存器后，未同步修改 vp_sensor 配置中的 linelenth/framelenth | 帧率不对 |
| 2 | SC 系列 init 序列包含 stream on 命令（0x0100） | 数据溢出 |
| 3 | analog_gain_max/digital_gain_max 未按三目式 (条目数>256)?255:(条目数-1) 计算（无对应表填 0） | gain 范围错误 |
| 4 | lines_per_second 使用理论 VTS 而非实际寄存器值 | 曝光计算错误 |
| 5 | Online 模式下 vin_ochn_attr.ddr_en 设为 1 | 数据通路异常 |
| 6 | MCLK 未在 GPIO 之前使能 | I2C 通信失败 |
| 7 | 忘记在 vp_sensor_config_t 中填写 support_sensor_mode | sensor_mode 校验失败 |

---

## 7. 可选功能

### 7.1 AF（自动对焦）支持

需要实现 `sensor_af_init()` + `sensor_af_control()` 函数，在 sensor_module_t 中注册 `.af_control`，并在 `userspace_control` 中添加 `HAL_AF_CONTROL`。

在 `linear_data_init` 中设置 `turning_data->af_mode = 1`。


### 7.2 动态帧率切换

需要实现 `sensor_dynamic_switch_fps()` 函数，核心公式 `vts = lines_per_second / fps`。

在 sensor_module_t 中注册 `.dynamic_switch_fps`。


### 7.3 PDAF（相位对焦）支持

需要在 `linear_data_init` 中初始化 `pd_info_t` 结构体，包含 sensor_type、bit_width、image_width/height、pd_area、pd_num_per_area、pdfocal 等参数。


### 7.4 Slave Mode/多摄同步

- 从 sensor 在 `support_sensor_mode` 中声明 `SLAVE_M`
- 运行时使用 `-m s` 参数启动从 sensor
- 框架自动启用 LPWM 同步
- 可通过 `-e json_file` 动态修改 LPWM 参数


### 7.5 JSON 外部参数注入

运行时通过 `-e <json_file>` 参数覆盖 sensor 配置，支持的参数：settle、lpwm_attr。

调试阶段可频繁修改参数而无需重编。
