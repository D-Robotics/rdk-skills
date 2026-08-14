# Skill Card: bsp-kernel-build

| Field | Value |
|---|---|
| name | bsp-kernel-build |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | medium — long CPU-heavy build, kernel customization affects the target board |
| platforms | x-series (X3/X5) |

## Use case

Kernel/dtbs/driver customization and the prerequisite builds for the `hobot-*` kernel-related deb packages.

## Known risks

- Forgetting the prerequisite full image build leads to missing headers/deps — always check first.
- `mk_kernel_rt.sh` (X5) produces a real-time kernel with different scheduling behavior.
- Untracked kernel config changes silently ship into the image; require visible diffs before building.

## Sources

- `x5-rdk-gen` README v3.5.0「编译 kernel」
- `rdk-gen` README v3.0.3「编译 kernel」
