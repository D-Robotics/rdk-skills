# Skill Card: bsp-bootloader-build

| Field | Value |
|---|---|
| name | bsp-bootloader-build |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | high — bootloader changes can brick a board |
| platforms | x-series (X5 documented; X3 pending official docs) |

## Use case

Rebuilding the minimal boot firmware for RDK X5 bootloader customization.

Before build or flash guidance, collect the board, boot medium, exact change, recovery method, and backup location. Normal image customization belongs to `bsp-image-build`; do not emit flash commands until the recovery and target selection are explicitly confirmed.

## Known risks

- A broken miniboot bricks the board — always have the official miniboot image and a recovery path.
- X3 steps are not in the official build README; guessing them risks unbootable hardware.
- `xbuild.sh lunch` configs are board-specific; picking the wrong one produces a wrong boot image.
- Replacing bootloader data is irreversible without a validated recovery path and a backup of the current artifact.

## Sources

- `x5-rdk-gen` README v3.5.0「编译 bootloader」
- 官方 miniboot 下载: `https://archive.d-robotics.cc/downloads/miniboot/`
