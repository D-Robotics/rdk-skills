# hrt_model_exec 工具参考

> 信息来源（官方文档）：
> - `rdk_x_doc/docs/07_Advanced_development/04_toolchain_development/intermediate/ptq_process.md`
> - `rdk_x_doc/docs/07_Advanced_development/04_toolchain_development/intermediate/runtime_sample.md`

`hrt_model_exec` 是官方板端模型工具，可评测 `.bin` 定点模型的推理性能并查看模型信息。
**在开发板上执行**，模型建议放在 `/userdata` 目录。

## perf 子命令（官方参数定义）

```bash
./hrt_model_exec perf --model_file mobilenetv1_224x224_nv12.bin \
                      --model_name="" \
                      --core_id=0 \
                      --frame_count=200 \
                      --perf_time=0 \
                      --thread_num=1 \
                      --profile_path="."
```

| 参数 | 默认值 | 含义（官方定义） |
| --- | --- | --- |
| `model_file` | — | 待评测的 bin 模型 |
| `model_name` | — | bin 内含多个模型时指定；单模型可省略 |
| `core_id` | 0 | `0` 任意核心，`1` 核心 0，`2` 核心 1；测双核极限帧率设 `0` |
| `frame_count` | 200 | 推理帧数，`perf_time=0` 时生效 |
| `perf_time` | 0 | 推理时长（分钟），非 0 时按时间评测 |
| `thread_num` | 1 | 线程数，取值范围 [1,8]；测极限帧率时调大并寻优 |
| `profile_path` | 关闭 | 生成 profiler.log / profiler.csv 的目录 |

## 典型输出（官方 RDK X3 实测示例）

```
Running condition:
  Thread number is: 1
  Frame count   is: 200
  core number   is: 1
  Program run time: 818.985000 ms
Perf result:
  Frame totally latency is: 800.621155 ms
  Average    latency    is: 4.003106 ms
  Frame      rate       is: 244.204717 FPS
```

- `Average latency`：平均单帧推理延时。
- `Frame rate`：模型极限帧率；官方提示通过调节 `thread_num` 寻找最优线程数。

## model_info 子命令

```bash
hrt_model_exec model_info --model_file=xxx.bin        # 单模型
hrt_model_exec model_info --model_file=xxx.bin,xxx.bin # 多模型
```

输出模型输入/输出张量的 shape、类型与量化信息。

## 性能瓶颈定位（官方建议）

若 `perf` 评估确认瓶颈是 CPU 算子，查阅官方**模型算子支持列表**确认该算子是否具备
BPU 支持能力，再回到工具链侧优化模型。
