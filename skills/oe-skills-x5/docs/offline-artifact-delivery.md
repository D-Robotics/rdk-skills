# 固定版本离线交付与 Docker 获取

本 Pack 为已启用的平台维护**版本固定**的 SDK、文档、离线 Docker 镜像和在线 Docker 镜像引用。唯一机器可读来源是 `.drobotics/release-artifacts.json`；可用 `.drobotics/scripts/release_artifacts.py` 只生成命令，不会自动下载大文件、执行 Docker 或读取凭据。

## 安全与完整性

- Registry 凭据必须通过受管 Secret、终端环境变量或交互式输入提供；不得写入 Skill、Pack、脚本、`AGENTS.md`、命令历史、任务记录或源代码。
- 在线 Registry 登录使用 `--password-stdin`。不得通过命令行的 `-p` 或 `--password` 选项传入密码，也不要在终端命令行中直接粘贴密码。
- 当前清单未附带供应方 SHA-256。下载后可生成 `SHA256SUMS.local` 用于内部缓存防篡改；在把文件提升为可信离线镜像库前，仍应从发布方取得并核验官方 SHA-256。
- 不能混用 X5 `1.2.8` 与 S 系列 `3.7.0` 的 SDK、文档、Docker 镜像或离线包。

## 命令生成

先仅查看本次固定发布物：

~~~bash
python .drobotics/scripts/release_artifacts.py --release x5-1.2.8 --mode list
python .drobotics/scripts/release_artifacts.py --release s-3.7.0 --mode list
~~~

生成公共文件的可审阅 `wget` 命令，再由用户确认后执行：

~~~bash
python .drobotics/scripts/release_artifacts.py --release x5-1.2.8 --mode wget --output-dir <cache-dir>
python .drobotics/scripts/release_artifacts.py --release s-3.7.0 --mode wget --output-dir <cache-dir>
~~~

离线 Docker 镜像下载完成后，生成 `docker load` 命令：

~~~bash
python .drobotics/scripts/release_artifacts.py --release x5-1.2.8 --mode docker-load --output-dir <cache-dir>
python .drobotics/scripts/release_artifacts.py --release s-3.7.0 --mode docker-load --output-dir <cache-dir>
~~~

在线 Docker 拉取会只输出安全的 `--password-stdin` 登录和 `docker pull` 命令。先通过受管秘密注入环境变量，再复制输出命令执行：

~~~bash
export DROBOTICS_REGISTRY_USERNAME='<read-only-registry-user>'
export DROBOTICS_REGISTRY_PASSWORD='<retrieve-from-secret-manager>'
python .drobotics/scripts/release_artifacts.py --release x5-1.2.8 --mode docker-pull
~~~

## X5：OE Mapper 1.2.8 / Python 3.10

| 交付物 | 文件名 / 镜像 | 固定地址 |
| --- | --- | --- |
| SDK | `horizon_x5_open_explorer_v1.2.8-py310_20240926.tar.gz` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/horizon_x5_open_explorer_v1.2.8-py310_20240926.tar.gz` |
| 中文文档 | `x5_doc-v1.2.8-py310-cn.zip` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/x5_doc-v1.2.8-py310-cn.zip` |
| 英文文档 | `x5_doc-v1.2.8-py310-en.zip` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/x5_doc-v1.2.8-py310-en.zip` |
| CPU 离线 Docker | `docker_openexplorer_ubuntu_20_x5_cpu_v1.2.8.tar.gz` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/docker_openexplorer_ubuntu_20_x5_cpu_v1.2.8.tar.gz` |
| GPU 离线 Docker | `docker_openexplorer_ubuntu_20_x5_gpu_v1.2.8.tar.gz` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/docker_openexplorer_ubuntu_20_x5_gpu_v1.2.8.tar.gz` |
| 中文发布说明 | `release_note_CN.txt` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe_x5/1.2.8/release_note_CN.txt` |

在线 Registry 镜像：

- `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_cpu:v1.2.8`
- `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_20_x5_gpu:v1.2.8`

## S：OpenExplorer 3.7.0 / S100、S100P、S600

| 交付物 | 文件名 / 镜像 | 固定地址 |
| --- | --- | --- |
| SDK | `oe-package-3.7.0-s100-s600.tgz` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe/3.7.0/oe-package-3.7.0-s100-s600.tgz` |
| 中文用户手册 | `oe-doc-3.7.0-s100-s600.zip` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe/3.7.0/oe-doc-3.7.0-s100-s600.zip` |
| CPU 离线 Docker | `ai_toolchain_ubuntu_22_s100_s600_cpu_v3.7.0.tar` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe/3.7.0/ai_toolchain_ubuntu_22_s100_s600_cpu_v3.7.0.tar` |
| GPU 离线 Docker | `ai_toolchain_ubuntu_22_s100_s600_gpu_v3.7.0.tar` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe/3.7.0/ai_toolchain_ubuntu_22_s100_s600_gpu_v3.7.0.tar` |
| S100 DSP UCP 教程包 | `ucp_tutorial_3.13.6_dsp_on_s100.zip` | `https://d-robotics-aitoolchain.oss-cn-beijing.aliyuncs.com/oe/3.7.0/ucp_tutorial_3.13.6_dsp_on_s100.zip` |

在线 Registry 镜像：

- `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_cpu:v3.7.0`
- `registry.d-robotics.cc/deliver/ai_toolchain_ubuntu_22_s100_s600_gpu:v3.7.0`

## 离线缓存交接标准

1. 按平台与版本分目录保存，例如 `<cache>/x5-1.2.8/`、`<cache>/s-3.7.0/`；不要把两个发布物混放。
2. 保存原始文件名、下载 URL、下载日期、文件大小、内部 SHA-256 与适用平台；没有官方校验值时明确标记为“仅内部缓存校验”。
3. 对 Docker 离线包执行 `docker load -i <file>` 后，记录 `docker image inspect` 的镜像 ID 和标签，再导出给离线网络使用。
4. 下载、`docker load`、`docker pull` 和镜像导出可能消耗大量带宽/磁盘或改变本地 Docker 状态，执行前必须获得用户明确确认。