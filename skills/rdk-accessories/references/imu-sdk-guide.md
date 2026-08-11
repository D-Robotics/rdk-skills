# RDK IMU SDK & Driver Reference

> Sources: D-Robotics `accessories_doc/docs/03_imu_module/05_software/{01_overview,02_c_api,03_python_api,04_ros2,05_iio}.md`, [rdk-imu-module-sdk](https://github.com/D-Robotics/rdk-imu-module-sdk) repo (MIT), and `rdk_doc/.../rdk_x5/imu/icm42688.md` for the ICM-42688-P IIO path. Facts re-verified against the accessories-catalog and the default-config asset; only what the docs/repos state.

## Table of contents

- [Architecture overview](#architecture-overview)
- [1. rdk-imu-module-sdk (Path A — recommended)](#1-rdk-imu-module-sdk-path-a--recommended)
  - [1.1 Repository structure](#11-repository-structure)
  - [1.2 Prerequisites & dependencies](#12-prerequisites--dependencies)
  - [1.3 Build & install](#13-build--install)
  - [1.4 C API reference](#14-c-api-reference)
  - [1.5 Python API reference](#15-python-api-reference)
  - [1.6 ROS2 node reference](#16-ros2-node-reference)
  - [1.7 Configuration reference (rdk_imu_config_t)](#17-configuration-reference-rdk_imu_config_t)
  - [1.8 Cross-compilation & non-X5 boards](#18-cross-compilation--non-x5-boards)
- [2. RDK OS BMI088 IIO driver (Path B — X5/X5M only)](#2-rdk-os-bmi088-iio-driver-path-b--x5x5m-only)
  - [2.1 Enable / disable](#21-enable--disable)
  - [2.2 sysfs interface](#22-sysfs-interface)
  - [2.3 I2C vs SPI registration](#23-i2c-vs-spi-registration)
- [3. ICM-42688-P (GS130Wi built-in IMU)](#3-icm-42688-p-gs130wi-built-in-imu)
- [4. API call patterns & examples](#4-api-call-patterns--examples)
- [5. Troubleshooting & debugging](#5-troubleshooting--debugging)
- [6. Performance tuning guide](#6-performance-tuning-guide)
- [Quick lookup: which path, which board](#quick-lookup-which-path-which-board)

---

## Architecture overview

The RDK ecosystem has **two IMU chips** and **two software paths**. Knowing which chip + which path applies is half the battle.

### Two IMU chips

| Chip | Where it lives | Interface to host | Bring-up path |
|------|----------------|-------------------|---------------|
| **Bosch BMI088** | RDK IMU Module (standalone, 40PIN) + S100/S600 MCU-Port on-board | I2C or SPI (jumper-selected on the module; SPI-5/SPI-13 on MCU boards) | Path A (SDK) or Path B (IIO, X5/X5M only) |
| **InvenSense ICM-42688-P** | Built into GS130Wi stereo camera | I2C multiplexed over right-eye MIPI connector (pins 20/21 = SCL/SDA shared with camera) | IIO driver on X5 (OS 3.4.1+); SDK does NOT cover this chip |

> **Critical:** the rdk-imu-module-sdk is designed for the **BMI088** only. It does not drive the GS130Wi's ICM-42688-P. The two chips have different registers, different IIO device names, and different default drivers.

### Two software paths

| Path | What | Boards | When to use |
|------|------|--------|-------------|
| **A — rdk-imu-module-sdk** | User-space C/Python/ROS2 SDK, no IIO dependency, uses `libgpiod` for GPIO interrupts | All aarch64 RDK boards with kernel >5.10 (X5/X5M direct; S100/S100P/S600 via jumper wiring) | Recommended for non-X5 boards, cross-platform needs, or when you need C/Python API control |
| **B — RDK OS BMI088 IIO driver** | Kernel IIO driver, accessed via `/sys/bus/iio/devices/` | X5 / X5 Module only (OS image 3.4.x, compatible with 3.5.x) | Quickest path on X5; no SDK build needed; sysfs reads only |

---

## 1. rdk-imu-module-sdk (Path A — recommended)

> Source: [github.com/D-Robotics/rdk-imu-module-sdk](https://github.com/D-Robotics/rdk-imu-module-sdk) (MIT license). The repo contains `core/` (C library), `python/` (Python bindings), and `ros2/` (ROS2 node).

### 1.1 Repository structure

```
rdk-imu-module-sdk/
├── core/           # C library + test binary
│   ├── Makefile    # make / make test / make install
│   ├── include/    # rdkimu.h (public API + rdk_imu_config_t + enums)
│   └── src/        # SDK implementation
├── python/         # Python wheel bindings
│   ├── Makefile    # make / make install
│   └── examples/   # test_imu.py
├── ros2/           # ROS2 node package (rdk_imu_module)
│   └── colcon build
└── examples/       # usage examples
```

### 1.2 Prerequisites & dependencies

| Requirement | Detail |
|-------------|--------|
| Architecture | aarch64 (ARM64) — runs on-board only, not on x86 PC |
| Kernel | >5.10 (needs standard user-space I2C/SPI + `gpiod`) |
| Build deps | `sudo apt install build-essential cmake libgpiod-dev python3-pip` |
| ROS2 (optional) | TROS sourced: `source /opt/tros/{humble,jazzy}/setup.bash` |

### 1.3 Build & install

**C library:**
```bash
cd core
make                # builds out/test (auto-probes I2C/SPI + address, 400 Hz output)
sudo ./out/test     # or: make test
make install        # installs headers + shared lib to system paths
make uninstall      # removes them
```

**Python bindings (requires `core/` built first):**
```bash
cd core && make     # step 1: build the C library
cd ../python
make                # builds dist/*.whl
pip install dist/rdkimu-*.whl   # or: make install
sudo python3 examples/test_imu.py
```

**ROS2 node:**
```bash
source /opt/tros/humble/setup.bash    # S600: /opt/tros/jazzy/setup.bash
cd ros2
colcon build
source install/setup.bash
ros2 launch rdk_imu_module rdk_imu.launch.py
```

### 1.4 C API reference

> Source: `accessories_doc/docs/03_imu_module/05_software/02_c_api.md`. The exact function signatures live in `core/include/rdkimu.h`; the doc describes the call contract and parameter semantics.

**API call order (mandatory lifecycle):**

```
bus_init → device_init → enable → read_* → disable → deinit/destroy
```

Each step must succeed before the next; skipping `enable` means no data; calling `read_*` after `disable` returns invalid data.

**Bus init — three forms:**

| Form | Parameters | Use case |
|------|-----------|----------|
| AUTO | (none) — auto-searches I2C/SPI + address | Quick test; **not** usable with multiple IMUs on the same bus |
| Explicit I2C | bus number + device address | When you know the I2C bus/address (e.g., `i2cdetect` confirmed) |
| Explicit SPI | bus number + chip-select + speed | When using SPI (jumper set to SPI side) |

**Device init** — takes a `rdk_imu_config_t` (see §1.7) covering range/ODR/bandwidth/interrupt/FIFO settings. Use `RDK_IMU_X5_DEFAULT_CONFIG` macro as the starting template (see [assets/rdk_imu_x5_default_config.txt](../assets/rdk_imu_x5_default_config.txt)).

**Read functions:**

| Function | Returns | When to use |
|----------|---------|-------------|
| `fifo_available()` | FIFO backlog count | Check how many samples are buffered before reading |
| `read_indep()` | Independent accel/gyro packets | BMI088 accel and gyro are two **independent, unsynchronized** devices — check `data.accel.valid` / `data.gyro.valid` before using each |
| `read_fused(fuse_by, max_age_ns)` | Time-aligned 6-axis data | 1-D linear interpolation to time-align all 6 axes; `fuse_by` = reference side (accel or gyro); `max_age_ns` recommended ≥3× the ODR period |

**Data structure fields:**

| Field | Type | Unit / meaning |
|-------|------|----------------|
| `accel.x, .y, .z` | float | **m/s²** (raw SDK read units) |
| `gyro.x, .y, .z` | float | **°/s** (raw SDK read units) |
| `timestamp_ns` | uint64 | `CLOCK_MONOTONIC` nanoseconds |
| `valid` | int | **1 = valid**, 0 = invalid/stale |

> **Unit note:** the raw SDK reads are accel m/s² + gyro °/s. The ROS2 node separately converts angular velocity to **rad/s** for the `sensor_msgs/Imu` message. Do not mix SDK units with ROS2 units.

### 1.5 Python API reference

> Source: `accessories_doc/docs/03_imu_module/05_software/03_python_api.md`. The Python API mirrors the C API; the wheel is `rdkimu`.

**Install:** `pip install dist/rdkimu-*.whl`

**Usage pattern (mirrors C lifecycle):**
```python
import rdkimu

# Bus init (AUTO or explicit I2C/SPI)
imu = rdkimu.IMU()             # AUTO probe
# or: imu = rdkimu.IMU(bus=5, addr=0x69)  # explicit I2C

# Device init with config
imu.init(rdkimu.RDK_IMU_X5_DEFAULT_CONFIG)

# Enable + read
imu.enable()
data = imu.read_indep()
if data.accel.valid:
    print(f"accel: {data.accel.x}, {data.accel.y}, {data.accel.z} m/s²")
if data.gyro.valid:
    print(f"gyro: {data.gyro.x}, {data.gyro.y}, {data.gyro.z} °/s")
print(f"timestamp: {data.timestamp_ns} ns")

# Cleanup
imu.disable()
imu.deinit()
```

> The Python method names and class structure mirror the C API: `read_indep()`, `read_fused(fuse_by, max_age_ns)`, `fifo_available()`. Check `help(rdkimu)` after install for the exact signatures.

### 1.6 ROS2 node reference

> Source: `accessories_doc/docs/03_imu_module/05_software/04_ros2.md`. Package: `rdk_imu_module`.

**Launch:**
```bash
source /opt/tros/humble/setup.bash    # S600: jazzy
ros2 launch rdk_imu_module rdk_imu.launch.py
```

**Published topic:**

| Topic | Type | Fields |
|-------|------|--------|
| `/rdkimu/data` (default, configurable via `imu_topic` param) | `sensor_msgs/msg/Imu` | `angular_velocity` in **rad/s** (ROS convention), `linear_acceleration` in m/s², `header.stamp` from CLOCK_MONOTONIC ns |

**Frame & orientation:**
- Default `frame_id`: `imu_link`
- Orientation: **not provided** by the BMI088 (no magnetometer) → constant quaternion `(0,0,0,1)` with attitude covariance set to **-1** (signals "not available" per ROS2 convention)

**Covariance:**
- Accel/gyro diagonal covariances are **auto-computed** from the configured bandwidth + BMI088 noise density specs

**Runtime services:**

| Service | Type | Effect |
|---------|------|--------|
| `~/enable` | `std_srvs/srv/Trigger` | Resumes publishing after a `~/disable` call |
| `~/disable` | `std_srvs/srv/Trigger` | Pauses publishing at runtime (does not close the device) |

**Configurable parameters (map 1:1 to `rdk_imu_config_t`):**

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `frame_id` | string | `imu_link` | ROS frame for the Imu message |
| `imu_topic` | string | `/rdkimu/data` | Output topic name |
| `fuse_by` | enum | (from config) | Reference side for time fusion: accel or gyro |
| `max_age_ns` | int | (from config) | Fusion time tolerance; ≥3× ODR period |
| `publish_rate` | float | (from config) | Output rate (Hz); may be lower than sensor ODR |
| `accel_range` | enum | ±24 g | See config reference §1.7 |
| `accel_odr` | enum | 400 Hz | |
| `gyro_range` | enum | ±2000 dps | |
| `gyro_bandwidth` | enum | ODR400/BW47 | Gyro ODR + bandwidth are a bound pair |
| `accel_drdy_gpio_chip` | int | 4 (X5) | SoC GPIO chip for accel interrupt |
| `accel_drdy_gpio_line` | int | 2 (X5) | SoC GPIO line |
| `gyro_drdy_gpio_chip` | int | 3 (X5) | SoC GPIO chip for gyro interrupt |
| `gyro_drdy_gpio_line` | int | 12 (X5) | SoC GPIO line |

> Check the full list with: `ros2 launch rdk_imu_module rdk_imu.launch.py --show-args`

### 1.7 Configuration reference (rdk_imu_config_t)

> Source: `accessories_doc/docs/03_imu_module/05_software/02_c_api.md` + [assets/rdk_imu_x5_default_config.txt](../assets/rdk_imu_x5_default_config.txt).

**Using the default macro:**
```c
rdk_imu_config_t config = RDK_IMU_X5_DEFAULT_CONFIG;  // copy the X5 defaults
config.accel_range = RDK_IMU_ACCEL_12G;                // override only what you need
```

**Full config member reference:**

| Member | Enum/values | X5 default | Notes |
|--------|-------------|------------|-------|
| `accel_range` | `RDK_IMU_ACCEL_3G/6G/12G/24G` | `RDK_IMU_ACCEL_24G` | Higher range = lower sensitivity |
| `accel_odr` | `12.5/25/50/100/200/400/800/1600 Hz` | 400 Hz | Output data rate |
| `gyro_range` | `RDK_IMU_GYRO_125DPS/250/500/1000/2000DPS` | `RDK_IMU_GYRO_2000DPS` | |
| `gyro_bandwidth` | ODR+bandwidth bound pair (e.g., `RDK_IMU_ODR400_BW47`) | `RDK_IMU_ODR400_BW47` | Gyro ODR 400 Hz / BW 47 Hz |
| `fifo_length` | power of two | 256 | Software FIFO length |
| `fifo_mode` | `RDK_IMU_FIFO_OVERWRITE` / `RDK_IMU_FIFO_DROP` | `OVERWRITE` | Overwrite oldest vs drop new when full |
| `accel_drdy_int` | `RDK_IMU_INT1` / `RDK_IMU_INT2` | INT1 | Accel data-ready interrupt pin |
| `accel_int_gpio_mode` | `RDK_IMU_PP_H` (push-pull active high) and others | PP_H | GPIO interrupt mode |
| `gyro_drdy_int` | `RDK_IMU_INT3` / `RDK_IMU_INT4` | INT3 | Gyro data-ready interrupt pin |
| `gyro_int_gpio_mode` | same enum as accel | PP_H | |
| `accel_drdy_gpio_chip` | int (SoC GPIO chip) | 4 | X5 default; **must verify on other boards** |
| `accel_drdy_gpio_line` | int | 2 | X5 default |
| `gyro_drdy_gpio_chip` | int | 3 | X5 default |
| `gyro_drdy_gpio_line` | int | 12 | X5 default |
| `irq_priority` | int (-1 = auto) | -1 | RT scheduling priority; -1 = auto-pick highest available |
| `irq_thread_timeout_ns` | uint64 | 1000000000 (1 s) | IRQ thread timeout; smaller = higher CPU, larger = slower shutdown |

> **Non-X5 boards:** the GPIO chip/line numbers are **X5-specific**. On S100/S100P/S600, confirm the actual chip/line with `gpioinfo` or `gpiodetect` before copying the defaults. See §1.8.

### 1.8 Cross-compilation & non-X5 boards

The SDK runs on aarch64 only (not x86 PC). It does **not** need cross-compilation in the traditional sense — you build it on the board itself:

```bash
# On the board (X5/S100/S600):
git clone https://github.com/D-Robotics/rdk-imu-module-sdk
cd rdk-imu-module-sdk
sudo apt install build-essential cmake libgpiod-dev python3-pip
cd core && make
```

**On S100/S100P/S600 (cannot direct-plug the 40PIN module):**
1. Jumper-wire the module's 40PIN I2C or SPI to the board's available I2C/SPI pins.
2. Set the 3×5 jumper caps to I2C or SPI side (see [accessories-catalog.md](accessories-catalog.md#3-rdk-imu-module-bosch-bmi088)).
3. **Find the correct GPIO chip/line** for the interrupt pins:
   ```bash
   gpiodetect                       # list all GPIO chips
   gpioinfo <chip>                  # list lines on a chip
   ```
4. Override `accel_drdy_gpio_chip/line` and `gyro_drdy_gpio_chip/line` in the config.
5. Use AUTO bus init (or explicit I2C bus number after `i2cdetect -l` confirms the bus).

> **S100 MCU-Port board on-board BMI088 (SPI-5):** the doc notes `RDKS100_LNX_SDK_V4.0.2 暂未实现` — do not assume this on-board IMU is ready out-of-box. The standalone RDK IMU Module on jumper wires is the supported path.

---

## 2. RDK OS BMI088 IIO driver (Path B — X5/X5M only)

> Source: `accessories_doc/docs/03_imu_module/05_software/05_iio.md`. OS image 3.4.x, compatible with 3.5.x. **Only X5 / X5 Module** — S100/S600 do not have this IIO driver.

### 2.1 Enable / disable

```bash
sudo srpi-config
# → 3 Interface Options → I6 IMU → select:
#     BMI088-I2C-Interface   (for I2C)
#     BMI088-SPI-Interface  (for SPI)
# → Finish → reboot
```

**To remove:**
```bash
sudo srpi-config → I6 IMU → UNSET → power off → detach module
```

### 2.2 sysfs interface

After enabling, the IIO driver creates devices under `/sys/bus/iio/devices/`:

```bash
# Find the device index (N varies by enumeration order):
ls /sys/bus/iio/devices/
# Typically: iio:device0 (accel) + iio:device1 (gyro) — two independent devices

# Confirm the device name:
cat /sys/bus/iio/devices/iio:deviceN/name    # should show "bmi088-accel" / "bmi088-gyro"

# Read raw values:
cat /sys/bus/iio/devices/iio:deviceN/gyr_val
```

> The exact sysfs attribute names (`gyr_val`, `accel_*`, etc.) depend on the driver version. Run `ls /sys/bus/iio/devices/iio:deviceN/` to see all available attributes. Always confirm the device index with `cat name` before substituting N.

### 2.3 I2C vs SPI registration

**I2C self-check:**
```bash
i2cdetect -y -r 5
# Expected: one "UU" (in-use) and one "69" (BMI088 I2C address)
# If you see two "69" and no "UU": power-cycle and re-scan (driver may not have claimed it yet)
```

**SPI registration check:**
```bash
dmesg | grep BS_LOG
# Should show BMI088 SPI registration messages
```

> If `i2cdetect` shows nothing or `dmesg` has no BS_LOG entries, verify the jumper caps are on the correct side (I2C vs SPI) and the module is seated on the 40PIN.

---

## 3. ICM-42688-P (GS130Wi built-in IMU)

> Source: `accessories-catalog.md` §2 + `rdk_doc/.../rdk_x5/imu/icm42688.md`. This chip is **NOT covered by rdk-imu-module-sdk**.

### Access path

The ICM-42688-P is reached through the **right-eye MIPI connector's multiplexed I2C** (pins 20 = SCL, 21 = SDA, shared with the camera sensor). It does not have a separate connector — the camera and IMU share the same I2C bus.

### IIO driver (X5, OS 3.4.1+)

On RDK X5 with OS image 3.4.1+, the ICM-42688 registers as **two separate IIO devices**:

| IIO device name | Covers |
|-----------------|--------|
| `icm42688-gyro` | Gyroscope (3-axis) |
| `icm42688-accel` | Accelerometer (3-axis) |

**Enable:**
```bash
sudo srpi-config → 3 Interface Options → I6 IMU → ICM42688
```

**Verify:**
```bash
ls /sys/bus/iio/devices/
cat /sys/bus/iio/devices/iio:deviceN/name    # confirm "icm42688-*"
```

### Hardware timestamp (3-pin connector + LPWM/EXT switch)

The GS130Wi has an **IMU interrupt-select switch** (LPWM / EXT) that routes INT2:

| Switch position | INT2 routes to | Effect |
|----------------|----------------|--------|
| **LPWM** | Right-eye TRIGL/FSYNC pin | Camera–IMU **hardware sync** — enables timestamp-aligned camera + IMU data (critical for VIO) |
| **EXT** | External 3-pin connector (PIN2) | IMU INT2 goes to an external pin for custom triggering |

> For VIO (`hobot_vio`) or any camera+IMU fusion, set the switch to **LPWM**. See [calibration-guide.md](../../rdk-ros/references/calibration-guide.md#5-timestamp-synchronization) in rdk-ros for the full timestamp sync discussion.

---

## 4. API call patterns & examples

### Pattern 1 — Quick C test (auto-probe)

```bash
cd rdk-imu-module-sdk/core
make test           # builds + runs out/test at 400 Hz, auto-probes I2C/SPI
sudo ./out/test
```

### Pattern 2 — C: explicit I2C + custom config

```c
rdk_imu_config_t config = RDK_IMU_X5_DEFAULT_CONFIG;
config.accel_range = RDK_IMU_ACCEL_12G;    // more sensitivity for low-g motion
config.accel_odr = RDK_IMU_ACCEL_200;     // 200 Hz is enough for a slow robot
config.gyro_bandwidth = RDK_IMU_ODR200_BW23;
// Bus init (explicit I2C, bus 5, address 0x69)
// device_init(&config)
// enable()
// read_indep() or read_fused(RDK_IMU_FUSE_BY_ACCEL, 7500000)  // 7.5ms > 3×200Hz period
```

### Pattern 3 — Python: read_fused for time-aligned data

```python
import rdkimu
imu = rdkimu.IMU()
imu.init(rdkimu.RDK_IMU_X5_DEFAULT_CONFIG)
imu.enable()
# read_fused: fuse_by=accel, max_age_ns=7.5ms (≥3× the 400Hz ODR period = 2.5ms)
fused = imu.read_fused(rdkimu.FUSE_BY_ACCEL, 7500000)
# fused.accel and fused.gyro are time-aligned
imu.disable()
imu.deinit()
```

### Pattern 4 — ROS2: custom publish rate + frame

```bash
ros2 launch rdk_imu_module rdk_imu.launch.py \
    publish_rate:=100.0 \
    frame_id:=imu_link_custom \
    accel_range:=RDK_IMU_ACCEL_6G
```

### Pattern 5 — IIO sysfs quick read (no SDK needed, X5 only)

```bash
sudo srpi-config → I6 IMU → BMI088-I2C-Interface → reboot
i2cdetect -y -r 5                    # confirm "UU" + "69"
ls /sys/bus/iio/devices/
cat /sys/bus/iio/devices/iio:device0/name   # "bmi088-accel" or "bmi088-gyro"
cat /sys/bus/iio/devices/iio:device0/gyr_val
```

---

## 5. Troubleshooting & debugging

### SDK (Path A)

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `make` fails: `libgpiod-dev` not found | Missing build dep | `sudo apt install build-essential cmake libgpiod-dev` |
| `out/test` runs but no data (all zeros) | Module not wired, or wrong I2C bus | `i2cdetect -l` → confirm bus; `i2cdetect -y -r <bus>` → look for `69` |
| `read_indep()` returns `valid=0` for gyro | Gyro interrupt not firing | Check `gyro_drdy_gpio_chip/line` match the board (X5 = chip3/line12); use `gpioinfo` to verify |
| `read_fused()` crashes or returns garbage | `max_age_ns` too small | Set `max_age_ns` ≥3× the ODR period (e.g., 400 Hz → ≥7.5 ms = 7500000 ns) |
| SDK compiles on x86 PC but fails at runtime | SDK requires aarch64 | Build on the board, not on PC |
| ROS2 node starts but topic is empty | TROS not sourced, or `~/disable` was called | `source /opt/tros/*/setup.bash`; `ros2 service call /rdk_imu_module/enable std_srvs/srv/Trigger` |

### IIO (Path B)

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `i2cdetect -y -r 5` shows no `69` | Module not seated, or wrong I2C bus | Reseat on 40PIN; check jumper caps = I2C side |
| `i2cdetect` shows two `69`, no `UU` | Driver didn't claim the device | Power-cycle, re-scan; re-run `srpi-config → I6 IMU` |
| `dmesg | grep BS_LOG` returns nothing (SPI) | SPI not registered | Check jumper caps = SPI side; re-run srpi-config with SPI entry |
| `iio:deviceN` index changes between boots | Enumeration order varies | **Always** `cat name` to confirm; never hardcode N |
| `srpi-config → I6 IMU` has no BMI088 entry | Wrong OS image version | Path B needs OS 3.4.x (compatible with 3.5.x); use Path A SDK instead |

### ICM-42688-P (GS130Wi)

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| No `icm42688-*` IIO devices | OS image <3.4.1, or not enabled | `srpi-config → I6 IMU → ICM42688`; upgrade OS if needed |
| Camera works but IMU doesn't | Right-eye MIPI not fully seated | The IMU I2C is multiplexed on the right-eye connector — reseat the FFC |
| VIO depth map is noise | Switch is on EXT, not LPWM | Set the IMU interrupt switch to **LPWM** for camera–IMU hardware sync |

---

## 6. Performance tuning guide

### Range selection

| Application | Recommended accel range | Recommended gyro range | Why |
|-------------|------------------------|----------------------|-----|
| AMR / indoor robot (slow) | ±3 g or ±6 g | ±250 dps or ±500 dps | Maximize sensitivity for gentle motion |
| Quadruped / dynamic robot | ±12 g | ±1000 dps | Higher accelerations from footfall impacts |
| High-speed / aggressive motion | ±24 g | ±2000 dps | Avoid clipping; lower sensitivity is acceptable |
| VIO / SLAM | ±3 g | ±500 dps | VIO algorithms prefer high sensitivity + low noise |

### ODR & bandwidth

- **VIO / SLAM:** accel 200–400 Hz, gyro 200–400 Hz/BW 20–47 Hz. Higher ODR → more data but more noise in the high band.
- **Pose estimation (complementary filter):** 100–200 Hz is sufficient.
- **Impact detection:** 800–1600 Hz for high-frequency event capture.
- **FIFO tuning:** keep `fifo_length` = 256 (default) unless you see drops at high ODR; switch to `DROP` mode if you prefer losing new data over old (rare).

### Fusion strategy

- `read_indep()`: use when you process accel and gyro independently (e.g., separate complementary filters for pitch/roll).
- `read_fused(fuse_by, max_age_ns)`: use when you feed a 6-axis fusion algorithm (VIO, EKF). Always set `max_age_ns` ≥3× the slowest ODR period. `fuse_by` = the side you trust more for timestamp accuracy (typically accel, which has a higher ODR on BMI088).

### Power & CPU

- The SDK uses a **high-priority sub-thread** to capture GPIO interrupts via `gpiod`. Higher ODR → more interrupt load. Monitor CPU with `top -H -p <pid>`.
- The ROS2 node's `publish_rate` can be set **lower** than the sensor ODR to reduce ROS2 bus traffic (e.g., sensor at 400 Hz, publish at 100 Hz — the SDK internally reads at 400 Hz but downsamples to the publish rate).
- Use `~/disable` service to pause the node during idle periods without closing the device.

---

## Quick lookup: which path, which board

| Board | IMU chip | Path A (SDK) | Path B (IIO) | GPIO chip/line |
|-------|----------|--------------|-------------|----------------|
| X5 / X5M | BMI088 (40PIN module) | ✅ (direct plug) | ✅ (OS 3.4.x) | chip4/line2 (accel), chip3/line12 (gyro) — defaults |
| X5 / X5M | ICM-42688-P (GS130Wi) | ❌ (SDK doesn't cover) | ✅ (OS 3.4.1+) | N/A (I2C over MIPI) |
| S100 / S100P | BMI088 (40PIN module, jumper wiring) | ✅ | ❌ | **Verify with `gpioinfo`** |
| S100 / S100P | BMI088 (MCU board on-board SPI-5) | ⚠️ (SDK V4.0.2 暂未实现) | ❌ | N/A |
| S600 | BMI088 (40PIN module, jumper wiring) | ✅ | ❌ | **Verify with `gpioinfo`** |
| S600 | BMI088 (MCU board on-board SPI-13) | ✅ (if supported) | ❌ | **Verify with `gpioinfo`** |
| X3 / X3M | — | ❌ (not supported) | ❌ | N/A |
