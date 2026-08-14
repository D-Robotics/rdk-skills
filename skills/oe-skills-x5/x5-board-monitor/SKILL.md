---
name: x5-board-monitor
description: 采集并解析 X5 hrut_somstatus、温度、CPU/BPU/DDR/GPU 频率、BPU ratio 和 dmesg 证据；当需要建立板端资源快照或关联性能异常时使用。默认只读和有界采样，不调频、不清日志、不循环到手工终止。
---

# X5 板端监控

## 目标与边界

获得可与推理窗口对齐的板端资源证据。手册规定 X5 使用 `hrut_somstatus` 查看 BPU 使用率；不要套用 S 系列 UCP 监控工具。

## 输入合同

- X5 板卡标识、采样窗口和推理开始/结束时间。
- `hrut_somstatus` 输出文件；可选 `uname -a`、`/etc/version` 和 `dmesg` 片段。

## 前置检查

- 只读命令可用，板卡确认为 X5。
- 采样次数和间隔有上限；监控开销被记录。

## 执行步骤

1. 推理前保存版本、温度、频率和空闲基线。
2. 在固定窗口采集有限次 `hrut_somstatus` 输出，不修改 governor/频率。
3. 推理失败或进程被 killed 时读取相关 `dmesg`，不清空系统日志。
4. 解析：

~~~bash
python .drobotics/platforms/x5/scripts/parse_somstatus.py \
  --input <somstatus.txt> --output <board-resource.json>
~~~

## 产物与完成标准

- 原始输出、`board-resource.json`、采样时间和推理窗口对应关系。
- 温度、当前/最大频率和 BPU ratio 可机器读取。
- 缺失字段被标为不可用，不填造默认值。

## 风险与确认

只读有界采样为低风险。调频、修改电源策略、清日志或停止进程不属于本 Skill，必须另行高风险确认。

## 失败与交接

解析失败时保留原始输出并更新解析器 fixture；资源异常交接 `x5-performance-diagnostics`。

## 按需参考

- `_sources/runtime/source/tool_introduction/auxiliary_tool.rst.txt`
