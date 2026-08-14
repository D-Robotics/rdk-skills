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

Repackaging modified `hobot-*` components and feeding them back into images or on-board installs.

## Known risks

- Dirty source trees leak uncommitted changes into packages.
- Packages are board-specific; an X5-built deb can break an X3 image and vice versa.
- `mk_debs.sh` only supports the documented package list; extending it is a source change, not a CLI tweak.

## Sources

- `x5-rdk-gen` README v3.5.0「编译 RDK 官方 debian 软件包」
- `rdk-gen` README v3.0.3「编译 debian 软件包」
