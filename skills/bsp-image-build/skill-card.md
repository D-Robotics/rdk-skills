# Skill Card: bsp-image-build

| Field | Value |
|---|---|
| name | bsp-image-build |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | medium — long sudo build, large downloads, disk-heavy |
| platforms | x-series (X3/X5) |

## Use case

Producing a flash-able RDK OS image, or refreshing the base artifacts every deep-development workflow depends on.

## Known risks

- First full build downloads several GB from the official server; interrupted runs leave partial artifacts.
- Wrong config (e.g. rdk-x3 config for an X5 board) builds a mismatched image — verify the config file name before running.
- `third_packages` debs are installed silently into the image; their provenance is the user's responsibility.

## Sources

- `x5-rdk-gen` README v3.5.0「编译系统镜像」
- `x5-rdk-gen/build_params/` 配置清单
- `rdk-gen` README v3.0.3「编译系统镜像」
