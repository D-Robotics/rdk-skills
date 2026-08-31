# Skill Card: bsp-env-setup

| Field | Value |
|---|---|
| name | bsp-env-setup |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow (environment) |
| riskLevel | medium — installs system packages and a toolchain with sudo |
| platforms | x-series (X3/X5 host development; Ubuntu 22.04 x86_64) |

## Use case

Preparing a supported Ubuntu 22.04 x86_64 build machine for RDK X3/X5 BSP work, or repairing a host that fails with missing build tools. This is host-only setup; S100/S600 requests belong to `bsp-s-series`.

## Known risks

- `sudo apt-get install` changes the host system; needs user confirmation.
- Do not issue package or toolchain commands until the host is Ubuntu 22.04 x86_64, the planned source/build volume has at least 100 GB free, network/GitHub SSH access is ready, and the user approves `/opt` changes.
- Toolchain download requires network access to `archive.d-robotics.cc`; failures must be reported, not worked around with unofficial sources.
- Windows or a smaller/unverified build volume must be remediated with a supported Ubuntu host before any installation command is supplied.
- Ubuntu 18.04/20.04 package lists differ slightly (documented in source READMEs); quoting the 22.04 list for other versions is wrong.

## Sources

- `x5-rdk-gen` README v3.5.0「开发环境」
- `rdk-gen` README v3.0.3「开发环境」
