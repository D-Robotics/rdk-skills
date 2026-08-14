# Skill Card: bsp-source-sync

| Field | Value |
|---|---|
| name | bsp-source-sync |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | low — downloads source into the workspace (no system modification) |
| platforms | x-series (X3/X5) |

## Use case

Bootstrapping a fresh BSP workspace or updating an existing one to a new manifest branch.

## Known risks

- X5 vs X3 manifests are different (`x5-manifest` vs `manifest`); a wrong manifest wastes a full sync and confuses later builds.
- Large download (tens of GB) and long runtime; users should confirm disk space.
- `repo` mirror URLs and SSH access are the two most common failure points; the skill must distinguish them in error reports.

## Sources

- `x5-rdk-gen` README v3.5.0「下载源码」
- `rdk-gen` README v3.0.3「下载源码」
