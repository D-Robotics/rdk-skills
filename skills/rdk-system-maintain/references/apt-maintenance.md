# APT Maintenance — 官方出处

本文件记录 rdk-system-maintain 技能所依据的官方文档路径与关键事实。
所有事实均来自本仓库 `.refs/` 下的官方文档克隆，不做二次推断。

## apt 源修复（FAQ Q10）

- DocScope: `rdk_x_doc/docs/08_FAQ/01_hardware_and_system.md`
  （"Q10: `apt update` 命令执行失败或报错如何处理？"）
- 源文件：`/etc/apt/sources.list.d/sunrise.list`
- 正确的源行（按板卡）：

```text
deb [signed-by=/usr/share/keyrings/sunrise.gpg] http://archive.d-robotics.cc/ubuntu-rdk-s100 jammy main   #RDK S100
deb [signed-by=/usr/share/keyrings/sunrise.gpg] http://archive.d-robotics.cc/ubuntu-rdk-x5 jammy universe #RDK X5
deb [signed-by=/usr/share/keyrings/sunrise.gpg] http://archive.d-robotics.cc/ubuntu-rdk jammy universe    #RDK X3
```

- 过期域名迁移（官方命令）：

```bash
sudo sed -i 's/archive.sunrisepi.tech/archive.d-robotics.cc/g' /etc/apt/sources.list.d/sunrise.list
sudo sed -i 's/ubuntu-rdk-s100-beta/ubuntu-rdk-s100/g' /etc/apt/sources.list.d/sunrise.list
```

- GPG key（官方命令）：

```bash
sudo wget -O /usr/share/keyrings/sunrise.gpg http://archive.d-robotics.cc/keys/sunrise.gpg
```

- 已知过期域名：`archive.sunrisepi.tech`、`sunrise.horizon.cc`；
  过期仓库名：`ubuntu-rdk-s100-beta`。

## apt 锁（FAQ 同章节）

- 报错样式：`Could not get lock /var/lib/apt/lists/lock. It is held by process XXXX`
- 官方处理顺序：等待后台更新结束 → 重启 → 确认无 apt/dpkg 进程后清理锁文件
  （官方标注 ⚠️ 谨慎操作，有破坏包管理系统的风险）。

## 系统版本升级约束

- DocScope: `rdk_x_doc/docs/08_FAQ/01_hardware_and_system.md`（"版本升级"条目）
- 官方约束：1.x 版本系统**无法**通过 `apt` 直接升级到 2.x 或更新版本，
  必须通过烧录新版本系统镜像重新安装。
- Release Note：`rdk_x_doc/docs/10_Release_Note/`。

## 文件系统扩容

- DocScope: `rdk_x_doc/docs/02_System_configuration/02_srpi-config.md`
  （Advanced Options → Expand Filesystem）
- 用途：TF 卡从已初始化系统复制而来时容量未自动扩展，用此功能扩满整卡。
