
---

## name: sensor-debug-experience-serdes
description: SerDes Camera（GMSL Serializer/Deserializer 链路）调试经验。当 SerDes sensor 调试出现 Serializer/Deserializer/Sensor 寄存器异常、Link Lock/Video Lock 失败、I2C 透传不通、PCLKDET/VID_LOCK 异常等现象时，按本文件的寄存器排查原则与触发特征定位修复。

# Sensor Debug Experience

本文档整理自 experience/raw/ 目录下的所有调试文档，包含 Serializer、Deserializer 和 Sensor 三部分的调试经验。


---

## 零、排查的强制执行规则（适用于本文档所有排查项）

所有排查节均遵守以下规则，违反任一条即视为违规，必须自我纠正：


 1. 从该排查节的入口检查项开始，不得从其他检查项开始
 2. 每个检查项由三要素构成：`动作`、`汇报`、`合法去向`，缺一不可
 3. `汇报` 字段必须写明实际值、期望值、结论
 4. `合法去向` 中只能填该检查项定义的下一检查项名，或终止标记（`提修改` / `经验未覆盖`），不得填"分析""推测""排查原因""自由检查"等。检查项名全文件唯一，按名跳转，无编号
 5. 当前检查项是叶子项（无`合法去向`）时，`合法去向` 填 `提修改`
 6. 输出`汇报`后不得直接开始分析或提修改，必须先按`合法去向`跳转到下一个检查项并执行它
 7. 若某检查项的`合法去向`与实际情况均不匹配（结论落在定义之外），`合法去向` 填 `经验未覆盖`，停下来问用户
 8. 一次测量只解读当前检查项对象对应的字段。读寄存器返回的值常含多个字段。本检查项对象是哪个字段，就只解读、只汇报那个字段；其他字段即便看似指向更可疑的根因，也不得据此改换排查对象。想查其他字段=自由检查，违规；若确信根因在别处，按合法去向走或填"经验未覆盖"停下。
 9. 合法去向是硬闸门。汇报后，下一步动作必须严格等于合法去向列表中的某一项。在"汇报"与"下一个检查项"之间，不得插入任何未在合法去向中列出的检查、读取、分析。若想做的下一步不在列表中 → 违规，退回按合法去向走。

各排查节只写"检查项 + 合法去向"，不重复以上规则。


## 一、寄存器排查原则

排查 SER/DES 寄存器时，必须遵循以下原则：


1. **先查手册再下结论** — 遇到不清楚的寄存器位含义时，优先调用 knowledge-rag 的 `search_register` 工具（给寄存器地址 0xXXXX 或名称，可限定 chip）检索 reference/ 下对应芯片手册的寄存器位定义，确认后再做判断
2. **禁止凭猜测断言** — 不能对任何寄存器值凭猜测下结论，必须用 `search_register` 查手册确认该值在该寄存器位定义下的实际含义
3. **手册不完整时主动搜索** — 如果 `search_register` 返回的位定义标注为 – 或明显残缺，应主动搜索该芯片的完整 datasheet/programming guide，补充理解后再下结论
4. **标注结论来源** — 对寄存器值的解读应标注来自哪份文档的具体位置（如"MAX9295A_registers.md §GPIO"），方便后续验证
5. **SER/Sensor 运行时 I2C 地址 = 配置值 + link_index 偏移** — SER 与 Sensor 的运行时 I2C 地址不是配置值本身，而是 `serial_addr / sensor_addr 配置值 + link_index 偏移`。link_index 字母→偏移：A→1, B→2, C→3, D→4（如 serial_addr=0x40, link_index=C → 运行时 SER 地址 0x43）。i2cdetect / i2ctransfer 验证 SER/Sensor 时直接用此运行时地址，不要用配置值地址。⚠️ 解串器（Deserializer）与 POC 的 I2C 地址不加偏移，仍用配置值本身，两者不要搞混


---

## I2C 寄存器配置失败

**定位不通对象**

* 触发特征：logcat I2C 写失败重试链 `camera_i2c_write_reg16_data8 ... ioctl r16d8 write <bus>@<运行时sensor_addr> <reg> <val> ret -1` 连续 retry 多次（如 retry 1~20）→ `set trig stream off failed` / `sensor config_index do start fail` / `sensor start error -1` → `create_and_run_vflow failed, ret -36`；dmesg：`sensor_detach flow0 link0 from sensorN <sensor>` + `release i2c<bus>@<运行时sensor_addr>`
* 动作：分别对 SER 地址、Sensor 地址做 i2cdetect -y -r <bus> 扫描
* 汇报：`实际值/期望值`= SER(通/不通) Sensor(通/不通)；`结论`= 仅SER不通 / 仅Sensor不通 / 两者都不通
* 合法去向：
  * 仅SER不通 → DES poc_map 配置检查
  * 两者都不通 → DES poc_map 配置检查
  * 仅Sensor不通 → MCLK 配置检查

**DES poc_map 配置检查**

* 动作：读 DES 的 poc_map 相关寄存器，与代码写入的期望值对比
* 汇报：`实际值/期望值`= ；`结论`= 成功 / 失败
* 合法去向：
  * 成功 → GMSL 速率匹配检查
  * 失败 → 提修改（重新配置 poc_map，改后回「定位不通对象」重新定位）

**MCLK 配置检查**

* 动作：读 SER 输出 MCLK 给 sensor 的配置寄存器（非 PIO 寄存器），与代码写入的期望值对比
* 汇报：`实际值/期望值`= ；`结论`= 生效 / 未生效
* 合法去向：
  * 生效 → SER Reset 驱动能力检查
  * 未生效 → 经验未覆盖

**SER Reset 驱动能力检查**

* 动作：检查SER Reset 引脚当前驱动能力配置，查询代码中配置ser reset驱动能力的寄存器，再在ser手册中查找这个寄存器配置的驱动能力是偏大还是偏小的
* 汇报：`实际值/期望值`= ；`结论`= 偏大 / 偏小 / 未知
* 合法去向：
  * 偏大 → 提修改（原代码reset执行后调小驱动能力并重新reset; 重新reset的方法完全仿照原代码中reset执行; 修改不能影响其他sensor代码执行）
  * 偏小 → 提修改（原代码reset执行后调大驱动能力并重新reset; 重新reset的方法完全仿照原代码中reset执行; 修改不能影响其他sensor代码执行）
  * 未知 → 经验未覆盖

**GMSL 速率匹配检查**

* 动作：检查 从文档中获取的GMSL 速率，与 emode 中的L字段是否匹配
* 汇报：`实际值/期望值`= ；`结论`= 匹配 / 不匹配
* 合法去向：
  * 匹配 → 经验未覆盖
  * 不匹配 → 提修改（修改emode 中的L字段与文档中获取的GMSL 速率匹配）



## Tuning Init 失败

**定位失败阶段**

* 触发特征：logcat 出现 `camera_sensor_dev_tuning_init` / `tuning init` / `SENSOR_TUNING_PARAM` 报错，记录错误码（如 -65670 = -HBN_STATUS_CAM_SENSOR_DEV_ERROR）
* 动作：从 logcat 确认失败发生在 init 阶段还是 start 阶段
* 汇报：`实际值/期望值`= 失败阶段(init/start) + 错误码 ; `结论`= tuning init 阶段失败 / 非 tuning 阶段失败
* 合法去向：
  * tuning init 阶段失败 → sensor_mode 支持检查
  * 非 tuning 阶段失败 → 经验未覆盖

**sensor_mode 支持检查**

* 动作：检查 vp_sensor 配置的 `camera_config_t.sensor_mode` 取值，对照 `camera_sensor_dev_tuning_fill_init`（camera_sensor_dev.c）的 switch 分支。switch 仅支持：NORMAL_M(1)/DOL2_M(2)/DOL3_M(3)/DOL4_M(4)/PWL_M(5)；不支持 SLAVE_M(6)，SLAVE_M 落入 default 分支返回 -HBN_STATUS_CAM_NOT_SUPPORT，最终 ret -65670
* 汇报：`实际值/期望值`= sensor_mode(实际值) vs switch支持列表 ; `结论`= 支持 / 不支持(SLAVE_M)
* 合法去向：
  * 支持 → 经验未覆盖
  * 不支持(SLAVE_M) → 提修改（将 sensor_mode 从 SLAVE_M(6) 改为 NORMAL_M(1)；触发同步改由 config_index 触发位(如 TRIG_SHUTTER_SYNC=512) + deserial_config 的 gpio_mfp\[CAMERA_DES_GPIO_TRIG0\]=0x5 承载，不用 sensor_mode=6）

> 来源：ISX031 MINGMO 模组调试 — sensor_mode=6(SLAVE_M) 致 tuning fill 落 default 分支 ret -65670，改 NORMAL_M(1)+config_index=512+gpio_mfp=0x5 后通过


## GMSL Speed 配置错误

**GMSL 速率平台支持检查**

* 触发特征：logcat 错误链 `the serial type X don't support gmsl speed Ygbps` → `gmsl speed init fail` → `deserial init error -65674` → `create_and_run_vflow failed, ret -65674`；dmesg：`deserial_init_result cmd: invalid wake`
* 动作：报错串行器型号（serial type X，由 emode 名 S 字段定）与被拒速率（Y gbps，由 L 字段定：L3→3Gbps/L6→6Gbps）；查 drivers/deserial/_common/max_common.c 的 serial_links[] 该 serial_type 条目 select[]，确认 Y gbps 不在 select[] 内
* 汇报：`实际值/期望值`= emode L 速率(Y gbps) vs serial_links[该serial].select[] 支持速率 ; `结论`= 平台不支持该速率
* 合法去向：
  * 平台不支持该速率 → GMSL 速率取值确认
  * 平台支持该速率 → 经验未覆盖

**GMSL 速率取值确认**

* 动作：emode L 字段当前设置值（如 L6=6Gbps）不被该串行器平台 serial_links 表支持，停下询问用户：gmsl 是否应设为当前设置值，还是改为平台支持速率（如 L3，或去 L 走默认）
* 汇报：`实际值/期望值`= 当前 L 速率 / 平台支持速率集合 ; `结论`= 需用户确认
* 合法去向：
  * 改为平台支持速率 → 提修改（emode L 字段改值或去 L，同步改 emode 枚举名/emode_data/sensor_emode 三处引用，回第4步重验）
  * 保持当前速率 → 提修改（serial_links[该serial].select[] 加当前速率，影响所有该型号模组）
  * 经验未覆盖 → 停下问用户
