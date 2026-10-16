# ISP pipeline tuning（仅建链）

当前项目 conf 含 `isp_test_dir` 时才读本文件。用途是让 `get_isp_data` 建链并吐出一帧 NV12。画质不在本文件范围。

## 生成

模板路径 = 项目根目录 + conf 的 `isp_tuning_src`。模板不存在则停下，告知缺失路径。不得改用其它 sensor 的 tuning 当模板。

输出路径 = 模板所在目录 + `/<sensor>_tuning.json`。`<sensor>` 与本次 `camera_config_t.name` 一致。

分辨率、datatype、bayer 只用第 1 步参数清单里已经定下的 `width`、`height`、datatype、bayer。这几项没有定值则停下，不得填默认分辨率或默认 Bayer。

只允许改这些结构字段：

1. 传感器名称字符串改为 `<sensor>`。
2. 模板中的分辨率名称字符串全部改为 `{width}x{height}`。
3. 数值形式的宽、高，以及 IPT、OPT、内部处理窗口的宽高，全部改为参数清单中的 width、height。只改字符串、数值仍是模板分辨率，视为未完成。
4. Bayer 排列与位宽改为与参数清单的 bayer、datatype 一致。模板已经与本次一致则保持原值。

BLS、AWB、LSC、AEC 以及其它算法表保持模板原值。不得为改善画质改这些表。

`camera_config_t.calib_lname` 填 `"<sensor>_tuning.json"`。

## 安装后核对

板端路径 = conf 的 `isp_tuning_board`，把 `{sensor}` 换成 `<sensor>`。

`hobot-camera` 安装完成后检查该路径。文件不存在时，把源码中的 `<sensor>_tuning.json` 拷到该路径，权限 `0644`。不得把板端 IP 写回 conf。重装 deb 会覆盖板端文件，源码里的 JSON 必须保留。

## ISP 失败时的检查项

`get_isp_data` 未满足 SKILL.md 第 4.2 节的三条成功条件时，只走下面三项。检查阶段只汇报，不提修改。三项的实际值都与期望一致、测试仍失败 → `经验未覆盖`，停下问用户。不得改 BLS、AWB、LSC、AEC。

### 板端 tuning 文件存在检查

* 触发特征：`get_isp_data` 失败，或日志找不到 `sensor_cali_name`
* 动作：只检查板端 `isp_tuning_board` 路径上文件是否存在
* 汇报：`实际值/期望值` = 存在或缺失 / 文件存在 ; `结论` = 文件存在 / 文件缺失
* 合法去向：
  * 文件存在 → 标定名一致检查
  * 文件缺失 → 提修改：把源码 `<sensor>_tuning.json` 拷到该路径，权限 `0644`，然后回到第 4.2 节

### 标定名一致检查

* 触发特征：上一检查项结论为文件存在
* 动作：只核对 dmesg 或 logcat 里的 `sensor_cali_name`，以及源码 `camera_config_t.calib_lname`
* 汇报：`实际值/期望值` = 日志中的名字与 calib_lname / 二者都是 `<sensor>_tuning.json` ; `结论` = 一致 / 不一致
* 合法去向：
  * 一致 → 分辨率窗口检查
  * 不一致 → 提修改：把 `calib_lname` 改为 `"<sensor>_tuning.json"`，重新编译安装，然后回到第 4.2 节

### 分辨率窗口检查

* 触发特征：上一检查项结论为一致
* 动作：只核对 tuning JSON 里的分辨率名称、数值宽高、IPT、OPT、内部处理窗口
* 汇报：`实际值/期望值` = JSON 中的宽高 / 参数清单的 width、height ; `结论` = 全部一致 / 仍有模板分辨率
* 合法去向：
  * 全部一致 → 经验未覆盖
  * 仍有模板分辨率 → 提修改：按本文件「生成」节改全窗口后重新部署，然后回到第 4.2 节
