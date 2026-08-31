# Skill Card: bsp-rootfs-custom

| Field | Value |
|---|---|
| name | bsp-rootfs-custom |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | medium — sudo rootfs generation, changes propagate into all images |
| platforms | x-series (X3/X5) |

## Use case

Custom samplefs with a tailored package set, users, and autostart services.

Collect the base rootfs, board/image variant, exact targets, backup location, and size goal first. Deletions require a dry-run/listing and explicit confirmation; changed `hobot-*` sources route to `bsp-deb-build`.

## Known risks

- Package-list edits silently change every future image; diffs must be reviewed.
- Hand-editing the generated rootfs breaks reproducibility — fixes belong in the source scripts.
- Desktop vs server outputs differ (`samplefs_desktop…` vs `samplefs_server…`); quoting the wrong artifact confuses downstream steps.
- A removal without a candidate list, backup, and confirmation can affect every subsequent image.

## Sources

- `x5-rdk-gen` README v3.5.0「Ubuntu 文件系统制作」
- `rdk-gen` README v3.0.3「制作 Ubuntu 文件系统」
