# Skill Card: bsp-s-series

| Field | Value |
|---|---|
| name | bsp-s-series |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow (reference) |
| riskLevel | low — points to official sources and docs; no direct build commands yet |
| platforms | s-series (S100/S100P/S600) |

## Use case

Guiding S-series BSP source acquisition and build setup while keeping X/S platform isolation intact.

Require the exact S board/chip and intended artifact. X3/X5 manifests, image configs, toolchains, and commands are not interchangeable; keep S source acquisition separate from generic `bsp-source-sync`.

## Known risks

- Fabricating S-series build commands before the source package is at hand — this skill deliberately defers to official docs.
- Users reusing X-series commands on S boards; the skill must block that explicitly.
- A proposed X5 command for S100/S600 must be rejected before any build guidance.
- Download center access needs a developer account; credentials are the user's responsibility.

## Sources

- `rdk_s_doc` §1.6 资源汇总 / §7.2.1 开发环境搭建 / §7.6 构建系统开发指南
- 用户指定入口：`https://developer.d-robotics.cc/resource`
