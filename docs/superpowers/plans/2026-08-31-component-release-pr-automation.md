# Component Release to Hub PR Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert each published source Release into one reviewable Hub component-upgrade PR, then publish the Hub only through a protected manual workflow.

**Architecture:** Four source workflows send a GitHub App-authenticated `repository_dispatch` event to the Hub. The Hub validates the release, updates one stable bot branch per component, synchronizes generated artifacts, and upserts a PR. A separate Environment-protected workflow creates immutable Hub tags and English Releases after approved PRs merge.

**Tech Stack:** GitHub Actions, GitHub App tokens, GitHub CLI, Bash, Python 3, PyYAML, yq, git, unittest.

**Spec:** `docs/superpowers/specs/2026-08-31-component-release-pr-automation-design.md`

## Global Constraints

- Only published, non-draft, non-prerelease source Releases with tags matching `vMAJOR.MINOR.PATCH` are eligible.
- Use the organization-owned `rdk-release-bot` GitHub App; never use a personal access token.
- The App may create bot branches and PRs only. It may not approve, merge, bypass branch protection, administer repositories, or publish Releases.
- A component has one stable branch: `bot/component-upgrade/<component-id>`.
- Source component tags and Hub versions are independent; all published tags are immutable.
- No workflow may push directly to Hub `main`.
- New files use existing SPDX/copyright headers. Hub Release titles are exactly `RDK Skills vX.Y.Z` and bodies are English.

## File Structure

| File | Responsibility |
| --- | --- |
| `.github/scripts/component_release.py` | Parse and validate events; map a source repo to exactly one component; decide `noop` or `upgrade`. |
| `.github/scripts/sync-components.sh` | Synchronize only selected components at their pinned refs and write a summary JSON file. |
| `.github/scripts/upsert-component-pr.sh` | Update stable bot branches and create or edit component PRs. |
| `.github/scripts/render_hub_release_notes.py` | Render English Hub notes from the template and merged upgrade metadata. |
| `.github/workflows/component-upgrade.yml` | Receive source dispatches and build component PRs. |
| `.github/workflows/reconcile-components.yml` | Read-only scheduled drift audit. |
| `.github/workflows/release-hub.yml` | Protected manual Hub tag and Release workflow. |
| `tests/test_component_release.py` | Validation, workflow contract, and idempotency tests. |
| `tests/test_sync_components.py` | Selective-sync integration test using local bare repositories. |
| `tests/test_render_hub_release_notes.py` | English release-note and mixed component-version tests. |

## Task 1: Configure GitHub App and repository controls

**Systems:** GitHub organization; four source repositories; Hub repository.

**Produces:** A least-privilege App, protected Hub `main`, Auto-merge, and a protected `release` Environment.

- [ ] **Step 1: Register and install the App**

Create `rdk-release-bot` and install it only on `bsp-skills`, `rdk-device-skills`, `oe-skills-x5`, `oe-skills-s`, and `rdk-skills`. Grant sources `Contents: read`; grant Hub `Contents: write`, `Pull requests: write`, and `Metadata: read`; grant no other permissions.

- [ ] **Step 2: Configure scoped credentials**

Add organization Actions variable `RDK_RELEASE_BOT_APP_ID` and secret `RDK_RELEASE_BOT_PRIVATE_KEY`, limited to the five repositories. Confirm forked pull requests cannot access the key.

- [ ] **Step 3: Configure merge and release boundaries**

Require maintainer approval and Hub CI checks on `main`; enable GitHub Auto-merge. Create Environment `release` with required maintainer approval.

- [ ] **Step 4: Verify the App boundary**

Use an App installation token to push a temporary Hub branch. Prove a direct push to protected `main` is rejected. Delete the temporary branch after recording the result.

## Task 2: Implement component-release validation

**Files:**
- Create: `.github/scripts/component_release.py`
- Create: `tests/test_component_release.py`

**Interfaces:**

The module defines immutable `ComponentReleaseEvent` and `UpgradeDecision` dataclasses and these interfaces: `load_components(root: Path) -> list[ComponentRef]`, `validate_release_event(event: ComponentReleaseEvent, component: ComponentRef, verified_target_sha: str | None = None) -> None`, and `decide_upgrade(component: ComponentRef, event: ComponentReleaseEvent, verified_target_sha: str | None = None) -> UpgradeDecision`.

- [ ] **Step 1: Write failing tests**

```python
def test_accepts_registered_published_stable_release(tmp_path):
    event = ComponentReleaseEvent("D-Robotics/bsp-skills", "v1.0.1", "a" * 40,
        "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1", "2026-08-31T00:00:00Z")
    assert decide_upgrade(load_components(tmp_path)[0], event).action == "upgrade"

def test_rejects_unknown_repo_prerelease_and_sha_mismatch(self):
    component = ComponentRef("bsp-skills", "D-Robotics/bsp-skills", "v1.0.0", Path("components.d/bsp-skills.yml"))
    with self.assertRaisesRegex(ValidationError, "unregistered source repository"):
        validate_release_event(ComponentReleaseEvent("D-Robotics/unknown", "v1.0.1", "a" * 40, "https://github.com/D-Robotics/unknown/releases/tag/v1.0.1", "2026-08-31T00:00:00Z"), component)
    with self.assertRaisesRegex(ValidationError, "stable release tag"):
        validate_release_event(ComponentReleaseEvent(component.repo, "v1.0.1-rc.1", "a" * 40, "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1-rc.1", "2026-08-31T00:00:00Z"), component)
    with self.assertRaisesRegex(ValidationError, "target SHA mismatch"):
        validate_release_event(ComponentReleaseEvent(component.repo, "v1.0.1", "b" * 40, "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1", "2026-08-31T00:00:00Z"), component, verified_target_sha="a" * 40)
```

- [ ] **Step 2: Verify the red state**

Run `python -B -m unittest tests/test_component_release.py -v`. Expected: import failure because the module is absent.

- [ ] **Step 3: Implement minimal validation**

Require one matching component YAML, tag regex `^v[0-9]+\.[0-9]+\.[0-9]+$`, a 40-character SHA, matching release URL, and workflow-supplied facts showing the Release is neither draft nor prerelease. Return `noop` only when the component ref exactly equals the incoming tag.

- [ ] **Step 4: Verify and commit**

Run `python -B -m unittest tests/test_component_release.py -v` and `python -B -m unittest tests/test_release_contract.py -v`; both must pass. Commit with `feat: validate component release events`.

## Task 3: Extract selective synchronization

**Files:**
- Create: `.github/scripts/sync-components.sh`
- Create: `tests/test_sync_components.py`
- Modify: `.github/workflows/sync-skills.yml`

**Interface:**

```bash
.github/scripts/sync-components.sh --components-dir components.d --component bsp-skills --repo-base-url https://github.com --work-root .tmp/component-sync --summary-file /tmp/sync-summary.json
```

The JSON summary contains `component_id`, `source_ref`, `source_sha`, `catalog_dirs`, `changed`, and `failure`.

- [ ] **Step 1: Write the failing integration test**

```python
def test_requested_component_sync_prunes_only_its_catalog_tree(tmp_path):
    result = run_sync(tmp_path, component="bsp-skills")
    assert result.returncode == 0
    assert read_summary(result)["components"][0]["component_id"] == "bsp-skills"
    assert not (hub_root / "skills/bsp-env-setup/stale.txt").exists()
    assert hash_tree(hub_root / "skills/rdk-diagnostic") == diagnostic_before
```

- [ ] **Step 2: Verify the red state**

Run `python -B -m unittest tests/test_sync_components.py -v`. Expected: failure because the script is absent.

- [ ] **Step 3: Implement the script**

Move clone, sparse-checkout, rsync, workspace `setup.sh` overlay, and summary collection from `sync-skills.yml`. Restrict `rsync --delete` to selected catalog directories. Reject unknown components, empty source paths, unsafe catalog paths, clone failures, and invalid summary destinations. Clean the work root with a shell trap.

- [ ] **Step 4: Route the current sync workflow through the script**

Replace the embedded clone/copy loop in `.github/workflows/sync-skills.yml`; preserve current catalog, plugin, README, and test gates.

- [ ] **Step 5: Verify and commit**

Run `bash -n .github/scripts/sync-components.sh`, the selective-sync test, and `python -B -m unittest discover -s tests -v`. Commit with `refactor: extract component synchronization`.

## Task 4: Build Hub dispatch-to-PR automation

**Files:**
- Create: `.github/workflows/component-upgrade.yml`
- Create: `.github/scripts/upsert-component-pr.sh`
- Modify: `tests/test_component_release.py`

**Workflow contract:**

```yaml
on:
  repository_dispatch:
    types: [rdk-component-release]
  workflow_dispatch:
    inputs:
      source_repo: { required: true, type: string }
      tag: { required: true, type: string }
      dry_run: { required: true, default: true, type: boolean }
```

- [ ] **Step 1: Write failing workflow-contract tests**

```python
def test_upgrade_workflow_is_dispatch_driven_and_dry_run_safe():
    workflow = read_workflow(".github/workflows/component-upgrade.yml")
    assert "rdk-component-release" in workflow and "dry_run" in workflow
    assert "git push origin main" not in workflow

def test_branch_is_stable_per_component():
    assert branch_for("bsp-skills") == "bot/component-upgrade/bsp-skills"
```

- [ ] **Step 2: Verify the red state**

Run `python -B -m unittest tests/test_component_release.py -v`. Expected: contract tests fail because the workflow is absent.

- [ ] **Step 3: Implement validated dispatch handling**

Generate an App token with `actions/create-github-app-token@v2`; require the expected App actor for dispatch events; query the source Release with `gh api`; verify published/non-draft/non-prerelease/tag/SHA consistency; call `component_release.py`; use a concurrency key based on the source component; exit before mutation for `dry_run` or `noop`.

- [ ] **Step 4: Implement PR upsert**

Update `bot/component-upgrade/<component-id>`, change only its component ref, invoke `sync-components.sh`, regenerate artifacts, run tests, commit/push the bot branch, and create or edit its PR. Apply labels `component-upgrade` and `source:<component-id>`. The PR body lists previous/new tag, source Release URL, SHA, mirrored directories, and test results. Do not use `gh pr merge`.

- [ ] **Step 5: Verify and commit**

Run workflow-contract tests and a real Hub manual dry run for `D-Robotics/bsp-skills` at `v1.0.0`; it must create no branch or PR. Commit with `feat: create Hub PRs for component releases`.

## Task 5: Add source Release notifiers

**Files in BSP, Device, X5, and S:**
- Create: `.github/workflows/notify-hub-release.yml`
- Modify: each source repository's workflow/release contract tests.

**Dispatch payload fields:** `schema_version`, `source_repo`, `tag`, `release_url`, `target_sha`, `published_at`.

- [ ] **Step 1: Write a failing BSP workflow test**

```python
def test_published_release_notifies_hub_with_verified_payload():
    workflow = read_workflow(".github/workflows/notify-hub-release.yml")
    assert "release:" in workflow and "published" in workflow
    assert "rdk-component-release" in workflow
    assert "RDK_RELEASE_BOT_PRIVATE_KEY" in workflow
    assert "github.event.release.prerelease" in workflow
```

- [ ] **Step 2: Verify the red state**

Run BSP's test suite. Expected: the notifier test fails because the workflow is absent.

- [ ] **Step 3: Implement and verify BSP notifier**

Trigger only on `release.published`; reject draft, prerelease, and invalid tags; obtain the App token; resolve the release tag to a 40-character SHA; call the Hub dispatch endpoint with the six declared payload fields. Parse the workflow YAML in the test and run the source suite.

- [ ] **Step 4: Roll out the proven workflow**

Repeat the tested notifier and contract check in Device, X5, and S. Commit separately in each source repository with `ci: notify Hub when a formal release is published`.

## Task 6: Replace scheduled direct writes with reconciliation

**Files:**
- Modify: `.github/workflows/sync-skills.yml`
- Create: `.github/workflows/reconcile-components.yml`
- Modify: `tests/test_component_release.py`

- [ ] **Step 1: Write failing safety tests**

```python
def test_reconciliation_cannot_push_or_create_prs():
    workflow = read_workflow(".github/workflows/reconcile-components.yml")
    assert "schedule:" in workflow
    assert "git push" not in workflow and "gh pr create" not in workflow

def test_legacy_sync_has_no_schedule_or_direct_commit():
    workflow = read_workflow(".github/workflows/sync-skills.yml")
    assert "schedule:" not in workflow
    assert "Commit and push changes" not in workflow
```

- [ ] **Step 2: Verify the red state**

Run `python -B -m unittest tests/test_component_release.py -v`. Expected: assertions fail against the current hourly direct-write workflow.

- [ ] **Step 3: Implement read-only reconciliation**

Use the selective-sync verification path in a temporary checkout to compare pinned source refs, mirrors, catalogs, and plugins. On drift or invalid references, create/update an issue labeled `component-upgrade-failure`; do not change tracked files, create a bot branch, PR, tag, or push.

- [ ] **Step 4: Restrict the legacy workflow**

Remove the hourly schedule and direct commit/push step from `sync-skills.yml`. Keep only manual verification if required; route every state-changing synchronization through `component-upgrade.yml`.

- [ ] **Step 5: Verify and commit**

Run workflow safety tests and `python -B -m unittest discover -s tests -v`. Commit with `ci: reconcile components without direct main writes`.

## Task 7: Add protected manual Hub Release workflow

**Files:**
- Create: `.github/workflows/release-hub.yml`
- Create: `.github/scripts/render_hub_release_notes.py`
- Create: `tests/test_render_hub_release_notes.py`
- Modify: `docs/RELEASING.md`

**Inputs:** `version` without `v`, `confirm` equal to `PUBLISH`, and optional approved English note additions.

- [ ] **Step 1: Write failing renderer tests**

```python
def test_release_title_is_exact_and_component_versions_are_independent():
    notes = render_notes("1.0.1", mixed_components(), upgrades())
    assert notes.title == "RDK Skills v1.0.1"
    assert "BSP Skills | `v1.0.1`" in notes.body
    assert "OE Skills X5 | `v1.0.0`" in notes.body
    assert not contains_cjk(notes.body)
```

- [ ] **Step 2: Verify the red state**

Run `python -B -m unittest tests/test_render_hub_release_notes.py -v`. Expected: import failure because the renderer is absent.

- [ ] **Step 3: Implement renderer and protected workflow**

Render `.github/RELEASE_TEMPLATE.md` with mixed component refs and merged `component-upgrade` PR metadata; reject CJK text, unresolved markers, invalid versions, duplicate rows, and missing source formal Releases. Use only `workflow_dispatch` and Environment `release`. Before mutation require confirmation `PUBLISH`, absence of the destination remote tag and GitHub Release, and passing Hub tests. Create one annotated tag, push without force, then call `gh release create` with title `RDK Skills v<version>` and rendered English notes.

- [ ] **Step 4: Update policy, verify, and commit**

Update `docs/RELEASING.md` for mixed component tags, component-upgrade PRs, the `release` Environment, and manual inputs. Run renderer tests and the full Hub suite. Commit with `feat: add protected Hub release workflow`.

## Task 8: Pilot and enable production

**Files:**
- Modify: `docs/RELEASING.md`

- [ ] **Step 1: Exercise Hub dry run**

Dispatch `component-upgrade.yml` for a known formal BSP Release with `dry_run=true`; verify no branch and no PR are created.

- [ ] **Step 2: Run the end-to-end pilot**

Publish a designated BSP patch Release or target a protected non-production Hub. Verify one dispatch, one stable bot branch, one labeled PR, correct source SHA, synchronized artifacts, and passing required checks.

- [ ] **Step 3: Verify idempotency and Auto-merge boundary**

Repeat the same dispatch and verify the existing PR is updated rather than duplicated. Confirm the App cannot approve/merge; maintainer approval plus required checks enables Auto-merge.

- [ ] **Step 4: Verify manual Release safeguards**

In a non-production repository or dry-run mode, prove the Hub workflow rejects tag collision, confirmation other than `PUBLISH`, and an unpublished component reference while rendering English mixed-version notes.

- [ ] **Step 5: Record operations and commit**

Add App location, required checks, branch/label conventions, recovery dispatch command, and pilot results to `docs/RELEASING.md`. Commit with `docs: record component release automation runbook`.

## Plan Self-Review

| Spec requirement | Plan task |
| --- | --- |
| Formal source Release only | 2 and 5 |
| Least-privilege GitHub App | 1 and 4 |
| Independent component PRs | 4 |
| Approval plus Auto-merge | 1 and 8 |
| No direct scheduled writes | 3 and 6 |
| Protected manual Hub Releases | 7 |
| Immutable tags and mixed versions | 7 and 8 |
| Failure recovery and pilot validation | 2, 4, 6, and 8 |

Self-review completed: every specification section maps to a task; interfaces are defined before use; no unresolved planning markers remain.
