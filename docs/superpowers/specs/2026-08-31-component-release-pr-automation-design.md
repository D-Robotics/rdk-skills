<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# Component Release to Hub PR Automation Design

## Status

Architecture approved in chat on 2026-08-31 and amended by the final-review ledger ruling on 2026-09-01. The split-credential model below is binding.

## Goal

When one of the four product-source repositories publishes a formal GitHub Release, automatically create or update one reviewable Hub pull request that pins that component to the released tag, synchronizes its mirrored content, and regenerates Hub artifacts. The bot never merges a pull request or publishes a Hub release by itself.

The four sources are:

- `D-Robotics/bsp-skills`
- `D-Robotics/rdk-device-skills`
- `D-Robotics/oe-skills-x5`
- `D-Robotics/oe-skills-s`

## Governing decisions

1. A source update is eligible only when its GitHub Release is published, non-draft, non-prerelease, and tagged with a stable semantic version such as `v1.0.1`.
2. Cross-repository dispatch, Hub PR operations, Hub bot-branch pushes, and Hub release publication use four isolated credentials. Only the Hub-only Release App has `Contents: write`, and its ID/private key exist only on the protected `release` Environment.
3. Each component has at most one open bot-managed Hub pull request. A newer release for that component updates the existing PR instead of opening another one.
4. Different components always use independent PRs; releases are never automatically batched.
5. A maintainer approval plus the Hub's required CI checks permits GitHub Auto-merge. The bot has no permission to approve, merge, or bypass branch protection.
6. The Hub is released separately and only by a maintainer-triggered workflow after one or more component PRs have merged.
7. Published Git tags are immutable. A correction is a new patch release, never a force-moved tag.

## Architecture

### 1. Source notification workflows

Each source repository receives `.github/workflows/notify-hub-release.yml`.

Trigger:

```yaml
on:
  release:
    types: [published]
```

The workflow obtains a short-lived token from the Hub-only dispatcher App, scoped to the exact Hub repository with `Actions: write`, and calls the Hub `component-upgrade.yml` `workflow_dispatch` endpoint on `main`.

Payload contract:

```json
{
  "ref": "main",
  "inputs": {
    "schema_version": "1",
    "source_repo": "D-Robotics/bsp-skills",
    "tag": "v1.0.1",
    "release_url": "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
    "target_sha": "<40-character commit SHA>",
    "published_at": "2026-08-31T00:00:00Z",
    "dry_run": "false"
  }
}
```

The source workflow emits no event for an invalid tag, draft, or prerelease. It logs only non-secret identifiers.

### 2. Hub component-upgrade workflow

The Hub adds `.github/workflows/component-upgrade.yml` with:

```yaml
on:
  workflow_dispatch:
    inputs:
      schema_version: { required: false, default: '1' }
      source_repo: { required: true }
      tag: { required: true }
      release_url: { required: false }
      target_sha: { required: false }
      published_at: { required: false }
      dry_run: { type: boolean, default: true }
```

Automated non-dry dispatches must have all six verified facts and the configured dispatcher bot actor. A maintainer may dispatch a dry run manually without that actor or write credentials.

Before changing files, the workflow must:

1. Require the expected dispatcher App bot actor for every non-dry `workflow_dispatch`.
2. Validate the payload schema, allowlisted source repository, and stable `vMAJOR.MINOR.PATCH` tag format.
3. Locate exactly one matching `components.d/*.yml` record.
4. Query the allowlisted public source repository with the job-scoped `GITHUB_TOKEN` and prove that the Release exists, is published, is not draft or prerelease, and has the same tag, canonical URL, publication time, and target SHA as the dispatch inputs.
5. Verify that the source tag is annotated and resolve it to the expected commit SHA.
6. Exit successfully without a PR when the component already pins that exact tag and its mirror/catalog is current.

An unprivileged build job then changes only the matched component's `ref`, invokes the shared sync pipeline, regenerates catalogs/plugins/README tables, runs the release and catalog tests, force-stages additive and ignored files, validates a path allowlist, and emits a binary patch plus structured metadata. It receives no repository write credential. A separate publication job applies only that validated artifact to trusted `main`.

Each component uses a stable branch such as `bot/component-upgrade/bsp-skills`. If that branch has an open PR against `main`, the bot updates it to the newest formal release and rewrites its title/body. Otherwise it creates a new branch and PR.

PR title:

```text
chore: upgrade BSP Skills to v1.0.1
```

PR body must include the previous and new tag, canonical source Release URL, dereferenced source SHA, changed mirrored directories, generated artifacts, test commands/results, and a note that a maintainer must choose the eventual Hub version after merge. It receives labels `component-upgrade` and `source:<component-id>`.

### 3. Shared synchronization logic

The current `sync-skills.yml` embeds its synchronization implementation and directly commits to `main`. Implementation extracts the deterministic sync portion into a reusable script or reusable workflow that accepts a component filter and produces machine-readable summaries.

It is called from an exact trusted-`main` candidate in the unprivileged proposal-build job, never directly commits to `main`, and remains responsible for:

- sparse checkout of the pinned source tag;
- mirror updates with stale-file pruning confined to the component catalog directory;
- workspace-pack `setup.sh` overlay;
- catalog and plugin regeneration;
- README table regeneration;
- existing contract, catalog, and plugin tests.

The existing hourly job is replaced by a read-only reconciliation/audit job. It may report drift or invalid component references, but it must not advance a component ref, change a mirror, create a tag, or push `main`.

### 4. Review and merge controls

`main` branch protection requires exactly `DCO Check / dco` and `Verify committed skills catalog / verify`. The latter runs the full Hub unittest suite plus catalog and plugin validation on the pull-request candidate. The `component-upgrade.yml` `validate` job is a pre-PR dispatch gate, not a PR-required check. Repository rules constrain the Hub-only SSH deploy key to `bot/component-upgrade/*` and deny it `main` and tag writes. A separate Hub-only App with `Pull requests: write` may open/update PRs but cannot write repository contents.

Maintainers approve the PR in GitHub. With all required checks passing, GitHub Auto-merge performs the merge. The App never reviews a PR and is not granted permissions that could bypass protections.

### 5. Hub release workflow

The Hub adds `.github/workflows/release-hub.yml`, triggered only by `workflow_dispatch` and protected by a GitHub Environment such as `release`.

Inputs:

- `version`: semantic version without the `v` prefix;
- `confirm`: exact value `PUBLISH`;
- optional release-note additions.
- `recover_existing_tag`: explicit protected recovery for an exact existing tag that points to the approved candidate and has no GitHub Release.

The workflow:

1. Validates canonical no-leading-zero SemVer, clean `main`, and the destination state. Normal publication requires no tag and no Release; recovery requires an exact existing annotated tag resolving to the approved candidate and no Release.
2. Verifies every component `ref` resolves to a published formal source release; component versions may differ from one another and from the Hub version.
3. Runs the Hub release contracts, artifact generation checks, and clean-clone smoke checks.
4. Generates an English Release body from `.github/RELEASE_TEMPLATE.md`, the component upgrade PRs merged since the prior Hub tag, and the optional approved additions.
5. Carries the validated source evidence across Environment approval, re-fetches every source Release/tag/object fact, and rejects any tuple that changed before the first write.
6. Creates one annotated, immutable Hub tag for normal publication with the validated notes SHA-256 in its message. Recovery preserves the exact existing tag and requires its notes digest to match before and after approval, then creates the GitHub Release titled exactly `RDK Skills v<version>`.
7. Publishes only after the Environment approval and all prior gates succeed. Every job keeps its job-scoped `GITHUB_TOKEN` at `contents: read`; after post-approval revalidation, the publish job invokes the token action at a reviewed full commit SHA, mints an exact-repository Release App token, rechecks the approved notes digest, and uses that token only for the tag push and `gh release create --verify-tag` so the CLI cannot synthesize a missing tag.

## Credential and secret model

| Credential | Availability | Capability and purpose |
| --- | --- | --- |
| Dispatcher App: `RDK_RELEASE_DISPATCHER_APP_ID` / `RDK_RELEASE_DISPATCHER_PRIVATE_KEY` | Private key in the four source repositories; App installed only on Hub | `Actions: write` on exactly `D-Robotics/rdk-skills`; dispatch `component-upgrade.yml`. No `Contents` or Pull requests write. |
| PR App: `RDK_COMPONENT_PR_BOT_APP_ID` / `RDK_COMPONENT_PR_BOT_PRIVATE_KEY` | Hub only | `Pull requests: write` on exactly the Hub; create/edit proposal PR metadata. No `Contents: write`. |
| SSH deploy key: `RDK_COMPONENT_BRANCH_DEPLOY_KEY` | Hub only | Push only `bot/component-upgrade/*`; repository rules reject `main` and tag refs. |
| Release App: `RDK_HUB_RELEASE_APP_ID` / `RDK_HUB_RELEASE_APP_PRIVATE_KEY` | Both values only on protected Hub Environment `release`; App installed only on Hub | `Contents: write` on exactly `D-Robotics/rdk-skills`; after approval, mint a short-lived token used only for the annotated-tag push and matching GitHub Release. Sole bypass actor for the all-tag creation ruleset. |
| Job-scoped `GITHUB_TOKEN` | Hub workflows | `contents: read` for Hub/source evidence and destination-state queries; never pushes a tag or creates a Release. |

The dispatcher and PR Apps receive no `Contents: write`; the Release App receives no Actions, Pull requests, Issues, administration, approval, or merge capability. The PR App, Release App, and deploy key are unavailable to all source repositories. Configure `RDK_RELEASE_DISPATCHER_ACTOR` in Hub to the exact dispatcher bot login. Never use a personal access token.

The Release App is not a bypass actor for any branch ruleset, and protected `main` rejects its pushes. Its `Contents: write` permission is repository-wide and can create an otherwise unprotected branch, so tag-only workflow commands, exact-repository installation, Environment-only private-key storage, and branch protections are compensating controls rather than a claim that the permission is ref-scoped.

Two active rulesets overlap every Hub tag. The creation ruleset has exactly one `always` bypass actor: the Release App integration. The update-and-deletion ruleset has no bypass actors. Layering permits the Release App to create an approved new tag while preventing every actor, including the Release App, from updating or deleting an existing tag. Because an integration bypass cannot be constrained to a specific Environment, exact-repository App installation plus Environment-only private-key storage is a required compensating boundary.

## Idempotency and failures

- Duplicate release events produce no duplicate PR because the component's stable bot branch and current pinned ref are checked first.
- A newer source release updates the existing open PR; delayed events older than protected `main` or the existing proposal are rejected.
- Simultaneous events use concurrency key `component-upgrade-<component-id>`; different components may run in parallel.
- Validation failure, inaccessible release, missing App permission, tag mismatch, or failed sync/test leaves `main` untouched and opens/updates an issue labeled `component-upgrade-failure` with redacted diagnostics.
- A failed PR CI run remains reviewable but cannot auto-merge. Rerunning the workflow updates the same PR.
- Source releases remain valid even if notification fails; maintainers can manually dry-run the same Hub workflow. Non-dry automation remains actor-bound to the dispatcher App.

## Verification strategy

1. Unit-test payload validation, source-to-component mapping, semver acceptance/rejection, and idempotency decisions.
2. Add contract tests ensuring every `components.d` ref used by an upgrade resolves to an approved source release.
3. Add workflow-level dry-run support that validates a real release without pushing a branch or opening a PR.
4. Test a real non-production source release event against a protected test Hub repository before enabling the App on production repositories.
5. Verify production rollout with one component patch release, one generated PR, maintainer approval, Auto-merge, and a manually initiated Hub patch release.

## Rollout sequence

1. Register the three Hub-only Apps and branch-only SSH deploy key; configure exact repository scopes, the overlapping tag rulesets, secrets/variables, Hub branch protection, Auto-merge, and a protected `release` Environment with required approval, self-review prevention, and deployments restricted to `main`.
2. Add and test the Hub component-upgrade workflow in dry-run mode.
3. Add the source notification workflow to one pilot repository (BSP Skills).
4. Exercise the event-to-PR path in a non-production repository or with dry-run before enabling real PR writes.
5. Roll out the source workflow to the remaining three source repositories.
6. Replace the existing direct-to-main scheduled sync with the read-only reconciliation job.
7. Add the protected manual Hub release workflow and update `docs/RELEASING.md` to document independent component versions.

## Out of scope

- Automatically publishing a Hub Release after a component PR merges.
- Batching different component releases into one upgrade PR.
- Rewriting any released source or Hub tag.
- Importing untagged source `main` changes into a formal Hub release.
