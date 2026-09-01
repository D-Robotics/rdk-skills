# Component Release to Hub PR Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert each published source Release into one reviewable Hub component-upgrade PR, then publish the Hub only through a protected manual workflow.

**Architecture:** Four source workflows use a Hub-only `Actions: write` dispatcher App to invoke the Hub's `component-upgrade.yml` through `workflow_dispatch`. The Hub builds and validates source-derived artifacts without write credentials, uses a branch-only SSH deploy key for proposal branches, and uses a separate `Pull requests: write` App for PR metadata. After protected Environment approval, a fourth capability—a Hub-only Release App with only `Contents: write`—creates immutable Hub tags and English Releases.

**Tech Stack:** GitHub Actions, GitHub App tokens, GitHub CLI, Bash, Python 3, PyYAML, yq, git, unittest.

**Spec:** `docs/superpowers/specs/2026-08-31-component-release-pr-automation-design.md`

## Global Constraints

- Only published, non-draft, non-prerelease source Releases with tags matching `vMAJOR.MINOR.PATCH` are eligible.
- Use three Hub-only Apps and one Hub-only branch deploy key; never use a personal access token.
- The dispatcher App has only `Actions: write`; the PR App has only `Pull requests: write`; the Release App has only `Contents: write`; repository rules restrict the deploy key to `bot/component-upgrade/*` and reject `main` and tag refs.
- A component has one stable branch: `bot/component-upgrade/<component-id>`.
- Source component tags and Hub versions are independent; all published tags are immutable.
- No workflow may push directly to Hub `main`.
- New files use existing SPDX/copyright headers. Hub Release titles are exactly `RDK Skills vX.Y.Z` and bodies are English.

## File Structure

| File | Responsibility |
| --- | --- |
| `.github/scripts/component_release.py` | Parse and validate events; map a source repo to exactly one component; decide `noop` or `upgrade`. |
| `.github/scripts/release_contract.py` | Canonical SemVer, Release facts, destination-state, and approval revalidation. |
| `.github/scripts/sync-components.sh` | Synchronize only selected components at their pinned refs and write a summary JSON file. |
| `.github/scripts/upsert-component-pr.sh` | Build/test an allowlisted proposal artifact without write credentials. |
| `.github/scripts/publish-component-pr.sh` | Apply the validated artifact, push with SSH, and upsert PR metadata with the PR App token. |
| `.github/scripts/regenerate_readme.py` | Render README tables from parsed YAML and paths as inert structured data. |
| `.github/scripts/render_hub_release_notes.py` | Render English Hub notes from the template and merged upgrade metadata. |
| `.github/workflows/component-upgrade.yml` | Receive source dispatches and build component PRs. |
| `.github/workflows/reconcile-components.yml` | Read-only scheduled drift audit. |
| `.github/workflows/release-hub.yml` | Protected manual Hub tag and Release workflow. |
| `tests/test_component_release.py` | Validation, workflow contract, and idempotency tests. |
| `tests/test_sync_components.py` | Selective-sync integration test using local bare repositories. |
| `tests/test_render_hub_release_notes.py` | English release-note and mixed component-version tests. |

## Task 1: Configure GitHub App and repository controls

**Systems:** GitHub organization; four source repositories; Hub repository.

**Produces:** Three least-privilege Apps, a branch-only SSH deploy key and rules, protected Hub `main`, Auto-merge, and a protected `release` Environment.

- [ ] **Step 1: Register the isolated Apps**

Create a dispatcher App installed only on `D-Robotics/rdk-skills` with `Actions: write`, a PR App installed only on that same Hub with `Pull requests: write`, and a Release App installed only on that Hub with `Contents: write`. Grant the dispatcher and PR Apps no content permission. Grant the Release App no Actions, Pull requests, Issues, administration, approval, or merge capability; its sole ruleset bypass is tag creation.

- [ ] **Step 2: Configure scoped credentials**

Expose `RDK_RELEASE_DISPATCHER_APP_ID` and `RDK_RELEASE_DISPATCHER_PRIVATE_KEY` only to the four source notifier workflows. Expose `RDK_COMPONENT_PR_BOT_APP_ID` and `RDK_COMPONENT_PR_BOT_PRIVATE_KEY` only to Hub. Configure `RDK_HUB_RELEASE_APP_ID` and `RDK_HUB_RELEASE_APP_PRIVATE_KEY` only on the protected Hub `release` Environment. Configure Hub `RDK_RELEASE_DISPATCHER_ACTOR` to the exact dispatcher bot login. Confirm forked pull requests and source repositories cannot access the PR App, Release App, or deploy key.

- [ ] **Step 3: Configure merge and release boundaries**

Create a Hub-only SSH deploy key secret `RDK_COMPONENT_BRANCH_DEPLOY_KEY`. Add repository rules that allow this key only on `bot/component-upgrade/*` and reject `main` and tag refs. Add two overlapping all-tag rulesets: creation with only the Release App integration as an `always` bypass actor, and update plus deletion with no bypass actors. Require maintainer approval and Hub CI checks on `main`; enable GitHub Auto-merge. Create Environment `release` with required maintainer approval, self-review prevention, and a deployment branch policy restricted to `main` before storing either Release App credential there.

- [ ] **Step 4: Verify the App boundary**

Use the deploy key to push a temporary `bot/component-upgrade/*` branch. Prove the same key cannot push protected `main` or create any tag. Prove the dispatcher and PR App tokens cannot write contents or publish a Release. Confirm the Release App is absent from every branch-ruleset bypass list and its token cannot push protected `main`; record that `Contents: write` is not intrinsically tag-scoped. In a protection-equivalent non-production Hub, prove the exact-repository Release App token can create a new tag and matching Release but cannot update or delete a tag; alternatively, bind the positive production proof to the first planned formal Release and never create an undeletable disposable production tag. Prove the Release App credentials are unavailable before approval and to every source repository. Delete only the temporary branch after recording the result.

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

Require one matching component YAML, the canonical no-leading-zero stable SemVer contract, a 40-character SHA, matching release URL, and workflow-supplied facts showing the Release is neither draft nor prerelease. Reject events older than protected `main`. Return `noop` only when the component ref exactly equals the incoming tag.

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
  workflow_dispatch:
    inputs:
      schema_version: { required: false, default: '1', type: string }
      source_repo: { required: true, type: string }
      tag: { required: true, type: string }
      release_url: { required: false, type: string }
      target_sha: { required: false, type: string }
      published_at: { required: false, type: string }
      dry_run: { required: true, default: true, type: boolean }
```

- [ ] **Step 1: Write failing workflow-contract tests**

```python
def test_upgrade_workflow_is_dispatch_driven_and_dry_run_safe():
    workflow = read_workflow(".github/workflows/component-upgrade.yml")
    assert "workflow_dispatch" in workflow and "dry_run" in workflow
    assert "git push origin main" not in workflow

def test_branch_is_stable_per_component():
    assert branch_for("bsp-skills") == "bot/component-upgrade/bsp-skills"
```

- [ ] **Step 2: Verify the red state**

Run `python -B -m unittest tests/test_component_release.py -v`. Expected: contract tests fail because the workflow is absent.

- [ ] **Step 3: Implement validated dispatch handling**

Require the configured dispatcher bot actor and all six verified inputs for non-dry automation; allow a maintainer manual dry run. Query the exact allowlisted public source with the job-scoped `GITHUB_TOKEN`; verify published/non-draft/non-prerelease/tag/URL/time/SHA consistency and an annotated tag; call `component_release.py`; reject releases older than protected `main` or the existing proposal; use a concurrency key based on the source repository; exit before mutation for `dry_run` or verified `noop`.

- [ ] **Step 4: Implement PR upsert**

In an unprivileged job, reconstruct from the exact trusted `main`, change only the component ref, invoke `sync-components.sh`, regenerate README through structured data, build artifacts, run tests, force-stage additions/ignored files, and validate the path allowlist. Pass only a binary patch and structured metadata to the publication job. Apply it to trusted `main`, push `bot/component-upgrade/<component-id>` using only the SSH deploy key, and create/edit its PR using only the PR App token. Apply labels `component-upgrade` and `source:<component-id>`. Never execute existing bot-branch content and do not use `gh pr merge`.

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
    assert "component-upgrade.yml/dispatches" in workflow
    assert "RDK_RELEASE_DISPATCHER_PRIVATE_KEY" in workflow
    assert "github.event.release.prerelease" in workflow
```

- [ ] **Step 2: Verify the red state**

Run BSP's test suite. Expected: the notifier test fails because the workflow is absent.

- [ ] **Step 3: Implement and verify BSP notifier**

Trigger only on `release.published`; reject draft, prerelease, and noncanonical tags; obtain an exact-Hub-scoped dispatcher token with only `Actions: write`; resolve the release tag to a 40-character SHA; invoke the Hub workflow-dispatch endpoint with the six declared facts plus `dry_run=false`. Parse the workflow YAML in the test and run the source suite.

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

Use the selective-sync verification path in a temporary checkout to validate every pin against a published, non-draft, non-prerelease canonical annotated Release. Force-stage the disposable reconstruction so tracked, additive, deleted, and ignored drift is observable. On drift, malformed metadata, API failure, or invalid references, create/update an issue labeled `component-upgrade-failure`; do not change repository history, create a bot branch, PR, tag, or push.

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

**Inputs:** canonical `version` without `v`, `confirm` equal to `PUBLISH`, optional approved English note additions, and explicit `recover_existing_tag` for protected release-only recovery.

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

Render `.github/RELEASE_TEMPLATE.md` with mixed component refs and merged `component-upgrade` PR metadata; reject CJK text, unresolved markers, invalid versions, duplicate rows, and missing source formal Releases. Use only `workflow_dispatch` and Environment `release`. Keep every job's `GITHUB_TOKEN` at `contents: read`; after Environment approval and post-approval evidence revalidation, invoke the Release App token action at a reviewed full commit SHA and mint an exact-`D-Robotics/rdk-skills` token with only `Contents: write`. Carry the validated requests/facts/notes as evidence, re-fetch and compare every source fact with `github.token`, bind the approved notes digest across token creation, and use the Release App token only for the tag push and `gh release create --verify-tag`. Normal publication creates one annotated tag containing the validated notes SHA-256, then the Release. Explicit recovery accepts only an exact existing annotated tag resolving to the approved candidate with no Release and the same notes digest, preserves the tag, and creates only the missing Release.

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

Repeat the same dispatch and verify the existing PR is updated rather than duplicated. Confirm none of the three Apps nor the deploy key can approve or merge; maintainer approval plus required checks enables Auto-merge.

- [ ] **Step 4: Verify manual Release safeguards**

In a non-production repository or dry-run mode, prove the Hub workflow rejects tag collision, confirmation other than `PUBLISH`, and an unpublished component reference while rendering English mixed-version notes.

- [ ] **Step 5: Record operations and commit**

Add all three App locations, exact repository scopes, deploy-key and tag-ruleset rules, required checks, branch/label conventions, release Environment controls, recovery dispatch procedure, and pilot results to `docs/RELEASING.md`. Commit with `docs: record component release automation runbook`.

## Plan Self-Review

| Spec requirement | Plan task |
| --- | --- |
| Formal source Release only | 2 and 5 |
| Isolated least-privilege credentials | 1, 4, and 5 |
| Independent component PRs | 4 |
| Approval plus Auto-merge | 1 and 8 |
| No direct scheduled writes | 3 and 6 |
| Protected manual Hub Releases | 7 |
| Immutable tags and mixed versions | 7 and 8 |
| Failure recovery and pilot validation | 2, 4, 6, and 8 |

Self-review completed: every specification section maps to a task; interfaces are defined before use; no unresolved planning markers remain.
