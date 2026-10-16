# Skill Card: cmos-sensor-bringup

| Field | Value |
|---|---|
| name | cmos-sensor-bringup |
| owner | sensor adapter workflow |
| license | Apache-2.0（代码）；CC-BY-4.0（文档），遵循仓库许可证规则 |
| kind | workflow |
| riskLevel | high — 会修改项目源码，并编译、scp/ssh 到板端安装和测试 |
| platforms | rdkx5、x5_evb、S100（6v/12v）、S600 |

## Use case

用户要调试一颗新的 SerDes camera 或 direct MIPI camera，从收集项目信息到板端验证。rdkx5 在 RAW 通过后继续跑 get_isp_data；tuning 只保证建链。

## Known risks

- 入口 6 条未齐就改代码或推板，会改错仓库或打到错误板子。
- S100 对应两份 conf（s100_6v / s100_12v）。未让用户选定就读取，会用错板型。
- 参数不在 sensor 文档或 patterns 白名单内时填默认值，会把错误寄存器配置写进驱动。
- 扫描 `out/`、`prebuilts/` 会把构建产物当成已有驱动。
- 验证失败后不按 experience 的检查项走，会改到与故障无关的寄存器。
- 只改 tuning 里的分辨率字符串、漏掉数值窗口，ISP 仍按模板分辨率建链。
- 把 dummy 的 BLS/AWB/LSC/AEC 当成最终画质参数。
- 在未配置 `isp_test_dir` 的板上猜测 `get_isp_data` 路径。
- 模组自带 24MHz 时仍改 `x5-rdk.dtsi` 或打开 `snrclk_en`，会切走板载晶振。

## Sources

- `code_ruler/patterns_serdes.md`
- `code_ruler/patterns_mipi.md`
- `code_ruler/isp_pipeline_tuning.md`
- `experience/sensor-debug-experience-serdes.md`
- `experience/sensor-debug-experience-mipi.md`
- `project_info/*_project.conf`
- `board_info/*_board.md`
- `embedded_common/embedded_rulers.md`
