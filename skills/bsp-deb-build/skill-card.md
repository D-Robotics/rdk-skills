# Skill Card: bsp-deb-build

| Field | Value |
|---|---|
| name | bsp-deb-build |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | medium — repackaging system components that may end up on boards |
| platforms | x-series (X3/X5) |

## Use case

Repackaging one supported modified `hobot-*` component for a stated consumer: a compatible on-board install or a later image build.

## Required request context

- Exact supported package name
- Target board and BSP source branch/release
- Intended artifact consumer (on-board install or `bsp-image-build`)
- Available free disk space

`mk_debs.sh` produces `.deb` packages in `deploy/deb_pkgs/`; it does not produce a flashable image. When the consumer is a release image, verify the package exists and then hand off to `bsp-image-build` for image assembly.

## Known risks

- Dirty source trees leak uncommitted changes into packages.
- Packages are board-specific; an X5-built deb can break an X3 image and vice versa.
- `mk_debs.sh` only supports the documented package list; extending it is a source change, not a CLI tweak.
- A package name outside the supported list requires the user to select a supported target or inspect build metadata; do not invent a command.

## Sources

- `x5-rdk-gen` README v3.5.0「编译 RDK 官方 debian 软件包」
- `rdk-gen` README v3.0.3「编译 debian 软件包」
