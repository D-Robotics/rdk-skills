# S-Series xburn Flashing (S100 / S100P / S600)

> Source: official `D-Robotics/rdk_s_doc`, `docs/01_Quick_start/02_install_os/rdk_s100|rdk_s600/03_xburn/{01_windows,02_Linux}.md`. Facts verified verbatim against the docs; nothing invented.

X3/X5/Ultra flash from an **SD card** (balenaEtcher / RDK Studio flasher / Rufus) and do **not** use xburn. Only the S-series (Nash) boards flash over USB with the **Xburn** tool through DFU/Fastboot.

## 1. Hardware connection

Connect the PC USB port to the board's **Type-C** port. Use a high-quality cable: shielded, as short as possible, high data-transfer quality. A poor cable is the most common cause of unstable flashing.

## 2. Host preparation

### Linux

```bash
sudo apt update
sudo apt install android-tools-adb android-tools-fastboot
sudo apt install dfu-util
```

### Windows

1. **USB WinUSB driver** — download `sunrise5_winusb.zip` from `archive.d-robotics.cc/downloads/software_tools/winusb_drivers/`, unzip, right-click `install_driver.bat` → **Run as administrator**. After success, Device Manager shows an **Android Device**; before success it shows an unknown **USB download gadget**.
2. **CH340 serial driver** — required to see the board's serial port (download from the resource center's tools section).
3. **Serial terminal parameters** (e.g. MobaXterm → Session → Serial):

   | Setting | Value |
   |---|---|
   | Baud rate | 921600 |
   | Data bits | 8 |
   | Parity | None |
   | Stop bits | 1 |
   | Flow control | None |

4. To verify the driver via U-Boot: power on, immediately hold **Space** to drop into the U-Boot command line, then type `fastboot 0` to put the board into Fastboot.

## 3. Download modes

| Mode | Connection | Use case | Note |
|------|-----------|----------|------|
| **DFU+Fastboot** | USB | Blank board, or system corrupted / bricked | Must set the hardware into DFU first |
| **Fastboot** | USB | Updating an already-working system | Requires a non-blank board whose U-Boot still boots |

Fastboot entry (working board): either it auto-creates an ADB device that Xburn drives into Fastboot, or you manually drop into U-Boot and type `fastboot 0`.

## 4. Enter DFU mode (per board)

### S100 / S100P

1. SW1 → **↑** — power off
2. SW2 → **↑** — enter Download mode
3. SW1 → **▽** — power on
4. `DOWNLOAD` LED lights → in DFU mode. If not, press **K1** to reset.

Also required: set **SW3 = boot from on-board eMMC**. Booting from an M.2 NVMe SSD is **not supported** for flashing.

### S600 V0P1

1. `PWR KEY` → **OFF** — power off
2. **Short the jumper cap** — enter DFU
3. `PWR KEY` → **ON** — power on
4. `FLS` red LED lights → in DFU mode

### S600 V0P2

1. `PWR KEY` → **OFF** — power off
2. `FLASH` switch → **ON** — enter DFU
3. `PWR KEY` → **ON** — power on
4. `FLS` red LED lights → in DFU mode

## 5. Xburn settings — full image

| Setting | S100 / S100P | S600 |
|---------|--------------|------|
| Product model (产品型号) | `RDKS100` | `RDKS600` |
| Connection mode (连接模式) | `usb` | `usb` |
| Download mode (下载模式) | `DFU+Fastboot` (blank/bricked) or `Fastboot` (normal) | same |
| **Media (介质存储)** | **`emmc`** | **`ufs`** |
| Firmware type (类型) | `secure` | `secure` |
| Image directory | browse to the `product` firmware folder | same |

Then click **Start (开始升级)** and power the board on when prompted. On completion:

- **DFU+Fastboot:** power off, flip the boot switch back down (exit DFU), power on again.
- **Fastboot:** simply power-cycle.

First boot runs ~45 s of default configuration; with HDMI connected the display should show the Ubuntu desktop. The **green** LED on = hardware power OK. If there is no display output after >2 minutes, boot failed — debug over the serial port.

## 6. Region-specific flash (S100 / S600)

In Xburn's **advanced config**, tick "flash specified region (烧录指定区域)" and select regions.

### S100 regions

| Region | Media | Contents | Image |
|--------|-------|----------|-------|
| `miniboot_flash` | Norflash | base boot image (HSM/MCU0 etc.) | `img_packages/disk/miniboot_flash.img` |
| `miniboot_emmc` | eMMC | base boot image (BL31/U-Boot etc.) | `img_packages/disk/miniboot_emmc.img` |
| `emmc` | eMMC | full eMMC image (includes miniboot_emmc) | `img_packages/disk/emmc_disk.img` |

### S600 regions

| Region | Media | Contents | Image |
|--------|-------|----------|-------|
| `miniboot_flash` | Norflash | base boot image (HSM/MCU0 etc.) | `img_packages/disk/miniboot_flash.img` |
| `miniboot_ufs` | UFS | base boot image (BL31/U-Boot etc.) | `img_packages/disk/miniboot_ufs.img` |
| `ufs` | UFS | full UFS image (includes miniboot_ufs) | `img_packages/disk/ufs_disk.img` |

## 7. Region backup (S100)

Advanced config → tick "backup specified region (备份指定区域)". Backups output `.img` files under `img_packages/disk/` (e.g. `miniboot_flash_backup.img`, `emmc_disk_backup.img`). **To flash a backup image back, rename its `.img` extension to `.simg` first** — Xburn only accepts `.simg` when flashing a backup. Full-medium backup can take a long time.

## 8. Safety

- Flashing is **dangerous** (flash erase). Confirm the board matches the `product` image — never flash an S100 image onto an S600 or vice-versa.
- Always set boot switches / jumpers with the board **powered off**.
- For a blank or bricked board you must use **DFU+Fastboot**; `Fastboot` requires a board whose U-Boot still boots.
- Symptoms of a failed/interrupted flash (e.g. `xburn ... failed`, `mcu upgrade fail`, corrupt GPT) → re-enter the correct download mode, use a direct USB connection (no hub), retry, and keep the full log. See failure-hints entries 31–32 and §12 below.

## 9. Boot chain & image architecture

> Source: `rdk_s_doc` xburn docs (image package layout), `rdk-board-delegate` s-advanced.md §6 (partition classes), and the `product` firmware folder structure. Verified against the official image packages.

Understanding **what** you are flashing prevents most “flashed the wrong region” mistakes. The S-series boot chain and image package have a specific structure:

### 9.1 Boot chain (power-on → Linux userspace)

```
ROM boot → SBL (secondary bootloader) → BL31 (ATF/TF-A) → OP-TEE → U-Boot → Linux kernel → rootfs
```

- **SBL** — on-chip ROM loads the secondary bootloader from the **Norflash** (the `miniboot_flash` region).
- **BL31 / OP-TEE / U-Boot** — loaded from the **eMMC** (S100/S100P) or **UFS** (S600), corresponding to the `miniboot_emmc` / `miniboot_ufs` region.
- **Linux kernel + rootfs** — the bulk of the `emmc` / `ufs` full-disk image.

This is why there are **two miniboot images** plus one full image:

| Image | Media | What it contains | Boot stage |
|-------|-------|------------------|------------|
| `miniboot_flash.img` | Norflash | SBL, HSM (security), MCU0 firmware | Stage 1 — chip ROM loads this first |
| `miniboot_emmc.img` (S100) / `miniboot_ufs.img` (S600) | eMMC / UFS | BL31, OP-TEE, U-Boot, SPL, Acore config | Stage 2 — SBL loads this from the main storage |
| `emmc_disk.img` (S100) / `ufs_disk.img` (S600) | eMMC / UFS | Everything: miniboot_emmc/ufs + kernel + rootfs + partitions | Full system |

### 9.2 Partition classes (why full flash ≠ OTA ≠ miniboot)

The S-series storage is partitioned into three classes (see [s-advanced.md](../../rdk-board-delegate/references/s-advanced.md) §6 for the full OTA design):

| Class | Partitions | Upgraded by |
|-------|-----------|-------------|
| **Persistent** | ubootenv, veeprom, userdata | Nothing — never upgraded, preserves user data across flashes |
| **AB (dual-slot)** | boot_a / boot_b, system_A / system_B | OTA (alternating, seamless upgrade) |
| **BAK (primary + backups)** | HSM_FW, SBL, SPL, MCU, bl31, optee, uboot, etc. | Miniboot upgrade (`rdk-miniboot-update`) or full flash |

**Key implication:** a full-flash with Xburn writes the **entire** medium (including partition table + Persistent), wiping everything. Miniboot upgrade only touches BAK + AB boot partitions. OTA only touches AB system partitions. Choose the right tool for the job (§13).

### 9.3 The `product` firmware folder

When you download an S-series firmware package and unzip it, you get a `product/` directory. Inside `product/img-packages/disk/`:

```
product/
├── img-packages/
│   └── disk/
│       ├── miniboot_flash.img     ← Norflash base boot (SBL/HSM/MCU0)
│       ├── miniboot_emmc.img      ← S100 eMMC base boot (BL31/U-Boot/...)
│       ├── miniboot_ufs.img       ← S600 UFS base boot (BL31/U-Boot/...)
│       ├── emmc_disk.img          ← S100 full eMMC image
│       └── ufs_disk.img           ← S600 full UFS image
```

In Xburn, the **Image directory** field should point to this `product/` folder. Xburn auto-detects which images to flash based on the selected regions (§6) or the full-image mode (§5).

## 10. Linux / macOS Xburn

> Source: `host-flashing.md` ("Xburn is a PC tool — Windows / macOS / Linux"), `rdk_s_doc` xburn docs. The Windows GUI flow is in §2–§5 above; this section covers the Linux/macOS path.

Xburn is cross-platform. On **Linux**, the host prep is simpler (no WinUSB driver needed — Linux has native DFU/Fastboot USB support):

```bash
# Install prerequisites (Debian/Ubuntu)
sudo apt update
sudo apt install android-tools-adb android-tools-fastboot dfu-util

# Verify the board is visible in DFU mode
dfu-util -l                    # should list the S-series device
fastboot devices               # in Fastboot mode
```

On **macOS**, install `android-platform-tools` (for `fastboot`) and `dfu-util` via Homebrew:
```bash
brew install android-platform-tools dfu-util
```

The Xburn GUI on Linux/macOS has the same settings as Windows (§5): product model, connection mode `usb`, download mode `DFU+Fastboot` or `Fastboot`, media `emmc`/`ufs`, type `secure`, image directory → `product/`.

**udev rules (Linux):** if the board isn't visible, add a udev rule for the D-Robotics USB VID/PID, then `sudo udevadm control --reload`.

## 11. Manual fastboot (advanced)

> Source: `rdk_s_doc` xburn docs (U-Boot `fastboot 0`), general Android fastboot protocol knowledge. For when Xburn GUI fails or you need fine-grained control.

If the board's U-Boot still boots (not blank/bricked), you can enter Fastboot manually and flash individual partitions with the `fastboot` CLI — no Xburn GUI needed:

```bash
# 1. Enter U-Boot: power on, immediately hold SPACE in the serial console
# 2. At the U-Boot prompt, type:
=> fastboot 0

# 3. On the host, verify:
fastboot devices

# 4. Flash individual partitions (examples):
fastboot flash miniboot_flash  product/img-packages/disk/miniboot_flash.img
fastboot flash miniboot_emmc   product/img-packages/disk/miniboot_emmc.img   # S100
fastboot flash emmc            product/img-packages/disk/emmc_disk.img        # S100 full
fastboot flash ufs             product/img-packages/disk/ufs_disk.img          # S600 full

# 5. Reboot
fastboot reboot
```

**When to use manual fastboot:**
- Xburn GUI won't start or crashes on your OS
- You only need to flash one specific region (e.g. just the kernel partition)
- Debugging a specific flash step (you can see the exact fastboot error)

**When NOT to use manual fastboot:**
- Blank/bricked board — must use DFU mode first (manual `dfu-util` is possible but the Xburn DFU+Fastboot flow is far more reliable)
- You don't know which partition maps to which image — use Xburn's region selector (§6) instead

## 12. Flash failure troubleshooting

> Source: `failure-hints.md` entries 31–32, `rdk_s_doc` xburn docs. A diagnosis flow for when flashing fails.

### 12.1 Xburn won't detect the board

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Windows: Device Manager shows "USB download gadget" (unknown) | WinUSB driver not installed | Install `sunrise5_winusb` driver (§2.1), re-plug USB |
| Linux: `dfu-util -l` shows nothing | udev rules missing / wrong cable | Add udev rule; try `sudo dfu-util -l`; use a **data** cable not a charge-only cable |
| Board not in DFU mode | Wrong switch sequence | Re-do the per-board DFU entry sequence (§4); confirm the **DOWNLOAD** / **FLS** LED is lit |
| `fastboot devices` empty (Fastboot mode) | U-Boot didn't enter fastboot | Serial console → hold SPACE at boot → `fastboot 0`; or re-enter DFU |

### 12.2 Flash starts but fails mid-way

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `xburn ... failed` / timeout | Poor USB cable / hub | Use a **short, shielded, high-quality** cable; **direct** USB port (no hub); retry |
| `mcu upgrade fail` | MCU0 firmware write failed | Re-enter DFU mode; re-flash `miniboot_flash` region only first, then full image |
| Corrupt GPT / partition table | Interrupted flash | Re-enter DFU+Fastboot; re-flash the **full** `emmc`/`ufs` image (rewrites GPT) |
| Flash completes but board won't boot | Wrong image for the board, or media mismatch | Confirm: S100→`emmc`+`RDKS100`, S600→`ufs`+`RDKS600`; never cross-flash |
| First boot > 2 min, no HDMI output | Boot failed | Serial console (921600 baud) → check for U-Boot/kernel errors; re-flash if needed |

### 12.3 Serial console — what to expect during a successful flash

Connect the serial console **before** starting Xburn. During a normal flash + first boot you should see:

1. **DFU phase** — minimal output (DFU is pre-U-Boot); the `DOWNLOAD`/`FLS` LED is the visual indicator.
2. **Fastboot phase** — U-Boot prints `Fastboot entered`; Xburn sends images; you may see `flash miniboot_flash`, `flash emmc` etc.
3. **Reboot** — U-Boot → BL31 → OP-TEE → kernel boot log → systemd → first-boot config (~45 s) → Ubuntu desktop (if HDMI connected).

If the serial output **stops** at U-Boot and never reaches the kernel, the boot chain is broken — re-flash `miniboot_emmc`/`miniboot_ufs` (the BL31/U-Boot image). If it stops before U-Boot, re-flash `miniboot_flash` (the SBL image).

## 13. Full flash vs OTA vs miniboot upgrade — decision matrix

> Source: [s-advanced.md](../../rdk-board-delegate/references/s-advanced.md) §6, `rdk-command-manual` SKILL.md. Choose the right upgrade mechanism.

| Scenario | Use | What it writes | Data preserved? | Requires Xburn? |
|---------|-----|----------------|-----------------|-----------------|
| Blank board / first flash | **Xburn full image** (`emmc`/`ufs` disk image) | Everything (GPT + all partitions) | No — clean slate | ✅ Yes |
| Bricked board / corrupt system | **Xburn DFU+Fastboot** | Everything | No | ✅ Yes |
| Normal system re-flash | **Xburn Fastboot** | Everything | No | ✅ Yes |
| Upgrade bootloader only (SBL/BL31/U-Boot/OP-TEE/MCU) | **`rdk-miniboot-update`** | BAK + AB boot partitions only | ✅ Yes (userdata, rootfs overlay) | ❌ No (on-board command) |
| Seamless system upgrade (kernel + rootfs) | **System OTA** (AB dual-slot) | AB system partitions only | ✅ Yes (overlay persists) | ❌ No (on-board) |
| Partition table change | **Xburn full image** | Everything (including GPT) | No | ✅ Yes (miniboot/OTA can't change GPT) |

**Key rules:**
- `rdk-miniboot-update` **cannot** upgrade the partition table — only Xburn full flash can.
- `rdk-miniboot-update` has **no auto-rollback** — a failed `dd` or power loss mid-write can brick boot. For safety-critical fields, prefer the full system OTA (AB + overlayfs) flow.
- On S-series, `rdk-miniboot-update` is **not** the same as the X-series command. Verify with `which rdk-miniboot-update` on the board first (see `rdk-command-manual` SKILL.md).
- Full flash with Xburn is the **only** way to recover a blank or bricked board — OTA and miniboot upgrade require a booting system.
