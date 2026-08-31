# Skill Card: bsp-image-build

| Field | Value |
|---|---|
| name | bsp-image-build |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | medium — long sudo build, large downloads, disk-heavy; explicit confirmation gate |
| platforms | x-series (X3/X5) |

## Use case

Producing a flash-able RDK X3/X5 OS image after explicitly selecting the board,
desktop/server flavor, beta/release channel, prepared source checkout, and any
third-party deb to preinstall. Package-only requests belong to `bsp-deb-build`.

## Required inputs before `pack_image.sh`

- X3 or X5; desktop or server; beta or release.
- Absolute checkout location and an existing matching `build_params` file.
- A checked free-space result (roughly 50 GB minimum), plus `sudo` availability.
- The exact board-compatible third-party `.deb` path, or confirmation that none
  will be included.
- Explicit user confirmation after the selected config and estimated time/storage
  cost have been shown.

## Known risks

- First full build downloads several GB from the official server; interrupted runs leave partial artifacts.
- Wrong config (e.g. rdk-x3 config for an X5 board) builds a mismatched image — verify the config file name before running.
- `third_packages` debs are installed silently into the image; their provenance is the user's responsibility.
- `pack_image.sh` can take substantial time and storage; do not run it before
  the user confirms the selected build plan.

## Sources

- `x5-rdk-gen` README v3.5.0「编译系统镜像」
- `x5-rdk-gen/build_params/` 配置清单
- `rdk-gen` README v3.0.3「编译系统镜像」
