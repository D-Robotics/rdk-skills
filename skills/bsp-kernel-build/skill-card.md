# Skill Card: bsp-kernel-build

| Field | Value |
|---|---|
| name | bsp-kernel-build |
| owner | D-Robotics BSP Team |
| license | Apache-2.0 |
| kind | workflow |
| riskLevel | high — long CPU-heavy build; incorrect kernel/DTB deployment can make the target board unbootable |
| platforms | x-series (X3/X5) |

## Use case

Kernel/DTB/driver-module/RT customization and prerequisite artifacts for the
`hobot-*` kernel-related deb packages. It does not create a complete image or
deploy artifacts to a board.

## Known risks

- Forgetting the prerequisite full image build leads to missing headers/deps — always check first.
- `mk_kernel_rt.sh` (X5) produces a real-time kernel with different scheduling behavior.
- Untracked kernel config changes silently ship into the image; require visible diffs before building.
- A board-family or DTS/config mismatch can produce an unusable artifact; require
  the X3/X5 board variant, target (`kernel`/`DTB`/`module`/`RT`), and exact
  configuration source.
- Replacing boot-partition artifacts or rebooting can make the board unbootable;
  require the deployment target, backup/rollback method, and explicit
  confirmation before those actions.

## Routing

- Complete flashable/release image: `bsp-image-build`.
- `hobot-*` package creation or rebuild: `bsp-deb-build` after kernel artifacts
  are available.

## Sources

- `x5-rdk-gen` README v3.5.0「编译 kernel」
- `rdk-gen` README v3.0.3「编译 kernel」
