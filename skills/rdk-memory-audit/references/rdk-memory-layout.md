# RDK 内存构成参考（DRAM / ION / CMA）

> 信息来源（官方文档）：
> - `rdk_x_doc/docs/09_Appendix/rdk-command-manual/cmd_rdkos_info.md`
> - `rdk_x_doc/docs/08_FAQ/01_hardware_and_system.md`

## rdkos_info 的内存报告

官方一站式信息命令 `sudo rdkos_info` 会同时报告系统内存与 ION 内存，例如：

```
[Total Memory]:         1.9Gi
[Used Memory]:          644Mi
[Free Memory]:          986Mi
[ION Memory Size]:      672MB
```

- **ION Memory** 是 RDK 上为多媒体（VIO/编解码）和 BPU 模型预留的连续物理内存池，
  从系统总内存中划出。`free` 看到的 Total 小于板载物理内存属于正常现象。
- ION 池大小可通过官方 FAQ 描述的方式调整（X3 上默认约 672MB；不同镜像版本有差异，
  以 `rdkos_info` 实测为准）。

## 与 /proc/meminfo 字段的对应

| 关注点 | 数据源 | 说明 |
| --- | --- | --- |
| 可用内存 | `MemAvailable` | 判断"还能跑多大的程序"的首选字段 |
| 页缓存 | `Cached` / `Buffers` | drop_caches 能回收的主要部分 |
| CMA | `CmaTotal` / `CmaFree` | 连续内存分配器；部分内核版本不暴露 |
| ION | `sudo rdkos_info` 输出 | meminfo 中无直接对应字段 |

## 审计要点

- drop_caches 回收的是 page cache，**回收不了** ION/CMA 中被驱动持有的内存。
- 模型加载失败报 `ion alloc failed` 时，方向是减小模型/关闭占用 ION 的进程或调大 ION
  池，而不是 drop_caches。
- 一切"回收了多少"的结论必须来自 audit.sh 的 before/after 差值。
