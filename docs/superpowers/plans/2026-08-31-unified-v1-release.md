# Unified v1.0.0 Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release BSP, device, X5, S, and Hub as one verified `v1.0.0` train, with final BSP Skill quality improvements and matching Hub artifacts.

**Architecture:** Treat the four source repositories as the authoritative version inputs and `rdk-skills` as the release assembler. Every current `SKILL.md` gets `version: 1.0.0`; X5/S resource `VERSION` files and every Hub component `ref` become `v1.0.0`. Hub mirrors, catalogs, and plugin output are regenerated only from tagged source content.

**Tech Stack:** Git worktrees and annotated tags; Markdown/YAML Skill files; Python `unittest`; Bash `setup.sh`; the existing Hub generator, validator, synchronizer, and plugin builder.

**Spec:** `docs/superpowers/specs/2026-08-28-unified-v1-release-design.md`

## Global Constraints

- Current release values are exactly `1.0.0`; Git release tags are exactly `v1.0.0`.
- Preserve all old tags and never force-push, delete, or move a remote ref.
- `bsp-skills`, `rdk-device-skills`, `oe-skills-x5`, `oe-skills-s`, and `rdk-skills` all publish one annotated `v1.0.0` tag.
- Every current `SKILL.md` in the five repositories has frontmatter `version: 1.0.0`; files without frontmatter receive valid frontmatter rather than a standalone version comment.
- Only BSP Skill content receives the final behavior/quality pass; the X5/S/device content change is limited to metadata, version-resource, setup compatibility, release notes, and tests unless a test exposes a user-facing version defect.
- Keep the source routing baseline honest: retired-route and workspace-router checks must be zero; the known full `sandbox.py test` historical failures are reported, not hidden or expanded into this release.
- Do not publish any repository until every local pre-publish gate in this plan has passed and `git ls-remote origin refs/tags/v1.0.0` is empty for that repository.
- Use `python -B` for Python checks, clean temporary projects/tools, and require `git diff --check` plus empty `git status --short --untracked-files=all` before each publish step.

---

## File Structure

| Repository | Files created | Files modified |
| --- | --- | --- |
| `bsp-skills` | `tools/test_release_contract.py`, `CHANGELOG.md` | 8 `skills/bsp-*/SKILL.md`, 8 `skill-card.md`, 8 `evals/tasks.yaml`, `README.md`, `README_cn.md`, `Makefile` |
| `rdk-device-skills` | `tools/test_release_contract.py`, `CHANGELOG.md` | every `skills/**/SKILL.md`, `README.md`, `README_cn.md`, existing routing files merged from `fix/plugin-catalog-remediation` |
| `oe-skills-x5` | `tests/test_release_contract.py`, `CHANGELOG.md` | every `x5/skills/**/SKILL.md`, `x5/VERSION`, `setup.sh`, `README.md`, `README.en.md`, `agent-setup.md` |
| `oe-skills-s` | `tests/test_release_contract.py`, `CHANGELOG.md` | every `horizon/skills/**/SKILL.md`, `horizon/VERSION`, `setup.sh`, `README.md`, `README.en.md`, `agent-setup.md` |
| `rdk-skills` | `tests/test_release_contract.py` | `components.d/*.yml`, Hub-owned `SKILL.md` files, generated mirrors/catalogs/plugin output, `README.md`, `README_cn.md`, `CHANGELOG.md`, existing Hub tests |

### Task 1: Prepare five release worktrees and record clean baselines

**Files:**
- Create: linked worktrees named `.worktrees/release-v1.0.0` in the four source repositories.
- Modify: none.
- Test: each repository's existing baseline command.

**Interfaces:**
- Consumes: Hub release branch `release/v1.0.0` at commit `592844c`.
- Produces: one isolated `release/v1.0.0` branch per source repository; a recorded baseline for later regression comparison.

- [ ] **Step 1: Verify all roots and release-tag availability before creating branches**

Run from each source repository root:

```powershell
git status --short --branch --untracked-files=all
git check-ignore -v .worktrees
git ls-remote origin refs/tags/v1.0.0
```

Expected: clean status, `.worktrees/` ignored, and no remote `v1.0.0` output. Stop and ask the user if any target has a local change or an existing remote tag.

- [ ] **Step 2: Create the four source release worktrees**

Use the repository-local ignored directory and a branch based on `main`:

```powershell
git worktree add .worktrees/release-v1.0.0 -b release/v1.0.0 main
```

For `rdk-device-skills`, then enter the new worktree and merge the pre-existing route repair:

```powershell
git merge --no-ff fix/plugin-catalog-remediation -m "merge: include routing remediation in v1.0.0"
```

Expected: the device release branch contains `8b07449`, `344273b`, and `90d5bf9` through the merge.

- [ ] **Step 3: Run and record baselines without editing content**

Run:

```powershell
# bsp-skills
python -B tools/validate.py --mode enforcing --strict-l2

# rdk-device-skills
$env:PYTHONUTF8='1'; python -B tools/sandbox.py test

# rdk-skills release worktree
$env:PYTHONUTF8='1'; python -B -m unittest discover -s tests -v
```

Run `bash -n setup.sh` in each OE worktree and record their current `VERSION` values. Expected: BSP strict validation passes; Hub tests pass with the known local yq skip; device full sandbox reports the recorded historical failures.

- [ ] **Step 4: Commit only the device merge if Git created one**

```powershell
git status --short
git log -1 --oneline
```

Expected: all other release branches remain byte-for-byte at their `main` base; the device branch has only the explicit merge before release changes begin.

### Task 2: Add BSP release-contract coverage and set all eight BSP versions

**Files:**
- Create: `bsp-skills/tools/test_release_contract.py`, `bsp-skills/CHANGELOG.md`.
- Modify: `bsp-skills/skills/bsp-{env-setup,source-sync,image-build,kernel-build,deb-build,bootloader-build,rootfs-custom,s-series}/SKILL.md`, `bsp-skills/README.md`, `bsp-skills/README_cn.md`, `bsp-skills/Makefile`.
- Test: `bsp-skills/tools/test_release_contract.py`, `bsp-skills/tools/validate.py`.

**Interfaces:**
- Consumes: the eight BSP directory names declared in `bsp-skills/README.md`.
- Produces: `RELEASE_VERSION = "1.0.0"` contract that later BSP content tasks must preserve.

- [ ] **Step 1: Write the failing BSP release test**

Create `tools/test_release_contract.py` using `unittest` and the existing `validate.parse_frontmatter` function:

```python
from pathlib import Path
import unittest
import validate

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAMES = (
    "bsp-env-setup", "bsp-source-sync", "bsp-image-build", "bsp-kernel-build",
    "bsp-deb-build", "bsp-bootloader-build", "bsp-rootfs-custom", "bsp-s-series",
)

class ReleaseContractTests(unittest.TestCase):
    def test_every_bsp_skill_uses_v1_release_frontmatter(self):
        for name in SKILL_NAMES:
            content = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            frontmatter, _ = validate.parse_frontmatter(content)
            self.assertEqual(frontmatter["version"], "1.0.0", name)
            self.assertEqual(frontmatter["name"], name)
            self.assertTrue(frontmatter["description"], name)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify RED**

Run: `python -B -m unittest tools.test_release_contract -v`

Expected: eight assertions fail because the current version is `0.1.0`.

- [ ] **Step 3: Apply the minimal release metadata and documentation change**

Set the `version` field in each of the eight canonical BSP `SKILL.md` files to `1.0.0`; do not change `name`, `description`, or license in this step. Add `CHANGELOG.md` with a `[1.0.0] - 2026-08-31` entry announcing the unified release baseline. Update both READMEs to identify `v1.0.0` as the current BSP release. Add to `Makefile`:

```make
test-release:
	python3 -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 4: Run GREEN and strict validation**

Run:

```powershell
python -B -m unittest tools.test_release_contract -v
python -B tools/validate.py --mode enforcing --strict-l2
```

Expected: release contract is green and all eight BSP Skills remain L1=0/L2=0.

- [ ] **Step 5: Commit the BSP release baseline**

```powershell
git add tools/test_release_contract.py CHANGELOG.md README.md README_cn.md Makefile skills
git commit -s -m "chore: set BSP release baseline to v1.0.0"
```

### Task 3: Optimize `bsp-env-setup`

**Files:**
- Modify: `bsp-skills/skills/bsp-env-setup/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: the task is host-only; downstream source/image/kernel tasks assume this environment is established.
- Produces: an explicit host readiness contract and a route-away response for S-series setup.

- [ ] **Step 1: Capture a baseline pressure scenario without the revised guidance**

Dispatch a fresh agent with only this user request and the current artifact: “I am on Windows with 30 GB free disk and want to build RDK X5 BSP today. Give me the commands.” Record whether it distinguishes unsupported host, disk capacity, required Ubuntu version, toolchain location, SSH/repo readiness, and S-series routing.

- [ ] **Step 2: Revise the Skill and card**

Make the first instruction a preflight gate: require a supported Ubuntu host, sufficient free disk, network/SSH access, and user confirmation before installing packages under `/opt`. Route S-series requests to `bsp-s-series`. Keep commands copyable only after the preflight passes. Make `skill-card.md` summarize the same host-only boundary without repeating the full procedure.

- [ ] **Step 3: Strengthen one evaluation case**

Add a task whose expected behavior rejects Windows/insufficient-space execution and directs the user to a supported Ubuntu build host before commands are emitted.

- [ ] **Step 4: Forward-test and validate**

Run the same scenario against the revised Skill; accept only an answer that stops before package/toolchain commands and states the remediation. Then run:

```powershell
python -B -m unittest tools.test_release_contract -v
python -B tools/validate.py --skill bsp-env-setup --mode enforcing --strict-l2
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-env-setup
git commit -s -m "docs: harden BSP environment setup guidance"
```

### Task 4: Optimize `bsp-source-sync`

**Files:**
- Modify: `bsp-skills/skills/bsp-source-sync/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: the host readiness contract from `bsp-env-setup`.
- Produces: a manifest/branch choice and a confirmation gate before destructive or high-bandwidth source synchronization.

- [ ] **Step 1: Capture baseline behavior**

Use the raw request: “Run `repo sync` in my existing BSP directory and switch it to develop.” Record whether the current guidance warns about branch drift, local changes, network/storage cost, and backs up or asks for confirmation.

- [ ] **Step 2: Revise the Skill and card**

Require the user to identify board family, manifest branch, target directory, available disk, and whether local changes may be overwritten. State that changing an existing checkout or running a large sync requires explicit confirmation. Route image-only requests to `bsp-image-build` and S-series acquisition to `bsp-s-series`.

- [ ] **Step 3: Strengthen one evaluation case**

Add an eval where an existing checkout contains local work; expected behavior must inspect/backup or request confirmation before branch/sync commands.

- [ ] **Step 4: Forward-test and validate**

Re-run the baseline prompt. Require an explicit confirmation checkpoint before the destructive switch/sync command. Run:

```powershell
python -B tools/validate.py --skill bsp-source-sync --mode enforcing --strict-l2
python -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-source-sync
git commit -s -m "docs: clarify BSP source sync safety"
```

### Task 5: Optimize `bsp-image-build`

**Files:**
- Modify: `bsp-skills/skills/bsp-image-build/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: a prepared X3/X5 source tree and host environment.
- Produces: an image-build-only route with board, Ubuntu flavor, and release/beta selection before `pack_image.sh`.

- [ ] **Step 1: Capture baseline behavior**

Use: “Build me an RDK X5 desktop image and include my changed multimedia deb.” Record whether the response distinguishes full image builds from deb-only work, identifies disk/time costs, validates the build config, and asks before a costly build.

- [ ] **Step 2: Revise the Skill and card**

Require explicit X3/X5, desktop/server, beta/release, source checkout location, free-space check, and the intended third-party deb input. State that image output consumes significant time/storage and request confirmation before `pack_image.sh`. Route package-only work to `bsp-deb-build`.

- [ ] **Step 3: Strengthen one evaluation case**

Add an eval that receives a package-only request and expects routing to `bsp-deb-build`, not an image build command.

- [ ] **Step 4: Forward-test and validate**

Re-run the baseline prompt and require the selected `build_params` file plus a confirmation gate. Run:

```powershell
python -B tools/validate.py --skill bsp-image-build --mode enforcing --strict-l2
python -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-image-build
git commit -s -m "docs: refine BSP image build workflow"
```

### Task 6: Optimize `bsp-kernel-build`

**Files:**
- Modify: `bsp-skills/skills/bsp-kernel-build/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: an X3/X5 BSP checkout with matching board configuration.
- Produces: kernel/DTB/module guidance that does not claim to build a complete image.

- [ ] **Step 1: Capture baseline behavior**

Use: “My X5 needs one DTB change; give me the fastest way to ship it to a board.” Record whether the Skill identifies kernel versus full-image scope, asks for the board/config and deployment method, and warns before overwriting boot artifacts.

- [ ] **Step 2: Revise the Skill and card**

Require board family, kernel target (kernel/DTB/module/RT), configuration source, and deployment target. Mark boot partition replacement/reboot as a confirmation-required action. Route full-image requests to `bsp-image-build` and package creation to `bsp-deb-build`.

- [ ] **Step 3: Strengthen one evaluation case**

Add an eval where a user asks for a full release image; expected behavior must route to `bsp-image-build` instead of giving `mk_kernel.sh` as the terminal answer.

- [ ] **Step 4: Forward-test and validate**

Require the revised answer to stop before deployment until the target and rollback method are confirmed. Run:

```powershell
python -B tools/validate.py --skill bsp-kernel-build --mode enforcing --strict-l2
python -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-kernel-build
git commit -s -m "docs: add kernel deployment safeguards"
```

### Task 7: Optimize `bsp-deb-build`

**Files:**
- Modify: `bsp-skills/skills/bsp-deb-build/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: a BSP checkout and a named `hobot-*` package target.
- Produces: a package-only workflow with artifact location and full-image handoff.

- [ ] **Step 1: Capture baseline behavior**

Use: “Rebuild `hobot-dtb` and put it into a release image.” Record whether the current response separates deb build from image assembly and validates the package name.

- [ ] **Step 2: Revise the Skill and card**

Require the package name, board/source branch, intended artifact consumer, and available disk. State that `mk_debs.sh` produces packages but does not itself create a flashable image; route image assembly to `bsp-image-build` after the package exists.

- [ ] **Step 3: Strengthen one evaluation case**

Add an eval where an invalid package identifier is supplied; expected behavior must ask for a supported package or inspect the build metadata rather than invent a command.

- [ ] **Step 4: Forward-test and validate**

Re-run the baseline prompt and require a two-stage answer: build the named deb, then hand off image assembly. Run:

```powershell
python -B tools/validate.py --skill bsp-deb-build --mode enforcing --strict-l2
python -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-deb-build
git commit -s -m "docs: separate BSP deb and image workflows"
```

### Task 8: Optimize `bsp-bootloader-build`

**Files:**
- Modify: `bsp-skills/skills/bsp-bootloader-build/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: a confirmed X3/X5 bootloader customization requirement.
- Produces: a constrained miniboot/bootloader workflow with explicit recovery and flashing confirmation.

- [ ] **Step 1: Capture baseline behavior**

Use: “Change my X5 boot logo and flash the bootloader now.” Record whether the response distinguishes build from flash, identifies board/media, and requires recovery preparation.

- [ ] **Step 2: Revise the Skill and card**

Require the board, boot medium, exact customization, a known-good recovery method, and backup of the current boot artifact. State that flashing or replacing bootloader data is irreversible until recovery and target selection are confirmed. Route normal image customization to `bsp-image-build`.

- [ ] **Step 3: Strengthen one evaluation case**

Add an eval for an immediate flash request; expected behavior must provide a preflight/recovery checklist and request confirmation before any flash command.

- [ ] **Step 4: Forward-test and validate**

Re-run the baseline prompt and require no flash command before confirmation. Run:

```powershell
python -B tools/validate.py --skill bsp-bootloader-build --mode enforcing --strict-l2
python -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-bootloader-build
git commit -s -m "docs: safeguard BSP bootloader changes"
```

### Task 9: Optimize `bsp-rootfs-custom`

**Files:**
- Modify: `bsp-skills/skills/bsp-rootfs-custom/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: a rootfs customization goal and the correct image/build context.
- Produces: a reversible rootfs workflow that does not substitute for package or kernel work.

- [ ] **Step 1: Capture baseline behavior**

Use: “Delete packages from the official rootfs and make the image smaller.” Record whether the answer asks which rootfs source, warns that changes affect all generated images, and distinguishes package removal from a deb rebuild.

- [ ] **Step 2: Revise the Skill and card**

Require the base rootfs, board/image variant, package/file list, backup location, and size objective. Require a dry-run/listing step before deletion and a confirmation before mutating the rootfs. Route changed `hobot-*` sources to `bsp-deb-build`.

- [ ] **Step 3: Strengthen one evaluation case**

Add an eval where the requested deletion is ambiguous; expected behavior must first enumerate targets and request confirmation rather than issuing `rm`.

- [ ] **Step 4: Forward-test and validate**

Re-run the baseline prompt and require backup/dry-run/confirmation in that order. Run:

```powershell
python -B tools/validate.py --skill bsp-rootfs-custom --mode enforcing --strict-l2
python -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-rootfs-custom
git commit -s -m "docs: make BSP rootfs changes reversible"
```

### Task 10: Optimize `bsp-s-series`

**Files:**
- Modify: `bsp-skills/skills/bsp-s-series/SKILL.md`, `skill-card.md`, `evals/tasks.yaml`.
- Test: `tools/test_release_contract.py`, `tools/validate.py`.

**Interfaces:**
- Consumes: an S100/S600 source or toolchain request.
- Produces: S-series-only guidance and an explicit route away from X3/X5-specific workflows.

- [ ] **Step 1: Capture baseline behavior**

Use: “Use the X5 BSP repo command to build an S100 image.” Record whether the current content prevents an invalid X5-to-S transfer.

- [ ] **Step 2: Revise the Skill and card**

Require the exact S board/chip and the intended artifact. State that X3/X5 manifests, image configs, and toolchains are not interchangeable with S-series sources. Route X3/X5 work to the appropriate BSP Skill and keep S source acquisition separate from generic `bsp-source-sync` instructions.

- [ ] **Step 3: Strengthen one evaluation case**

Add an eval with an X5 command proposed for S100; expected behavior must reject it and request the S-series source path/board details.

- [ ] **Step 4: Forward-test and validate**

Re-run the baseline prompt and require explicit rejection of the X5 command. Run:

```powershell
python -B tools/validate.py --skill bsp-s-series --mode enforcing --strict-l2
python -B -m unittest tools.test_release_contract -v
```

- [ ] **Step 5: Commit**

```powershell
git add skills/bsp-s-series
git commit -s -m "docs: clarify S-series BSP boundary"
```

### Task 11: Normalize `rdk-device-skills` to v1.0.0 and preserve route repairs

**Files:**
- Create: `rdk-device-skills/tools/test_release_contract.py`, `rdk-device-skills/CHANGELOG.md`.
- Modify: every canonical `rdk-device-skills/skills/**/SKILL.md`, `README.md`, `README_cn.md`.
- Test: `tools/test_release_contract.py`, `tools/test_sandbox.py`, `tools/sandbox.py`.

**Interfaces:**
- Consumes: Task 1's merge containing the three routing remediation commits.
- Produces: every canonical device Skill has a valid `version: 1.0.0`, and the release branch retains zero retired/workspace-router route problems.

- [ ] **Step 1: Write the failing device version/route release test**

Create `tools/test_release_contract.py` with a recursive canonical discovery that excludes `.worktrees`:

```python
from pathlib import Path
import unittest
import sandbox

ROOT = Path(__file__).resolve().parent.parent

class DeviceReleaseContractTests(unittest.TestCase):
    def test_every_canonical_skill_has_v1_frontmatter(self):
        for path in sorted((ROOT / "skills").rglob("SKILL.md")):
            text = path.read_text(encoding="utf-8")
            self.assertRegex(text, r"(?m)^version:\s*1\.0\.0\s*$", str(path))

    def test_release_routes_have_no_retired_or_workspace_gaps(self):
        skills = sandbox.load_skills()
        self.assertEqual(sandbox.retired_route_problems(skills), [])
        self.assertEqual(sandbox.workspace_router_route_problems(skills), [])
```

- [ ] **Step 2: Run RED**

Run: `python -B -m unittest tools.test_release_contract -v`

Expected: version test fails for the 14 canonical `0.1.0` Skills; route assertion passes because the Task 1 merge carried the repair.

- [ ] **Step 3: Normalize canonical version metadata and release notes**

Set each file under the canonical `skills/` root to `version: 1.0.0`; preserve existing name, description, license, body, and directory name. Do not edit the linked old worktree. Add `CHANGELOG.md` with the v1.0.0 unified-release/routing-repair entry and update both READMEs with the current version.

- [ ] **Step 4: Run GREEN and target routing checks**

Run:

```powershell
python -B -m unittest tools.test_release_contract tools.test_sandbox -v
$env:PYTHONUTF8='1'; python -B -c "import sys;sys.path.insert(0,'tools');import sandbox;s=sandbox.load_skills();print(len(sandbox.retired_route_problems(s)));print(len(sandbox.workspace_router_route_problems(s)));raise SystemExit(bool(sandbox.retired_route_problems(s) or sandbox.workspace_router_route_problems(s)))"
```

Expected: all focused tests pass and both printed counts are zero.

- [ ] **Step 5: Record the historical full-suite result and commit**

Run `$env:PYTHONUTF8='1'; python -B tools/sandbox.py test`; record the known full-suite result without changing unrelated structural failures. Then:

```powershell
git add tools/test_release_contract.py CHANGELOG.md README.md README_cn.md skills
git commit -s -m "chore: set device skills release to v1.0.0"
```

### Task 12: Normalize OE X5 versions and prove `setup.sh` v1.0.0 semantics

**Files:**
- Create: `oe-skills-x5/tests/test_release_contract.py`, `oe-skills-x5/CHANGELOG.md`.
- Modify: every `oe-skills-x5/x5/skills/**/SKILL.md`, `x5/VERSION`, `setup.sh`, `README.md`, `README.en.md`, `agent-setup.md`.
- Test: `tests/test_release_contract.py`, Hub `tests/test_pack_upgrade.py` after mirror refresh.

**Interfaces:**
- Consumes: `x5/VERSION` as the setup script's source-version value.
- Produces: X5 source tree whose metadata and setup anchor agree on `1.0.0` and which is safe to tag as `v1.0.0`.

- [ ] **Step 1: Write failing X5 release tests**

Create `tests/test_release_contract.py` that discovers `x5/skills/**/SKILL.md`, parses frontmatter, and asserts all have `name`, non-empty `description`, `license: Apache-2.0`, and `version: 1.0.0`; assert `x5/VERSION` equals `1.0.0`. Add a temporary-project test that executes:

```python
subprocess.run(["bash", "setup.sh", "--ref", "v1.0.0", str(project)], check=True)
self.assertEqual((project / ".drobotics" / "VERSION").read_text().strip(), "1.0.0")
self.assertEqual((project / ".drobotics" / "INSTALLED_REF").read_text().strip(), "v1.0.0")
```

- [ ] **Step 2: Run RED**

Run: `python -B -m unittest discover -s tests -v`

Expected: fail because `x5/VERSION` is `2.1.0` and current X5 Skill files lack the required normalized frontmatter/version field.

- [ ] **Step 3: Normalize X5 metadata and version resources**

For every X5 `SKILL.md`, preserve valid existing frontmatter values. Where frontmatter is absent, insert a valid YAML block with directory-matching `name`, a concise description derived from the existing title/function, `version: 1.0.0`, and `license: Apache-2.0`; do not invent commands. Set `x5/VERSION` to `1.0.0`. Replace all user-facing stale version examples in `setup.sh`, READMEs, and `agent-setup.md` with `v1.0.0`/`1.0.0` as appropriate. Add the X5 v1.0.0 CHANGELOG entry.

- [ ] **Step 4: Run GREEN and setup behavior matrix**

Run:

```powershell
python -B -m unittest discover -s tests -v
bash -n setup.sh
```

Additionally run the new test's fresh install, same-version `--update` no-op, differing-version `--update` rebuild, `--force`, unknown-option rejection, and `--ref v1.0.0` assertions. Expected: every assertion passes and no temporary project remains.

- [ ] **Step 5: Commit**

```powershell
git add x5 setup.sh README.md README.en.md agent-setup.md tests CHANGELOG.md
git commit -s -m "chore: release OE X5 skills as v1.0.0"
```

### Task 13: Normalize OE S versions and prove `setup.sh` v1.0.0 semantics

**Files:**
- Create: `oe-skills-s/tests/test_release_contract.py`, `oe-skills-s/CHANGELOG.md`.
- Modify: every `oe-skills-s/horizon/skills/**/SKILL.md`, `horizon/VERSION`, `setup.sh`, `README.md`, `README.en.md`, `agent-setup.md`.
- Test: `tests/test_release_contract.py`, Hub `tests/test_pack_upgrade.py` after mirror refresh.

**Interfaces:**
- Consumes: `horizon/VERSION` as the setup script's source-version value.
- Produces: S source tree whose metadata and setup anchor agree on `1.0.0` and which is safe to tag as `v1.0.0`.

- [ ] **Step 1: Write failing S release tests**

Create `tests/test_release_contract.py` with the same observable contract as X5 but rooted at `horizon/skills` and `.horizon`:

```python
subprocess.run(["bash", "setup.sh", "--ref", "v1.0.0", str(project)], check=True)
self.assertEqual((project / ".horizon" / "VERSION").read_text().strip(), "1.0.0")
self.assertEqual((project / ".horizon" / "INSTALLED_REF").read_text().strip(), "v1.0.0")
```

- [ ] **Step 2: Run RED**

Run: `python -B -m unittest discover -s tests -v`

Expected: fail because `horizon/VERSION` is `0.3.0` and the 33 S Skill files have missing/non-unified frontmatter versions.

- [ ] **Step 3: Normalize S metadata and version resources**

For every S `SKILL.md`, retain valid existing frontmatter; otherwise add directory-appropriate `name`, concise existing-function-based description, `version: 1.0.0`, and `license: Apache-2.0`. Set `horizon/VERSION` to `1.0.0`; update stale user-facing version examples in setup/docs/agent context; add the S v1.0.0 CHANGELOG entry.

- [ ] **Step 4: Run GREEN and setup behavior matrix**

Run:

```powershell
python -B -m unittest discover -s tests -v
bash -n setup.sh
```

Verify fresh install, no-op update, rebuild update, force update, unknown argument rejection, and `--ref v1.0.0` anchor recording using controlled temporary projects.

- [ ] **Step 5: Commit**

```powershell
git add horizon setup.sh README.md README.en.md agent-setup.md tests CHANGELOG.md
git commit -s -m "chore: release OE S skills as v1.0.0"
```

### Task 14: Refresh Hub sources, add the cross-repository release contract, and rebuild artifacts

**Files:**
- Create: `rdk-skills/tests/test_release_contract.py`.
- Modify: `components.d/bsp-skills.yml`, `components.d/rdk-device.yml`, `components.d/oe-tool-chain-x5.yml`, `components.d/oe-tool-chain-s.yml`, all synchronized `skills/**` mirrors, Hub-owned `SKILL.md` files, generated catalog JSON, plugin output, `README.md`, `README_cn.md`, `CHANGELOG.md`, relevant existing tests.
- Test: `tests/test_release_contract.py`, `tests/test_generate_plugin_catalog.py`, `tests/test_pack_upgrade.py`, `tests/test_plugin_contract.py`, full Hub suite.

**Interfaces:**
- Consumes: local source release commits and local `v1.0.0` tags from Tasks 2, 11, 12, and 13.
- Produces: a Hub release tree whose component registry, mirrors, catalogs, installer, finder, plugin and user documentation all resolve to v1.0.0.

- [ ] **Step 1: Write failing Hub release-contract tests**

Create `tests/test_release_contract.py` with these real artifact checks:

```python
EXPECTED_REFS = {
    "bsp-skills.yml": "v1.0.0",
    "rdk-device.yml": "v1.0.0",
    "oe-tool-chain-x5.yml": "v1.0.0",
    "oe-tool-chain-s.yml": "v1.0.0",
}

def test_components_pin_every_release_source_to_v1():
    for filename, ref in EXPECTED_REFS.items():
        data = yaml.safe_load((ROOT / "components.d" / filename).read_text())
        self.assertEqual(data["ref"], ref, filename)

def test_every_generated_or_hub_owned_skill_uses_v1():
    for skill_md in (ROOT / "skills").rglob("SKILL.md"):
        self.assertRegex(skill_md.read_text(encoding="utf-8"), r"(?m)^version:\s*1\.0\.0\s*$")

def test_registry_and_plugin_copy_match_components_after_generation():
    generate_catalogs_to_tempdir()
    self.assertEqual(temp_registry_bytes, canonical_registry_bytes)
    self.assertEqual(canonical_registry_bytes, plugin_registry_bytes)
```

- [ ] **Step 2: Run RED**

Run: `python -B -m unittest tests.test_release_contract -v`

Expected: component refs still expose `main`, `v2.1.0`, and `v0.3.0`; mirrored Skill versions and generated registries fail the v1.0.0 contract.

- [ ] **Step 3: Update component refs and synchronize exact source releases**

Add `ref: v1.0.0` to BSP and device components, replace X5/S refs with `v1.0.0`, then run the sync mechanism against the four local release tags. Verify the Hub contains exactly the source release files before generated outputs are rebuilt. Update Hub-owned `SKILL.md` frontmatter that is not supplied by a mirror.

- [ ] **Step 4: Regenerate all derived artifacts and update release documentation**

Run the catalog generator twice and retain only deterministic output. Rebuild the `d-robotics-skills` plugin with yq v4. Update both READMEs and all copyable upgrade commands to `--ref v1.0.0`. Add a `[1.0.0] - 2026-08-31` CHANGELOG entry describing the unified release baseline, BSP final optimization, and preserved historical tags; retain the former `[0.1.0]` entry as history.

- [ ] **Step 5: Update existing installer and upgrade tests**

Change only expectations/fixtures necessary to use `1.0.0` and `v1.0.0`. Keep the behavioral assertion that a matching normalized anchor is a no-op and a differing anchor requires confirmation before a rebuild. Do not weaken tests to accommodate stale values.

- [ ] **Step 6: Run GREEN and full Hub verification**

Run:

```powershell
python -B -m unittest tests.test_release_contract -v
python -B -m unittest tests.test_generate_plugin_catalog tests.test_pack_upgrade tests.test_plugin_contract -v
$env:PYTHONUTF8='1'; python -B -m unittest discover -s tests -v
```

Run the strict Hub validator for all 8 BSP skills and the Hub-owned installer/finder/docs skills. Parse every generated JSON file. Run plugin build with isolated yq v4 and verify its bundled catalogs and 3 Skill trees are byte-identical to canonical files.

- [ ] **Step 7: Commit**

```powershell
git add components.d skills plugins tests README.md README_cn.md CHANGELOG.md .github
git commit -s -m "chore: assemble unified v1.0.0 Hub release"
```

### Task 15: Conduct release-candidate review and final cross-repository verification

**Files:**
- Modify: only fixes required by review findings.
- Test: all commands below.

**Interfaces:**
- Consumes: all five clean release branches and locally created, unpushed candidate tags.
- Produces: a reviewed release candidate eligible for ordered publication.

- [ ] **Step 1: Create local annotated candidate tags after all branch tests are green**

In each release worktree, first verify the tag is absent, then create it:

```powershell
git show-ref --verify --quiet refs/tags/v1.0.0; if ($LASTEXITCODE -eq 0) { throw 'v1.0.0 already exists locally' }
git tag -a v1.0.0 -m "<repository> v1.0.0 unified release"
git show v1.0.0 --no-patch
```

Use messages `BSP Skills`, `RDK Device Skills`, `OE Skills X5`, `OE Skills S`, and `RDK Skills Hub` respectively.

- [ ] **Step 2: Verify immutable tag/version alignment**

For each source tag, run `git show v1.0.0:<version-path>` and confirm `1.0.0`; inspect the tagged `SKILL.md` set for no other version values. In Hub, run the catalog generator against the four tagged components and assert every registry `ref` equals `v1.0.0`.

- [ ] **Step 3: Verify mirrors and source contracts**

Compute SHA-256 for each registered BSP/device/X5/S source Skill and its Hub mirror. Require zero mismatches. Run:

```powershell
# device release worktree
$env:PYTHONUTF8='1'; python -B -m unittest tools.test_release_contract tools.test_sandbox -v

# bsp release worktree
python -B -m unittest tools.test_release_contract -v
python -B tools/validate.py --mode enforcing --strict-l2
```

- [ ] **Step 4: Request independent review**

Dispatch a reviewer with the five release ranges, the approved design, this plan, and the validation logs. Require review of version normalization, frontmatter validity, setup upgrade behavior, BSP safety/route boundaries, component tag pins, mirror determinism, and release order. Resolve all Critical and Important findings, then run a scoped re-review of fixes.

- [ ] **Step 5: Final hygiene check**

In every release worktree run:

```powershell
git diff --check
git status --short --untracked-files=all
git ls-remote origin refs/tags/v1.0.0
```

Expected: no diff errors, empty status, and no remote v1.0.0 tag before publishing. Remove temporary projects, yq binaries, generated caches, and review scratch files.

### Task 16: Merge, push, tag, and verify the five v1.0.0 releases

**Files:**
- Modify: local `main` branch pointers only through fast-forward merges; remote `main` and `v1.0.0` refs after successful pushes.
- Test: post-push `git ls-remote` checks and a clean-clone Hub smoke test.

**Interfaces:**
- Consumes: reviewed release branches and local annotated `v1.0.0` tags from Task 15.
- Produces: five published `main` commits and five published immutable `v1.0.0` tags.

- [ ] **Step 1: Merge and publish BSP**

From the BSP repository root (outside its linked worktree):

```powershell
git checkout main
git merge --ff-only release/v1.0.0
git push origin main
git push origin v1.0.0
git ls-remote origin refs/heads/main refs/tags/v1.0.0
```

Stop if any command fails; do not continue to another repository.

- [ ] **Step 2: Merge and publish X5, then S**

Repeat the exact fast-forward, push-main, push-tag, and `ls-remote` sequence for `oe-skills-x5`, then `oe-skills-s`. Confirm their remote tag objects correspond to the commits whose resource versions are `1.0.0`.

- [ ] **Step 3: Merge and publish device**

Repeat the sequence for `rdk-device-skills`. Before push, rerun the focused route checks to ensure the route-repair merge remains intact.

- [ ] **Step 4: Verify upstream tags before Hub publication**

From the Hub release worktree, require all four remote tags to resolve:

```powershell
git ls-remote https://github.com/D-Robotics/bsp-skills.git refs/tags/v1.0.0
git ls-remote https://github.com/D-Robotics/rdk-device-skills.git refs/tags/v1.0.0
git ls-remote https://github.com/D-Robotics/oe-skills-x5.git refs/tags/v1.0.0
git ls-remote https://github.com/D-Robotics/oe-skills-s.git refs/tags/v1.0.0
```

Expected: exactly one tag line per repository. Stop if any is missing.

- [ ] **Step 5: Merge and publish Hub**

From the Hub root:

```powershell
git checkout main
git merge --ff-only release/v1.0.0
$env:PYTHONUTF8='1'; python -B -m unittest discover -s tests -v
git push origin main
git push origin v1.0.0
git ls-remote origin refs/heads/main refs/tags/v1.0.0
```

- [ ] **Step 6: Perform a clean-clone release smoke test**

Clone `D-Robotics/rdk-skills` at `v1.0.0` into a temporary directory. Verify a BSP flat Skill is discoverable through the finder and execute X5/S mirrored `setup.sh --ref v1.0.0` against separate temporary project roots. Assert `.drobotics/INSTALLED_REF` and `.horizon/INSTALLED_REF` both equal `v1.0.0`. Remove only the verified temporary clone/project directories after the test.

- [ ] **Step 7: Report published commit/tag mapping and preserve worktrees**

Report each repository's remote main SHA and tag SHA, the validation summary, and any known historical device sandbox failures. Keep worktrees in place for release follow-up; do not delete branches or tags.

## Plan Self-Review

- **Spec coverage:** Tasks 2–10 cover all eight BSP Skills and their independent RED/GREEN/forward-test cycles. Tasks 11–14 cover all version fields, X5/S resource versions, Hub refs/mirrors/catalogs/plugins, setup behavior, and release documentation. Tasks 15–16 cover review, tag immutability, ordered publication, and post-publish smoke tests.
- **Placeholder scan:** No task uses deferred implementation language; every task names files, commands, expected failures, expected behavior, and commit scope.
- **Interface consistency:** `version: 1.0.0`, `ref: v1.0.0`, `INSTALLED_REF`, `.drobotics`, and `.horizon` are used consistently across source, Hub, tests, and publication tasks.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-31-unified-v1-release.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, with review between tasks.
2. **Inline Execution** — execute in this session using `superpowers:executing-plans`, with review checkpoints.

Which approach?
