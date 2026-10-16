---
name: cmos-sensor-bringup
description: >-
  点亮 SerDes camera 和 direct MIPI camera 的新 sensor bring-up：收集项目与接入信息，按规律提取参数、生成驱动代码，再编译推送到板端验证。项目 conf 含 isp_test_dir 时，RAW（get_vin_data）通过后继续跑 get_isp_data。
  触发词: 调试新 sensor、$cmos-sensor-bringup、点亮 camera、mipi_index、link_index、serdes camera、direct mipi camera、get_isp_data。
  不要用于：BSP 源码同步、整机镜像或与本次 sensor 无关的编译；寄存器位定义查询交给 knowledge-rag。
version: "1.1.1"
license: Apache-2.0
metadata:
  content-license: CC-BY-4.0
  tags: [sensor, serdes, mipi, bring-up]
---

# CMOS Sensor Bringup

## Purpose

点亮一颗新 sensor。从用户给出的项目、文档和接入位置出发，按规律提取参数、改驱动、编译推送到板端。先验证 RAW（get_vin_data）。当前项目 conf 含 `isp_test_dir` 时，RAW 通过后继续验证 ISP（get_isp_data）。验证失败时按经验文件排查。入口是本 skill，不是计划模式。

## When to use

Use when:

- 用户说「调试新 sensor」，或调用 `$cmos-sensor-bringup`
- 需要点亮 SerDes camera 或 direct MIPI camera

Do not use:

- BSP 源码同步、整机镜像、与本次 sensor 无关的编译。这些不是本 skill 的范围。
- 只查寄存器位定义。调用 knowledge-rag 的 `search_register`，传 `chip` 限定芯片型号；芯片不在已索引清单内时，工具会返回「未索引该手册」并列出已索引芯片，无需自行核验。

## Instructions

当用户调用本 skill 或说「调试新 sensor」时，不要进入 plan 模式，不要创建规划，直接按下列顺序执行。

### 可参考文件

调试时只能参考：`code_ruler/patterns_serdes.md` 或 `code_ruler/patterns_mipi.md`（根据 sensor 类型）、`board_info/<board>_board.md`（根据 `project_info/<项目名>_project.conf` 中的 board 值加载对应板级文件，如 board=x5_evb→x5_evb_board.md、board=rdkx5→rdkx5_board.md、board=s100_6v→s100_6v_board.md、board=s100_12v→s100_12v_board.md、board=s600→s600_board.md；只加载当前板，不加载其它板；若对应文件不存在则停下报错给用户，告知缺失的文件名与 board 值，不得静默跳过继续执行）、`experience/sensor-debug-experience-serdes.md` 或 `experience/sensor-debug-experience-mipi.md`（根据 sensor 类型）。当前项目 conf 含 `isp_test_dir` 时，还须读取 `code_ruler/isp_pipeline_tuning.md`。寄存器位定义只调用 knowledge-rag 的 `search_register`，不读取 `reference/` 下的 PDF。

### 前置

必须先直接用文字询问用户以下信息（不要使用提问表单或选择题界面）。
此提示词为固定模板，每次逐字原样输出以下 6 条，不得改写：

1. 项目名（rdkx5、x5_evb、S100 还是 S600？）
2. 项目根目录绝对路径
3. 新 sensor 文档路径
4. camera 类型（direct mipi camera 还是 serdes camera）
5. camera 接入位置（按第4条类型二选一，参考示例格式）：
   - direct mipi camera：mipi_index=0
   - serdes camera：mipi_index=0, link_index=A
6. 板端 IP 地址

禁止从目录、文件或上下文中猜测或推断这些信息，必须由用户明确提供。
只有用户回答后才能继续，在此之前不做任何其他操作。

用户回答后检查以下项目：

7. 用户必须指定项目名，未指定则向用户确认。
8. 读取项目配置：按用户回答的项目名匹配 `project_info/` 下的 conf（忽略大小写）。
   - 唯一匹配（如 x5_evb_project.conf、s600_project.conf、rdkx5_project.conf）→ 直接读该 conf。
   - 多个匹配（如 S100 对应 s100_6v / s100_12v_project.conf）→ 停下追问用户选哪个，列出候选 conf 及其板型含义（取自各 conf 顶部注释），选定后再读；不得自行猜测。仅实际多匹配时触发，不预设。
9. 获取用户指定的项目根目录绝对路径。
10. 将项目根目录与第 8 步匹配到的 `*_project.conf` 中的相对路径拼接，得到各仓库的绝对路径。
11. **加载嵌入式通用规则**：读取 `embedded_common/embedded_rulers.md` 全文作为本次调试的背景约束，全程适用。未读此文件不得进入后面步骤。

### 1. 提取参数

读取新 sensor 文档，提取关键参数表（I2C 地址、分辨率、格式、lane 数、时钟等）。按以下顺序执行，不得跳步：

1. **类型校验**：camera 类型由用户在入口指定，无需从文档判断；但须按 `code_ruler/patterns_<类型>.md`「参数提取」节首条校验文档内容是否与指定类型相符，不符则停下询问用户，不得自动改类型。
2. **读规律章节**：读 `code_ruler/patterns_serdes.md` §0.2「待提取参数」作为后续提取与判定的依据。
3. **逐参数提取**：逐参数提取，生成参数清单。以 patterns「待提取参数」清单（SerDes §0.2.2 / MIPI §0.6）为封闭白名单，逐个参数从 sensor 文档取值并标注其在文档中的来源位置（如「第 3 页表 2」），逐字摘录规律原文（禁止转述，转述=未回查）锚定取值，清单必须含待提取参数、取值、来源、每个参数的确认判据。提取每个参数时都要遵守以下判定规则：
   - 参数不在白名单 → 不从文档提取，不进入参数清单。
   - 参数在白名单但规律已给强制取值/动作条款（「必须/须/直接/不得/每次/都必须」措辞，或「确认判据」行写「不确认」）→ 直接按条款填值，标注于参数清单，不进最终确认清单。
   - **参数清单入口闸门**：输出参数清单前逐参数核对四点——白名单内/有取值/有来源/逐字摘录判据原文；缺一即违规补全再输出。白名单内所有参数须逐个列入，判据写「必问」的不论文档有无信号都须列，不得用汇总表替代。
4. **出最终确认清单**：必须逐个检查参数的确认判据，才能进入确认清单，提供给用户确认；本规则同样覆盖第 2 步 diff、第 5 步修复。向用户提出的每一条确认，须是白名单内某参数的「确认判据」明写需确认、且文档确无该信息；否则不问。
   - 必须严格根据参数清单中各参数的确认判据判断：不确认的禁止放入确认清单。
   - 清单格式：多个待确认参数用 `1. 2. 3. ...` 主序号并列；单个参数内有多项需确认时用 `(1) (2) (3)` 子序号分行列出。每条结构 = 参数名 + 当前情况陈述（据本次文档/参数清单如实写，不得照抄他例）+ 末尾「是否…？…还是…？」是非/分支问句；分支处置合并为一条，不拆多条，条数不膨胀。
   - **简洁易懂呈现要求（强制）**：确认清单须简洁易懂，只让用户做决策，不堆砌推理过程。
   - 骨架（仅示意结构，尖括号处填本次真实值，禁止照抄示例内容）：
     1. <参数名>：<本次该参数的情况陈述>。<是否[选项A]？还是[选项B]？>
     2. <参数名>：<本次该参数的情况陈述>。请确认：
        (1) <子问题1，含本次实际情况>
        (2) <子问题2，含本次实际情况>
        (3) <子问题3，含本次实际情况>

参数提取阶段禁止参考已有代码，唯一依据是当前 sensor 文档 + patterns 提取规律；凡参数提取阶段基于已有代码提出的异议、疑问一律禁止。只能输出文档中明确写出的参数值，禁止编造、猜测或填充默认值。

### 2. 生成代码变更

按 sensor 类型读取对应规律文件作为生成依据，并据此生成代码变更：

- SerDes Camera → 读取 `code_ruler/patterns_serdes.md`
- Direct MIPI Camera → 读取 `code_ruler/patterns_mipi.md`

生成驱动代码的依据是 `patterns_<类型>.md` 的代码模板 + 当前 sensor 手册。当前项目 conf 含 `isp_test_dir` 时，tuning JSON 另以 `code_ruler/isp_pipeline_tuning.md` 为依据。除此之外一律不作数。按以下顺序完成（缺一不可）：

1. **探测驱动库是否已存在**：在项目源码中检索该 sensor 是否已有驱动库（按规律文件给出的驱动库文件命名/路径特征检索）。本步直接判定，不询问用户：
   - 已存在该 sensor 的驱动库 → 往现有驱动中添加新模组枚举/emode 条目（参考 SerDes §12 / §13 的「添加」位置），不要再询问用户确认，不要新建整库
   - 不存在 → 按规律文件的「新建」路径整库新建（MIPI §1 / SerDes §17）

   **读驱动的边界**：读目标 sensor 自身驱动只许用来确认库已存在、复用其既有寄存器序列（init/stream 等配置）；不得读取兄弟 sensor（不论同系列）的 .c/.h 驱动作取值来源。确认框架 API 调用形式（函数名/参数顺序/结构体字段）时可查 `libcam/src/inc/` 下的 .h，但仍不得复制数值。
2. **按新 sensor 参数判定分支**：根据第 1 步提取的参数（格式类型、lane 数、分辨率+fps 组合、厂商等），在规律文件中定位需套用的章节与模板分支（SerDes 尤需跨章圈定：§12/§13 加枚举、§15 vp_sensor 配置、§16 注册、§17 驱动结构；MIPI 按 §2/§3 文件流水线）。判定分支前不得动手填任何模板。
3. **逐项填模板**：将新 sensor 参数逐项填入上一步圈定的各文件修改模板，生成具体代码变更。填模板时遵守：
   - **已定值即冻结**：第 1 步参数清单中已定取值的参数（含规律强制取值、确认判据为「不确认」直接填值的），本步取值冻结，只填模板不问不疑。驱动既有实现里的分支/功能位、兄弟 sensor 写法、文档措辞的字面贴近、模板省略号旁看似更贴切的写法，都不得构成重新询问、让用户二选一或推翻的理由；「稳妥起见」不构成询问理由，模板已写明却仍问 = 违规。驱动里出现而 patterns 模板没列的分支/功能位（如 1024）是历史遗留，一律忽略，按第 1 步值填。仅当第 1 步取值本身违反提取规律时才停下，且汇报「第 1 步取错了」，而非「要不要换一个值」。
   - **唯一允许问用户的情形**：该参数在第 1 步没取到值，且 patterns 模板也未写明取值——此时按第 1 步第 4 条规则生成确认清单。
   - **二阶段确认禁令**：本阶段绝对禁止向用户确认「提取参数」阶段已闭环/已呈现确认的参数（含 gain_lut 形态）。
4. **生成 ISP 建链 tuning**：仅当当前项目 conf 含 `isp_test_dir`。读取 `code_ruler/isp_pipeline_tuning.md` 并按其生成 `<sensor>_tuning.json`，同时把本次 `camera_config_t.calib_lname` 设为 `"<sensor>_tuning.json"`。conf 不含 `isp_test_dir` 时不生成该文件，`calib_lname` 按 patterns 原文。

文件路径 = 项目根目录 + `project_info/<项目名>_project.conf` 中的相对路径 + 具体文件路径。填完后输出新 sensor 在 `vp_sensor_config_list` 中的序号（camera_index），供后续测试使用。

### 3. 编译推送安装

读取 `project_info/<项目名>_project.conf` 中的 build/deploy/install 命令，依次执行。所有配置在该 conf 中的仓库都必须执行 deploy 和 install，不论本次是否改动其代码，以保证板端环境完整。

执行 deploy/install/test 前先 ping 测试 board_ip 是否可达：

- 可达 → 正常执行
- 不可达 → 直接用文字询问用户输入正确的 IP，更新本次执行的 IP，不影响配置文件

登录板端时使用该 conf 中的 `board_user` 与 `board_password`。

本步及第 4 步均为执行性操作，连贯执行，不停顿等待确认。只在以下两类情况停下询问用户：

1. 报错：build/deploy/install 任一步返回非零退出码或输出明显错误，暂停并汇报错误，等待用户处理
2. 需要用户拍板：遇到规律/参数无法确定、或发现与预期不符需决策的情况（如配置位置不确定、需确认兜底值），停下询问

正常完成时不必逐步询问「是否继续」，直接进入下一步。

当前项目 conf 含 `isp_test_dir` 时，安装完成后检查板端 `isp_tuning_board`（`{sensor}` 换成 `camera_config.name`）。文件不存在则把源码中的 `<sensor>_tuning.json` 拷到该路径，权限 `0644`。源码 JSON 不存在则回到第 2 步第 4 条生成，不得跳过 ISP。不得把本次 IP 写回配置文件。

### 4. 验证测试

分两段。当前项目 conf 含 `isp_test_dir` 时，RAW 与 ISP 都通过才算本次验证通过。不含 `isp_test_dir` 时只做 RAW，做完告知用户该板未配置 ISP 测试，不得猜测 `get_isp_data` 的路径。

#### 4.1 RAW（get_vin_data）

ssh 登录板端，进入 test_dir，按顺序执行 test_clean、test_build、test_prepare 中的全部指令、test_cmd。若 conf 含 `test_cmd_mipi` / `test_cmd_serdes`，按入口 camera 类型选取对应命令；否则使用 `test_cmd`。占位符按 conf 中注释规则替换，执行前检查不得残留 `{...}` 占位符。四步按配置逐一执行；conf 未提供 test_build 时跳过编译，不自行补命令。

**test_cmd 形式禁令**：test_cmd 仅替换占位符，其余原样执行；禁止删改 stdin 喂入（如 `printf 'l\nq\n' |`），禁止与 dmesg/logcat 合并进同一命令。查日志在 test_cmd 跑完后单独执行。

**测试等待时长**：test_cmd 执行后等待 10 秒，10 秒内未自行退出 → kill 掉测试进程，判定 RAW 失败，进入第 5 步。RAW 失败不得开始 ISP。正常退出本身不代表 RAW 成功，须同时满足下列验收条件。RAW 成功后：conf 含 `isp_test_dir` 则继续第 4.2 节；不含则告知 RAW 已通过、本板未配置 ISP 测试，然后停止。

**RAW 成功验收（全部满足）**：

1. 测试前记录运行起始时间及输出文件清单；将旧帧文件移到独立备份目录或使用可核对的本次新文件，禁止用旧输出验收。
2. 测试正常退出，日志无采集错误，并有本次成功获取和保存帧的记录。快速退出但没有有效帧，仍判失败。
3. 本次帧文件存在且非空；采集日志中的分辨率、格式与当前配置一致。按实际 stride、packing、plane 布局核验文件大小，不统一套用 width × height × bitwidth / 8。无法确定布局时报告证据不足，不宣告成功。
4. 连续采集时核对成功保存的帧数与测试程序该操作的预期帧数一致，并核对帧号或时间戳推进。预期帧数须来自当前测试程序说明或实现，不猜测。

任一验收条件不满足即 RAW 失败，记录日志和文件证据后进入第 5 步，不进入 ISP；证据不足时先补齐证据。最终报告包含本次文件、帧数、分辨率、格式及大小核验结果。

#### 4.2 ISP（get_isp_data）

仅当 conf 含 `isp_test_dir`。进入 isp_test_dir，按顺序执行 isp_test_clean、isp_test_build、isp_test_prepare、isp_test_cmd。占位符规则与 test_cmd 相同。

**isp_test_cmd 形式禁令**：仅替换占位符，其余原样执行；禁止删改 stdin 喂入（如 `printf 'g\nq\n' |`），禁止与 dmesg/logcat 合并进同一命令。查日志在 isp_test_cmd 跑完后单独执行。

**测试等待时长**：等待 conf 中的 `isp_test_wait_sec` 秒（未写则 30 秒）。时限内进程自行退出后再判定；超时则 kill 掉测试进程，判定 ISP 失败，进入第 5 步。

成功须同时满足以下三条，缺一条即 ISP 失败：

1. 打印含 `isp dump yuv {width}x{height}`，宽高为参数清单已定的 width、height。
2. 生成的 yuv 文件大小等于 `width × height × 3 / 2`。
3. dmesg 或 logcat 中 `sensor_cali_name` 等于 `<sensor>_tuning.json`。

三条都满足则告知用户 RAW 与 ISP 都已通过并停止。该 tuning 只用于建链，BLS、AWB、LSC、AEC 仍是模板数据，不能当作最终画质版本。

### 5. 问题修复

先区分失败段。

- **RAW 失败**（第 4.1 节）：按下面的 experience 流程排查。
- **ISP 失败**（第 4.2 节）：只读 `code_ruler/isp_pipeline_tuning.md` 的「ISP 失败时的检查项」，按其中的检查项名排查。不得改 BLS、AWB、LSC、AEC。三项都与期望一致而测试仍失败时，结论为经验未覆盖，停下问用户。

RAW 失败时，先从 3 种日志来源（测试打印、logcat、dmesg）分析出具体的异常点，然后到对应的 experience 文件中匹配触发特征进入入口检查项，按检查项的合法去向逐步排查、按到达的修复点修改。不允许盲目分析问题原因，不允许跳过，不允许自创排查路线或忽略。ISP 失败段不读 experience 文件。

排查必须分阶段执行，检查与修改严格分离：

1. **检查阶段**：只做检查，只汇报检查结果（实际值 vs 期望值 / 通或不通），此阶段严禁提出任何修改。检查阶段最高频违规：因一次测量读到的寄存器值含其他字段，就擅自把排查对象从当前检查项换成「那个看似更可疑的字段」。严禁。检查项的对象由 experience 流程固定，测量值只填「实际值」，不改对象；「我觉得别的字段更像根因」不是换方向的理由——按合法去向走，或填「经验未覆盖」停下问用户。
2. **匹配阶段**：基于检查项的汇报结论，按合法去向跳到对应的下一检查项或修复点。
3. **修改阶段**：提出修改前，必须标注出处——RAW 失败标 experience 文件中的检查项名，ISP 失败标 `isp_pipeline_tuning.md` 中的检查项名。标注不出来则属于自创路线，不得提出。

排查中一旦出现「可能/推测/也许/我觉得」等措辞，立即停下来，RAW 失败退回 experience、ISP 失败退回 `isp_pipeline_tuning.md` 按合法去向走，找不到就不继续。

根据第 1 步判断的 sensor 类型查询对应经验文件：

- SerDes Camera → `experience/sensor-debug-experience-serdes.md`
- Direct MIPI Camera → `experience/sensor-debug-experience-mipi.md`

给出修复代码，重新编译推送安装测试。RAW 失败修复后从第 4.1 节重新验证。ISP 失败修复后从第 4.2 节重新验证；若修复改了驱动或 tuning 的加载路径，则从第 4.1 节重新验证。循环执行第 4、第 5 步，直到当前项目要求的验证段都通过。

## Safety

- 6 条入口信息未由用户明确提供之前，不读项目、不改代码、不编译、不推板。
- 排查项目源码时禁止从项目根全局扫描。禁止读取 `out/deploy`、`out/...`、`prebuilts/` 等构建产物 / 预编译二进制目录。这些不是源码，会污染判断（如把 .so 产物误当成已有驱动）。
- 调试与排查时禁止查询项目 git 历史：不得执行 `git log`、`git show`、`git blame`、`git diff <commit>`、`git log -p` 等任何读取历史 commit 的命令，也不得通过其它方式检索历史提交信息。规律文件的条款是当前生效规则，以规律文件原文为准，不得用「历史 commit 曾经怎么写」来佐证、推翻或绕过现行规律。规律文件中亦不再保留任何 commit hash / sensor 名 / 出处图片等来源标注。
- 参数值只取 sensor 文档和 patterns 中写明的内容。禁止编造、猜测或填充默认值。
- build、deploy、install 或测试返回非零退出码或明显错误时停下，向用户汇报，等待处理。不要自行换 IP 以外的配置项，也不要把本次 IP 写回配置文件。
- 检查阶段只汇报实测值，不提出修改。RAW 修复必须标出 experience 文件中的检查项名。ISP 修复必须标出 `isp_pipeline_tuning.md` 中的检查项名。

> Sources: `code_ruler/patterns_serdes.md`、`code_ruler/patterns_mipi.md`、`code_ruler/isp_pipeline_tuning.md`、`experience/sensor-debug-experience-serdes.md`、`experience/sensor-debug-experience-mipi.md`、`project_info/*_project.conf`、`board_info/*_board.md`、`embedded_common/embedded_rulers.md`。寄存器手册留在使用者本机，经 knowledge-rag 检索，不随本 skill 发布。
