# Skill Card: bsp-env-setup

| Field | Value |
|---|---|
| name | bsp-env-setup |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow (environment) |
| riskLevel | medium — installs system packages and a toolchain with sudo |
| platforms | x-series (X3/X5 host development) |

## Use case

Preparing a fresh Ubuntu build machine for RDK X3/X5 BSP work, or repairing a host that fails with missing build tools.

## Known risks

- `sudo apt-get install` changes the host system; needs user confirmation.
- Toolchain download requires network access to `archive.d-robotics.cc`; failures must be reported, not worked around with unofficial sources.
- Ubuntu 18.04/20.04 package lists differ slightly (documented in source READMEs); quoting the 22.04 list for other versions is wrong.

## Sources

- `x5-rdk-gen` README v3.5.0「开发环境」
- `rdk-gen` README v3.0.3「开发环境」
