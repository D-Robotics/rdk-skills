---
## name: sensor-debug-experience-mipi
description: Direct MIPI Camera（无 Serializer/Deserializer）调试经验。当 Direct MIPI sensor 调试出现 I2C 通信异常、MIPI PHY fatal、lane state error、无法进入 HS、SIF 报错、overflow 等现象时，按本文件各检查项的触发特征与合法去向定位修复。
---

# Direct MIPI Camera Debug Experience

本文档记录 Direct MIPI Camera（无Serializer/Deserializer）的调试经验。各排查项由检查项名唯一标识，合法去向按检查项名跳转，无编号。判定型（动作=只观测，结论从值比对直接读出，多分支各跳唯一去向，叶子=提修改）与轮流型（动作=施加候选+回测，结论=过/不过，过则报告成功并停、不过跳下一候选、末候选不过经验未覆盖）由「动作」字段填什么区分，不设模式字段。

---

## 零、排查的强制执行规则（适用于本文档所有排查项）

所有排查项均遵守以下规则，违反任一条即视为违规，必须自我纠正：

1. 从带触发特征的入口检查项开始，不得从其他检查项开始。先从三类日志来源（测试打印、logcat、dmesg）分析出具体的异常点，匹配到带该触发特征的入口检查项；匹配不到任何入口项 → 经验未覆盖，停下问用户。
2. 每个检查项由三要素构成：`动作`、`汇报`、`合法去向`，缺一不可。
3. `汇报` 字段必须写明实际值、期望值、结论。
4. `合法去向` 中只能填该检查项定义的下一检查项名，或终止标记（`提修改` / `经验未覆盖` / `报告成功并停`），不得填"分析""推测""排查原因""自由检查"等。检查项名全文件唯一，按名跳转，无编号。
5. 输出`汇报`后不得直接开始分析或提修改，必须先按`合法去向`跳转到下一个检查项并执行它。
6. 若某检查项的`合法去向`与实际情况均不匹配（结论落在定义之外），`合法去向` 填 `经验未覆盖`，停下来问用户。
7. 一次测量只解读当前检查项对象对应的字段。读寄存器返回的值常含多个字段，本检查项对象是哪个字段，就只解读、只汇报那个字段；其他字段即便看似指向更可疑的根因，也不得据此改换排查对象。想查其他字段=自由检查，违规；若确信根因在别处，按合法去向走或填"经验未覆盖"停下。
8. 合法去向是硬闸门。汇报后，下一步动作必须严格等于合法去向列表中的某一项。在"汇报"与"下一个检查项"之间，不得插入任何未在合法去向中列出的检查、读取、分析。若想做的下一步不在列表中 → 违规，退回按合法去向走。
9. 轮流型候选须按检查项链既定顺序逐个"施加候选+回测"，过则止；禁止跳序、禁止凭猜测选定候选；末候选不过→`经验未覆盖`停下问用户。候选修复是经验预定的（出处=该候选检查项名），非自创。
10. 查看日志时不得使用 `tail -N` / `head -N` 等限制日志数量的命令，直接使用完整的 `dmesg` / `logcat` 输出（可用 `grep` 过滤关键词，但不得截断数量）。

各检查项只写"触发特征 + 动作 + 汇报 + 合法去向"，不重复以上规则。

---

## 寄存器排查原则

排查 MIPI/Sensor 寄存器时，必须遵循以下原则：

1. **先查手册再下结论** — 遇到不清楚的寄存器位含义时，优先调用 knowledge-rag 的 `search_register` 工具（给寄存器地址 0xXXXX 或名称，可限定 chip）检索对应芯片手册的寄存器位定义，确认后再做判断
2. **禁止凭猜测断言** — 不能对任何寄存器值凭猜测下结论，必须用 `search_register` 查手册确认该值在该寄存器位定义下的实际含义
3. **手册不完整时主动搜索** — 如果 `search_register` 返回的位定义标注为 – 或明显残缺，应主动搜索该芯片的完整 datasheet/programming guide，补充理解后再下结论
4. **标注结论来源** — 对寄存器值的解读应标注来自哪份文档的具体位置，方便后续验证

---

## I2C 通信异常

### i2cdetect timeout 检查

* 触发特征：i2cdetect -y -r <bus> 返回 timeout
* 动作：观测 I2C 驱动能力配置（设备树 `drive-strength`）
* 汇报：实际/期望=drive-strength 当前值 / 期望 2(mA)；结论=偏小 / 不偏小
* 合法去向：
  * 偏小 → 提修改（设备树 drive-strength 改 2，改后回第4步重验）
  * 不偏小 → i2cdetect 无法检测到 sensor 地址检查

### i2cdetect 无法检测到 sensor 地址检查

* 触发特征：i2cdetect -y -r <bus> 扫描不到该 sensor 7bit 地址
* 动作：按顺序逐个施加候选修复 + 回测（走第3步编译推送安装 + 第4步验证）
* 汇报：结论=过(探测到地址) / 不过(未探测到)
* 合法去向：
  * 过 → 报告成功并停（根因=该项，已验证修复）
  * 不过 → dlsym 库名检查

### dlsym 库名检查

* 动作：检查测试日志有无 `dlsym libxxx.so:xxx failed`，若有确认库名 `libxxx.so` 是否为当前 sensor 名扩展（如 sensor 名 `ovx`→`libovx.so`）
* 汇报：实际/期望=库名 / 当前 sensor 名扩展；结论=库名不对 / 库名对
* 合法去向：
  * 库名不对 → 提修改（修正库名，改后回第4步重验）
  * 库名对 → reset GPIO 生效检查

### reset GPIO 生效检查

* 动作：检查 reset GPIO 配置是否正确、硬件是否生效
* 汇报：结论=未生效 / 生效
* 合法去向：
  * 未生效 → 提修改（修正 reset GPIO 配置，改后回第4步重验）
  * 生效 → MCLK 配置检查

### MCLK 配置检查

* 动作：先判定时钟来源，再查配置是否生效。判定只认这两类事实：用户明确说明模组或转接板自带 24MHz；或 `board_info/rdkx5_board.md` 已列的自带晶振模组（22pin 的 IMX219、IMX477、OV5647，以及 22pin 转 24pin 自带 24M 晶振转接板上的 SC230AI、SC132gs、IMX415）。sensor 手册只写 INCK=24MHz 不算来源。
* 汇报：结论=自带晶振 / SoC供钟 / 来源不明 / 未生效 / 生效
* 合法去向：
  * 自带晶振（rdkx5，模组或转接板自带 24MHz）→ 模组自带 MCLK 上电复测
  * SoC供钟（rdkx5，必须由 SoC 提供 MCLK，且 i2cdetect 扫描不到外设）→ SoC MCLK DTS 检查
  * 来源不明 → 停下问用户。问清前不改 `x5-rdk.dtsi`，不写 `snrclk_en`
  * 未生效（非 rdkx5）→ 提修改（修正 MCLK 配置，改后回第4步重验）
  * 生效（非 rdkx5）→ 手动辅助上电复测

### 模组自带 MCLK 上电复测

* 动作：只做 reset GPIO 释放，不改 DTS，不写 `snrclk_freq` / `snrclk_en`。`RESET_PIN` 来自 `board_info/<board>_board.md` 中该 mipi_host 的 reset 引脚。执行后用 i2cdetect 复测该 sensor 7bit 地址。
  ```sh
  if [ ! -d "/sys/class/gpio/gpio${RESET_PIN}" ]; then
      echo "$RESET_PIN" > /sys/class/gpio/export
  fi

  echo out > /sys/class/gpio/gpio${RESET_PIN}/direction
  echo 0 > /sys/class/gpio/gpio${RESET_PIN}/value
  sleep 0.1
  echo 1 > /sys/class/gpio/gpio${RESET_PIN}/value
  ```
* 汇报：结论=探测到 / 未探测到
* 合法去向：
  * 探测到 → 报告成功并停
  * 未探测到 → I2C bus/addr 配置检查

### SoC MCLK DTS 检查

* 动作：只读本次接入的那一个 `mipi_host`（用户给出的 mipi_index）。对照 `board_info/rdkx5_board.md` 例外表，核对该节点是否已有 `pinctrl-names = "enable", "disable"`、`pinctrl-0`、`pinctrl-1`、`snrclk-idx`。不读、不改其它 host。
* 汇报：实际/期望=该节点现有四项 / 例外表中该 host 的四项；结论=已一致 / 未一致
* 合法去向：
  * 已一致 → SoC MCLK sysfs 复测
  * 未一致 → 提修改：只给这一路补上例外表中的四项。然后在 `rdk-x5-bsp` 根目录执行 `sudo ./mk_kernel.sh` 与 `sudo ./mk_debs.sh hobot-dtb`。安装该 deb 与重启前必须先向用户确认，确认前不安装、不重启。新 DTB 生效后再进入 SoC MCLK sysfs 复测

### SoC MCLK sysfs 复测

* 动作：只对已改的那一路写 sysfs，频率用参数清单里已定的 MCLK（24MHz 写 24000000）。写完后用 i2cdetect 复测该 sensor 7bit 地址。
  ```sh
  echo "$MCLK" > /sys/class/vps/mipi_host${MIPI_HOST}/param/snrclk_freq
  echo 1 > /sys/class/vps/mipi_host${MIPI_HOST}/param/snrclk_en
  ```
* 汇报：结论=探测到 / 未探测到
* 合法去向：
  * 探测到 → 报告成功并停
  * 未探测到 → I2C bus/addr 配置检查

### 手动辅助上电复测

* 动作：非 rdkx5 板。在板端手动执行辅助上电，使 sensor 进入可被 I2C 探测的状态，执行后再用 i2cdetect 复测该 sensor 7bit 地址。需先确定 3 个变量：
  - `MCLK`：MCLK 频率(Hz)，来自手册提取（如 IMX415 INCK=24MHz → 24000000）
  - `RESET_PIN`：reset GPIO 编号，来自板端约束 `board_info/<board>_board.md` 中该 mipi_host 对应的 reset 引脚（如 X5_EVB mipi_host0 → GPIO 498）
  - `MIPI_HOST`：MIPI host 号，来自用户输入的 mipi_index（如 mipi_index=0 → 0）
  ```sh
  if [ ! -d "/sys/class/gpio/gpio${RESET_PIN}" ]; then
      echo "$RESET_PIN" > /sys/class/gpio/export
  fi

  echo out > /sys/class/gpio/gpio${RESET_PIN}/direction
  echo 0 > /sys/class/gpio/gpio${RESET_PIN}/value
  sleep 0.1
  echo 1 > /sys/class/gpio/gpio${RESET_PIN}/value

  echo "$MCLK" > /sys/class/vps/mipi_host${MIPI_HOST}/param/snrclk_freq
  echo 1 > /sys/class/vps/mipi_host${MIPI_HOST}/param/snrclk_en
  ```
  操作顺序：先 export 并配置 reset GPIO 为 out → 拉低 0 → sleep 0.1 → 拉高 1（释放 reset）→ 再设 snrclk_freq → 使能 snrclk_en（给 MCLK）。执行后 i2cdetect 复测。
* 汇报：结论=探测到 / 未探测到
* 合法去向：
  * 探测到 → 报告成功并停（根因=reset/MCLK 未生效，手动上电后可探测，据前面 reset GPIO/MCLK 检查结论提修复）
  * 未探测到 → I2C bus/addr 配置检查

### I2C bus/addr 配置检查

* 动作：列举当前 sensor 配置的 I2C bus number 和 I2C addr，与实际硬件配置核对是否相符
* 汇报：实际/期望=配置 bus/addr vs 硬件实际；结论=不相符 / 相符
* 合法去向：
  * 不相符 → 提修改（修正 bus/addr 配置，改后回第4步重验）
  * 相符 → 经验未覆盖

---

## MIPI PHY Fatal 报错

### settle 配置检查

* 触发特征：`vin mipiN: irq status 0x1` / `vin mipiN: phy_fatal: 0x3` 反复出现，随后 `hbn_vnode_getframe s0 CIM failed`
* 动作：施加 settle=0（若缺则同时增配 `.rx_ex_mask=0x40` / `.rx_attr_ex.stop_check_instart=1`）；回测
* 汇报：结论=过 / 不过
* 合法去向：
  * 过 → 报告成功并停（根因=settle/高速配置）
  * 不过 → rx_ex_mask 配置检查

### rx_ex_mask 配置检查

* 动作：检查现有 `mipi_config_t` 是否有 `.rx_ex_mask=0x40` / `.rx_attr_ex.stop_check_instart=1`，没有则增配；回测（若 settle 项已加则直接回测确认）
* 汇报：结论=过 / 不过
* 合法去向：
  * 过 → 报告成功并停（根因=rx_ex_mask/高速配置）
  * 不过 → VTS/HTS/mipiclk 配置检查

### VTS/HTS/mipiclk 配置检查

* 动作：检查 `framelenth`(VTS)、`linelenth`(HTS)、`mipiclk` 是否与提取参数一致，不一致则改；回测
* 汇报：结论=过 / 不过
* 合法去向：
  * 过 → 报告成功并停（根因=VTS/HTS/mipiclk 不匹配）
  * 不过 → HTS 公式重算检查

### HTS 公式重算检查

* 动作：按公式 `HTS = mipiclk × 10⁶ / (VTS × FPS × format_bitwidth)` 重算 HTS（mipiclk 取 `mipi_config_t.mipiclk` 字段值，×10⁶ 换算 bit/s，不再额外乘 lane 数，向下取整），填入；回测
* 汇报：结论=过 / 不过
* 合法去向：
  * 过 → 报告成功并停（根因=HTS 取值来源错误，须按公式而非 setting/文档/用户输入）
  * 不过 → 板端 reboot 检查

### 板端 reboot 检查

* 动作：reboot 测试板端，不改任何代码，重新测试
* 汇报：结论=过 / 不过
* 合法去向：
  * 过 → 报告成功并停（根因=板端状态）
  * 不过 → 经验未覆盖

---

## lane state of host phy is error 报错

### lane 配置一致性检查

* 触发特征：`vin mipiN: lane state of host phy is error: 0x1000d`（可能伴随 `0x0`）/ `vin mipiN: wait phy stop state error` / `vin mipiN: init error: -1`
  - lane 配小/不匹配日志：`vin mipiN: lane state of host phy is error: 0xc`（或 `0xd`）/ `vin mipiN: start error: -1` / `sensor_frame_end_stop_wait ... fe ... timeout`（init 与 stream on 均成功，PHY lane state 异常收不到帧）
  - lane 配大日志：`vin mipiN: phy_fatal: 0x100` 反复出现（多条连续）/ `sensor_frame_end_stop_wait <N> fe 0ms abort`（init 成功进入出流，但 PHY fatal 持续收不到帧，无 lane state error 行）
* 动作：向用户输出当前 `mipi_config_t.lane` 配置值，提醒用户检查 lane 配置是否与板端物理 data lane 接线数相符（`mipi_config_t.lane` 是 host 接收侧物理接线数，可与 sensor init 寄存器 lane 数不同）；回测
* 汇报：结论=过 / 不过
* 合法去向：
  * 过 → 报告成功并停（根因=lane 数不一致）
  * 不过 → lane state rx_ex_mask 配置检查

### lane state rx_ex_mask 配置检查

* 动作：检查现有 `mipi_config_t` 是否有 `.rx_ex_mask=0x40` / `.rx_attr_ex.stop_check_instart=1`，没有则增配；回测
* 汇报：结论=过 / 不过
* 合法去向：
  * 过 → 报告成功并停（根因=rx_ex_mask/高速配置）
  * 不过 → 经验未覆盖

---

## 无法进入 HS，mipi start error

### HS reception 失败定位

* 触发特征：`vin mipiN: check hs reception` / `vin mipiN: hs reception check error 0x10000` / `vin mipiN: hs reception state error` / `vin mipiN: start error: -1`
* 动作：判断 sensor 是"没有正常出流"还是"提前出流"（按 init 序列是否含 stream on 命令判定，判定方法见「如何判断 init 序列末尾 stream 命令是 on 还是 off」）
* 汇报：结论=sensor 没有正常出流 / sensor 提前出流
* 合法去向：
  * sensor 没有正常出流 → sensor 出流状态检查
  * sensor 提前出流 → stream on 位置修正检查

### sensor 出流状态检查

* 动作：区分 master/slave。slave mode sensor：需外部 trigger 信号才能出流，确认 trigger 是否已正确配置；master mode sensor：检查代码流程确认 sensor stream on 是否执行成功，可用示波器测 MIPI data lane 确认有无数据
* 汇报：结论=trigger 未配置(slave) / stream on 未执行(master) / 正常出流
* 合法去向：
  * trigger 未配置(slave) → 提修改（配置 trigger，改后回第4步重验）
  * stream on 未执行(master) → 提修改（修复 stream on 流程，改后回第4步重验）
  * 正常出流 → 经验未覆盖

### stream on 位置修正检查

* 动作：查看 setting 中的 stream on 配置，若有 stream on 则将 stream on 操作移到 `sensor_start()` 中执行（init 序列中去除）
* 汇报：结论=含 stream on(已移至 sensor_start) / 无 stream on
* 合法去向：
  * 含 stream on(已移至 sensor_start) → 提修改（stream on 移至 sensor_start，init 去除 stream on，改后回第4步重验）
  * 无 stream on → 经验未覆盖

### 如何判断 init 序列末尾 stream 命令是 on 还是 off（通用判定方法）

部分厂商 init 序列末尾会带一对 stream 控制寄存器，需先判断是 on 还是 off 再决定是否从 init 中去除：

* on（出流）→ 必须从 init 去除，独立成 `stream_on_setting[]`，由 `sensor_start()` 调用
* off（待机）→ 保留在 init 中，不需去除

通用判定方法（不依赖具体寄存器地址，地址随 sensor 型号而异）：

1. 从该 sensor 的 datasheet 查 stream 控制寄存器（standby/mode 类寄存器）的位定义
2. 按位定义区分两个状态方向：`运行/出流(operating/start)` 与 `待机/就绪(standby/ready)`
3. 写入值为"运行/出流"方向的 → 是 stream on，须从 init 去除
4. 写入值为"待机/就绪"方向的 → 是 stream off，保留在 init 中
5. stream_on_setting 取其反方向（待机→运行）的写入值

关键：寄存器地址与位值随型号不同，必须查对应 datasheet，禁止套用其它型号的寄存器地址。

---

## SIF 报错

### linelenth/width 一致性检查

* 触发特征：`hobot-sif <addr>.sif: sif frame size incorrect, hsize count:0x<XXX> vsize count:0x<XXX> for inst:0`
* 动作：检查 vp_sensor 配置中的 `linelenth`(HTS) 和 `width` 是否与参数提取出的 HTS 和实际图像 width 一致
* 汇报：实际/期望=配置 linelenth/width vs 提取 HTS/实际 width；结论=不一致 / 一致
* 合法去向：
  * 不一致 → 提修改（修正 linelenth/width，改后回第4步重验）
  * 一致 → 经验未覆盖

---

## mclk config error / create_and_run_vflow failed

### mclk 配置检查

* 触发特征：
  测试打印：`INFO: Found sensor_name:xxx on mipi rx csi 0, i2c addr 0x..., config_file:...` / `Index 0 sensor_name(xxx) specify sensor mode to NORMAL_M` / `create_and_run_vflow(341) failed, ret -10` / `create_and_run_vflow failed for sensor <index>. ret = -10`
  dmesg：`vin mipiN: mclk <填入值> should >= 637(6375000Hz)` / `vin mipiN: mclk config error!` / `vin mipiN: init error: -1`
* 动作：核对配置的 mclk 当前值与期望
* 汇报：实际/期望=mclk 当前值 / 期望值；结论=需用户确认
* 合法去向：
  * 需用户确认 → 停下问用户 mclk 是否是（mclk 当前值），用户确认后据实填值或修正
  * （mclk 文档/规则已明确则不确认，按值填——见 SKILL『入清单前的过滤判据』与 patterns_mipi 的 mipiclk 判据）
