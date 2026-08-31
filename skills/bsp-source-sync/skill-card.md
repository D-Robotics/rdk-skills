# Skill Card: bsp-source-sync

| Field | Value |
|---|---|
| name | bsp-source-sync |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | medium — an existing checkout can have its manifest branch and many project revisions changed |
| platforms | x-series (X3/X5) |

## Use case

Bootstrapping a fresh BSP workspace or updating an existing one to a new manifest branch.

## Known risks

- X5 vs X3 manifests are different (`x5-manifest` vs `manifest`); a wrong manifest wastes a full sync and confuses later builds.
- `develop` is rolling and may drift from an existing checkout's project branches; changing it in place requires an explicit confirmation.
- Existing local work can be obscured or conflicted by branch/sync changes; inspect it and obtain permission to preserve it with a backup, commit, or stash before proceeding.
- Large download (tens of GB), long runtime, and substantial network use; users must confirm the target directory and free disk space before synchronization.
- `repo` mirror URLs and SSH access are the two most common failure points; the skill must distinguish them in error reports.

## Sources

- `x5-rdk-gen` README v3.5.0「下载源码」
- `rdk-gen` README v3.0.3「下载源码」
