---
name: rdk-board-knowledge
description: Identify which RDK board you're on, confirm its runtime baseline (SoC/OS/TROS — BPU TOPS facts belong to rdk-hardware), diagnose the common on-board errors (camera, model/BPU, TROS/ROS2, APT/pubkey, GPIO/I2C/serial, power, network), correct the high-frequency user misconceptions, and flash the S-series (S100/S100P/S600) via xburn DFU/Fastboot. Use this WHENEVER a user pastes an error/log, asks "which board is this / 是哪块板", reports something broken on the board, asks an official-FAQ-style question, or needs to flash an S-series image — don't wait for them to name the exact subsystem. 触发词:报错、排查、诊断、卡死、连不上、识别板型、确认板子、是哪块板、板型基线、系统版本、摄像头没画面、模型跑不了、ros2 command not found、NO_PUBKEY、GPIO 权限、供电不足、under-voltage、xburn、烧录、刷机、进下载模式、DFU、Fastboot、变砖、S100/S600 烧录、官方 FAQ、默认账户密码。Routing — pure pin/connector/spec facts → rdk-hardware; full self-trained model deployment loop (hb_mapper/hb_compile) → rdk-device; peripheral driver cookbooks → rdk-peripheral-cookbook; product selection/comparison → rdk-ecosystem; exact latest doc URL → rdk-doc-finder.
trigger: 报错, 排查, 诊断, 卡死, 连不上, 识别板型, 确认板子, 是哪块板, 板型基线, 系统版本, 摄像头没画面, 模型跑不了, ros2 command not found, NO_PUBKEY, GPIO权限, 供电不足, under-voltage, xburn, 烧录, 刷机, 进下载模式, DFU, Fastboot, 变砖, S100烧录, S600烧录, 官方FAQ, 默认账户密码
---

# RDK Board Baseline & Failure Diagnosis

Before answering any RDK problem, **confirm the board from on-board facts, not from the user's words.** The board determines every downstream answer — package names, TROS path, toolchain, camera node, default IP. Guessing the board (e.g. assuming X5) is the single most common way these answers go wrong.

> Sources: official D-Robotics docs `rdk_doc` / `rdk_x_doc` / `rdk_s_doc` (08_FAQ + 01_Quick_start/install_os), the OpenExplorer / 天工开物 (TianGong) toolchains, and reproduced community cases. Facts are carried over with provenance; nothing is invented.

## The one move that matters most

**Run a read-only identity probe first.** Never flash, upgrade, or drive GPIO before you know the board:

```bash
cat /sys/class/socinfo/board_id     # X5 / S-series read this (srpi-config, hobot_mipi_cam use it)
cat /sys/class/socinfo/som_name     # X3 docs use som_name; pick one per board
cat /proc/device-tree/model         # literal model string; fallback /etc/board_config.json
cat /etc/version                     # OS/RDK image version (2.1.0+ also has `rdkos_info`)
```

If the output doesn't map cleanly to X3/X5/Ultra/S100/S100P/S600, **ask for more logs — do not assume X5.**

## Board baseline cheat-sheet

| Board | BPU arch | OS / TROS | Default IP (wired) | Power | Flash method |
|-------|----------|-----------|--------------------|-------|--------------|
| RDK X3 | Bernoulli2 (`bernoulli2`) | Ubuntu 20.04/22.04, Humble (`/opt/tros/humble`) | 2.1.0+ `192.168.127.10` (≤2.0.0 `192.168.1.10`) | Type-C 5V/3A+ | SD card (balenaEtcher / official flasher) |
| RDK X5 | Bayes-e (`bayes-e`) | Ubuntu 22.04, Humble | wired `192.168.127.10`, USB-net `192.168.128.10` | 5V/5A | SD card |
| RDK Ultra | Bayes (`bayes`) | Ubuntu 20.04, Foxy/Humble | DHCP | 12V/5A DC | SD card |
| RDK S100 | Nash-e (`nash-e`) | Ubuntu 22.04, Humble (`tros-humble`) | **eth1 fixed `192.168.127.10`**, eth0 DHCP | 12–20V (typ. 12V/5.5A ~70W) | **xburn** (media `emmc`) |
| RDK S100P | Nash-m (`nash-m`) | Ubuntu 22.04, Humble | eth1 fixed `192.168.127.10` | 12–20V | **xburn** (media `emmc`) |
| RDK S600 | Nash (`nash-p`) | **Ubuntu 24.04, Jazzy (`/opt/tros/jazzy`, `tros-jazzy`)** | eth1 fixed `192.168.127.10` | **12–28V** (adapter 24V/8A) | **xburn** (media `ufs`) |

> BPU march is the `hb_compile --march` / `hb_mapper` arch flag. **`bayes` (Ultra) ≠ `bayes-e` (X5)** and **`nash-e`/`nash-m`/`nash-p` (S100/S100P/S600)** are all distinct — artifacts never interchange across marches. Board runtime: X3/Ultra `hobot_dnn`; X5 `hbm_runtime` (RDK OS 3.5.0+) or `pyeasy_dnn`; S-series `hbm_runtime`.

**Default login on every RDK image: both `sunrise/sunrise` (normal) AND `root/root` (super).** Desktop autologin uses `sunrise`; RDK Studio's SSH channel often uses `root`. (FAQ "默认登录账户" Q.)

X-series produce `.bin`; S-series produce `.hbm`. Cross-architecture artifacts are **never** interchangeable. Toolchain (`hb_mapper` for X, `hb_compile` for S) runs on an **x86 Docker host**, never on the board.

## Correct the misconception first

When a user opens with a wrong premise, **clarify in one line before continuing** — don't answer the wrong question. Common premises to catch: "X3 `.bin` runs on X5" (no — different BPU march), "`apt install hb_mapper` on the board" (no — host Docker only), "RDK Studio = the board" (no — desktop IDE), "RDK is Horizon's" (current brand is D-Robotics), "Ultra = overclocked X5" (no — `bayes` ≠ `bayes-e`), "hobot_dnn in venv" (no — system Python only), "`apt upgrade` 1.x→3.x" (no — reflashing required), "S600 has a 40PIN" (no — 1.8V self-locking connectors), "CAN on S100 = SocketCAN" (no — MCU-domain CANHAL). Full catalog → [hardware-notes.md](references/hardware-notes.md) §2.

## Failure quick-routing: symptom → entry point

Match the error keyword, then go to [failure-hints.md](references/failure-hints.md) for the exact command + doc (59 entries).

- **Camera** — `SIGABRT` / `exit code -6` / `No image data` / `VIDIOC_*` / `timeout` → 99% YUYV, switch to MJPEG; default node `/dev/video8`
- **Model / BPU** — `No such file *.bin/.hbm` / `OOM` / `model incompatible` / `unsupported op` → use `find` for absolute path; cross-march artifacts don't interchange
- **TROS / ROS2** — `ros2: command not found` / `NO_PUBKEY` / `setup.bash missing` → source humble (X3–S100P) or jazzy (S600)
- **GPIO / I2C / serial / PWM** — `Permission denied` / `gpiochip not found` → pin not muxed; use `gpiofind` (not Pi numbers); serial needs `dialout` group
- **CAN** — `can0 not found` → X5 only has SocketCAN; S-series routes through MCU-domain CANHAL (no `can0` netdev)
- **Power / hang** — `under-voltage` / `throttled` / `kernel panic` / `System halted` → check power supply (X3 5V/3A+, X5 5V/5A, S100 12–20V, S600 12–28V), then temp
- **Network / SSH** — `Connection refused` / `timeout` / `Host key verification failed` → `ip addr` + `ping`; `ssh-keygen -R` after reflash; fresh S100/S600 → fixed eth1 `192.168.127.10`
- **Device unrecognized** — `No such device` / `ENODEV` → `dmesg | tail -50 && lsusb && ls /dev/tty* /dev/video* /dev/i2c-* /dev/snd/`

## Diagnostic command safety tiers

Classify before running ([full library](references/diagnostic-commands.md)):

- **safe** (read-only, run directly): BPU/SoC monitoring, `free`/`df`/`dmesg`/`journalctl`, `cat /sys/...`, `ip addr`. Universal fallbacks: `cat /sys/devices/system/bpu/bpu0/ratio` (BPU load), `hrut_somstatus` (temp/voltage/clock).
- **moderate** (changes state, confirm intent): `apt`/`pip`/`npm install`, `systemctl`, `nmcli`, `docker run`, `insmod`/`modprobe`, kernel-header builds.
- **dangerous** (can destroy the system / needs explicit OK): `dd`, `mkfs`, `rm -rf /`, `fdisk`/`parted`, flash erase, `modules_install`/`depmod`, writes to `/boot` · `/lib/modules` · `/etc/fstab`, bootloader/initramfs changes. **Never run these before the board is confirmed.**

## Workflow 1 — Confirm board & baseline

**Trigger:** identify board / 确认板型 / board profile / connected a new device / 不知道是哪块.
**Precondition:** you have a shell (SSH, serial, or RDK Studio).

1. **Read board identity** `[safe]` — run `bash scripts/board_probe.sh` for structured JSON output (`board_id`, `som_name`, `model`, `os_version`), or use the raw identity probe at the top of this file. Map output to X3/X5/Ultra/S100/S100P/S600. Unknown output → keep collecting logs.
2. **Read OS/image version** `[safe]` — `cat /etc/version` (and `rdkos_info` on 2.1.0+). Package names, TROS path, and toolchain advice all depend on this.
3. **Pick the BPU monitor by board** `[safe]` — X3: `hrut_smi`; X5/Ultra: `hrut_bpuprofile -b 0`; S-series: `hrut_bpuprofile`; universal fallback: `cat /sys/devices/system/bpu/bpu0/ratio`. (`hrut_smi`/`bputop` are NOT on X5.)
4. **State the baseline back** — name board, SoC/BPU arch, OS version, and what's still unknown before giving any install/deploy/camera/TROS advice. Don't apply the X5 template to an unconfirmed board.

**Safety:** read-only only; no flashing/upgrade/GPIO output before the board is confirmed.

**验证:** `bash scripts/board_probe.sh` outputs JSON with `board_id` matching the expected board (X3/X5/Ultra/S100/S100P/S600); `cat /etc/version` confirms OS image version; BPU monitor command (`hrut_smi` / `hrut_bpuprofile` / `cat /sys/devices/system/bpu/bpu0/ratio`) returns a non-zero ratio.

## Workflow 2 — S-series xburn flashing (DFU / Fastboot)

**Trigger:** flash S100/S100P/S600 / xburn / enter download mode / DFU / Fastboot / bricked / blank-board flash. (X3/X5/Ultra use **SD card**, not xburn.) Full step-by-step: [xburn-flashing.md](references/xburn-flashing.md).

1. **Host prep** — PC USB ↔ board **Type-C**, high-quality short shielded cable. Linux: `apt install android-tools-adb android-tools-fastboot dfu-util`. Windows: `sunrise5_winusb` driver + CH340 serial driver (921600/8/N/1/none). Full host setup → [xburn-flashing.md](references/xburn-flashing.md) §2.
2. **Choose mode** — **DFU+Fastboot** (blank/bricked, must set hardware into DFU) vs **Fastboot** (normal update, U-Boot boots or `fastboot 0`).
3. **Enter DFU** — per-board switch sequence (S100/S100P: SW1+SW2 combo; S600 V0P1: jumper; V0P2: FLASH switch) → [xburn-flashing.md](references/xburn-flashing.md) §4.
4. **Xburn settings** — product `RDKS100`/`RDKS600`, media **S100=`emmc`** / **S600=`ufs`**, type `secure` → [xburn-flashing.md](references/xburn-flashing.md) §5. Region flash/backup → §6–7.
5. **Finish** — power off, flip boot switch back (exit DFU), power on. First boot ~45 s config; HDMI shows Ubuntu desktop.

**Safety:** flashing is **dangerous** (flash erase). Confirm the board matches the `product` image (don't flash an S100 image onto an S600); always set boot switches/jumpers with the board **powered off**.

**验证:** `xburn --chip` reads the correct chip model; after reboot, `bash scripts/board_probe.sh` shows the board type changed to the flashed target; HDMI displays the Ubuntu desktop within ~45 s of first-boot config.

## Worked examples

**Example 1 — "板子连不上，ssh 一直 timeout,是新到的 S100"**
A fresh S100/S600 has **eth1 fixed at `192.168.127.10`** (eth0 is DHCP). Tell them: set the PC NIC to the same subnet (e.g. `192.168.127.100/24`), then `ssh root@192.168.127.10` or `ssh sunrise@192.168.127.10`. Don't chase Wi-Fi/router config first.

**Example 2 — "跑 ros2 launch 报 /opt/tros/humble/setup.bash: No such file,这是 S600"**
On S600 the premise is wrong: **S600 is Ubuntu 24.04 / ROS2 Jazzy**, so TROS lives at `/opt/tros/jazzy/`, packages are `tros-jazzy-*`. `source /opt/tros/jazzy/setup.bash`. Humble paths are for X3/X5/Ultra/S100/S100P only.

**Example 3 — "USB 摄像头 launch 一跑就 exit code -6 / SIGABRT"**
Camera node crash, almost always format. Order: `ls /dev/video*` + `lsusb` → `v4l2-ctl -d /dev/video0 --list-formats-ext` to read real modes → set the launch to **MJPEG** at a resolution that exactly matches a listed entry (validate 640×480 first). Note the RDK USB-cam default node is `/dev/video8`. Don't tweak other params before the format matches.

**Example 4 — "我要给一块变砖的 S600 重新刷系统"**
Route to Workflow 2 / xburn-flashing.md. Use **DFU+Fastboot** (blank/bricked). Enter DFU by board rev: V0P1 short the jumper, V0P2 set `FLASH` ON — both with PWR KEY OFF first, then ON until the `FLS` red LED lights. Xburn: product `RDKS600`, media `ufs`, type `secure`. Always power off before flipping switches.

## Common pitfalls

| ❌ Don't | ✅ Do |
|---------|------|
| Assume X5 when the board is unconfirmed | Run the socinfo probe first; ask for logs if unclear |
| Tell S600 users to source `humble` | S600 = Jazzy (`/opt/tros/jazzy`) |
| Flash an X3/X5 image with xburn | xburn is S-series only; X-series use SD card |
| Set xburn media wrong | S100/S100P = `emmc`, S600 = `ufs` |
| Flip S-series boot switches while powered | Always power off first |
| Use Raspberry Pi gpiochip numbers | `gpiofind "<line>"` — numbers differ per board |
| Recite default-IP from memory | wired RDK is `192.168.127.10`; S eth1 is fixed there |
| Say only `root/root` (or only `sunrise`) | Both `sunrise/sunrise` and `root/root` ship on every image |

## Anti-hallucination guardrails

When answering from this skill, follow these rules — never fabricate facts, commands, or file paths:

1. **Report only observed data.** Quote what scripts/commands actually return, not what you remember. If the probe says `board_id: X5`, answer for X5 — even if the user insists it's an S100.
2. **No fabrication when tools are missing.** If a script or reference doesn't exist, say "not found" — don't invent from memory. Route to the appropriate skill or doc instead.
3. **Preserve null/false/empty on failure.** If a probe returns `null` or `false`, report that — don't substitute a plausible value. Empty output is data, not an error to "fix".
4. **No substitution off-platform.** If `off_platform: true`, say "probe didn't run on an RDK board" — don't guess what it would have returned. Ask for on-board logs.
5. **No hand-editing JSON.** Scripts emit structured JSON; never hand-craft output. If the contract says `{ok,off_platform,reason,fields}`, that's what goes to the user.
6. **Acknowledge sandbox limits.** If you can't run a command, say so — don't pretend you did. Offer the command for the user to run.
7. **Read-only boundary.** Never modify the system — no `dd`, `mkfs`, `rm -rf`, `apt install`, `reboot`, or GPIO output without explicit user confirmation.

## Reference map

| Read this | When |
|-----------|------|
| [failure-hints.md](references/failure-hints.md) | A concrete error string — 59 symptom→advice→doc entries (camera, model, TROS, GPIO, power, network, audio, S-series specifics) |
| [official-faq.md](references/official-faq.md) | The official rdk_doc/rdk_s_doc `08_FAQ` Q&A points with URLs and board coverage (problem→answer); complements failure-hints |
| [xburn-flashing.md](references/xburn-flashing.md) | Flashing an S100/S100P/S600 — full DFU/Fastboot steps, Xburn settings, region flash/backup, host driver setup, **plus boot chain & image architecture (§9), Linux/macOS Xburn (§10), manual fastboot (§11), flash failure troubleshooting (§12), full-flash vs OTA vs miniboot decision matrix (§13)** |
| [diagnostic-commands.md](references/diagnostic-commands.md) | Need a command's risk tier or board applicability before running it |
| [hardware-notes.md](references/hardware-notes.md) | Common dev traps and the full misconception→correction catalog |
| `scripts/board_probe.sh` | Live board identity probe — reads `/sys/class/socinfo/` + `/proc/device-tree/model` for current board_id / som_name / model / OS version (structured JSON `{ok,off_platform,reason,fields}`; non-board → `{"ok":false,"off_platform":true,"reason":"not_on_rdk_board","fields":null}`) |
