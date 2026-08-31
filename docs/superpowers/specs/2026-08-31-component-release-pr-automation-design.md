<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# Component Release to Hub PR Automation Design

## Status

Architecture approved in chat on 2026-08-31. This written specification requires maintainer review before implementation begins.

## Goal

When one of the four product-source repositories publishes a formal GitHub Release, automatically create or update one reviewable Hub pull request that pins that component to the released tag, synchronizes its mirrored content, and regenerates Hub artifacts. The bot never merges a pull request or publishes a Hub release by itself.

The four sources are:

- `D-Robotics/bsp-skills`
- `D-Robotics/rdk-device-skills`
- `D-Robotics/oe-skills-x5`
- `D-Robotics/oe-skills-s`

## Governing decisions

1. A source update is eligible only when its GitHub Release is published, non-draft, non-prerelease, and tagged with a stable semantic version such as `v1.0.1`.
2. A dedicated GitHub App is the only cross-repository identity. It is installed on the four source repositories and the Hub.
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

The workflow obtains a short-lived GitHub App installation token and calls the Hub repository-dispatch endpoint with event type `rdk-component-release`.

Payload contract:

```json
{
  "event_type": "rdk-component-release",
  "client_payload": {
    "schema_version": 1,
    "source_repo": "D-Robotics/bsp-skills",
    "tag": "v1.0.1",
    "release_url": "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
    "target_sha": "<40-character commit SHA>",
    "published_at": "2026-08-31T00:00:00Z"
  }
}
```

The source workflow emits no event for an invalid tag, draft, or prerelease. It logs only non-secret identifiers.

### 2. Hub component-upgrade workflow

The Hub adds `.github/workflows/component-upgrade.yml` with:

```yaml
on:
  repository_dispatch:
    types: [rdk-component-release]
  workflow_dispatch:
    inputs:
      source_repo: { required: true }
      tag: { required: true }
      dry_run: { type: boolean, default: true }
```

The manual dispatch path exists only for testing and recovery; it applies the same validation path as an App event.

Before changing files, the workflow must:

1. Require the expected GitHub App actor for repository-dispatch events.
2. Validate the payload schema, allowlisted source repository, and stable `vMAJOR.MINOR.PATCH` tag format.
3. Locate exactly one matching `components.d/*.yml` record.
4. Query the source repository's release API using the App token and prove that the release exists, is published, is not draft or prerelease, and has the same tag and target SHA as the payload.
5. Verify that the source tag is annotated and resolve it to the expected commit SHA.
6. Exit successfully without a PR when the component already pins that exact tag and its mirror/catalog is current.

The workflow then changes only the matched component's `ref` to the new tag, invokes the shared sync pipeline, regenerates catalogs/plugins/README tables, and runs the release and catalog tests.

Each component uses a stable branch such as `bot/component-upgrade/bsp-skills`. If that branch has an open PR against `main`, the bot updates it to the newest formal release and rewrites its title/body. Otherwise it creates a new branch and PR.

PR title:

```text
chore: upgrade BSP Skills to v1.0.1
```

PR body must include the previous and new tag, canonical source Release URL, dereferenced source SHA, changed mirrored directories, generated artifacts, test commands/results, and a note that a maintainer must choose the eventual Hub version after merge. It receives labels `component-upgrade` and `source:<component-id>`.

### 3. Shared synchronization logic

The current `sync-skills.yml` embeds its synchronization implementation and directly commits to `main`. Implementation extracts the deterministic sync portion into a reusable script or reusable workflow that accepts a component filter and produces machine-readable summaries.

It is called by the component-upgrade workflow from its bot branch, never directly commits to `main`, and remains responsible for:

- sparse checkout of the pinned source tag;
- mirror updates with stale-file pruning confined to the component catalog directory;
- workspace-pack `setup.sh` overlay;
- catalog and plugin regeneration;
- README table regeneration;
- existing contract, catalog, and plugin tests.

The existing hourly job is replaced by a read-only reconciliation/audit job. It may report drift or invalid component references, but it must not advance a component ref, change a mirror, create a tag, or push `main`.

### 4. Review and merge controls

`main` branch protection requires the Hub test suite and the component-upgrade validation job. The GitHub App may push only its `bot/component-upgrade/*` branches and open/update PRs.

Maintainers approve the PR in GitHub. With all required checks passing, GitHub Auto-merge performs the merge. The App never reviews a PR and is not granted permissions that could bypass protections.

### 5. Hub release workflow

The Hub adds `.github/workflows/release-hub.yml`, triggered only by `workflow_dispatch` and protected by a GitHub Environment such as `release`.

Inputs:

- `version`: semantic version without the `v` prefix;
- `confirm`: exact value `PUBLISH`;
- optional release-note additions.

The workflow:

1. Validates that `main` is clean and the destination `v<version>` tag and GitHub Release do not already exist.
2. Verifies every component `ref` resolves to a published formal source release; component versions may differ from one another and from the Hub version.
3. Runs the Hub release contracts, artifact generation checks, and clean-clone smoke checks.
4. Generates an English Release body from `.github/RELEASE_TEMPLATE.md`, the component upgrade PRs merged since the prior Hub tag, and the optional approved additions.
5. Creates one annotated, immutable Hub tag and then the GitHub Release titled exactly `RDK Skills v<version>`.
6. Publishes the Release only after the environment approval and all prior gates succeed.

## GitHub App and secret model

Create one organization-owned GitHub App, for example `rdk-release-bot`.

| Repository group | Required App permission | Purpose |
| --- | --- | --- |
| Source repositories | Contents: read | Read the published release/tag and send the dispatch event. |
| Hub | Contents: write; Pull requests: write | Push bot branches and create/update component-upgrade PRs. |
| Hub | Metadata: read | Resolve repository and release metadata. |

The App must not receive administration permission, approval/bypass capability, or a release-publishing role. Store its private key as an organization Actions secret (`RDK_RELEASE_BOT_PRIVATE_KEY`) scoped only to the five repositories; store the app ID as an organization Actions variable (`RDK_RELEASE_BOT_APP_ID`). Generate short-lived installation tokens in each workflow. Do not use a personal access token.

## Idempotency and failures

- Duplicate release events produce no duplicate PR because the component's stable bot branch and current pinned ref are checked first.
- A newer source release updates the existing open PR for that source component.
- Simultaneous events use concurrency key `component-upgrade-<component-id>`; different components may run in parallel.
- Validation failure, inaccessible release, missing App permission, tag mismatch, or failed sync/test leaves `main` untouched and opens/updates an issue labeled `component-upgrade-failure` with redacted diagnostics.
- A failed PR CI run remains reviewable but cannot auto-merge. Rerunning the workflow updates the same PR.
- Source releases remain valid even if the Hub notification fails; maintainers can use the Hub workflow-dispatch recovery path.

## Verification strategy

1. Unit-test payload validation, source-to-component mapping, semver acceptance/rejection, and idempotency decisions.
2. Add contract tests ensuring every `components.d` ref used by an upgrade resolves to an approved source release.
3. Add workflow-level dry-run support that validates a real release without pushing a branch or opening a PR.
4. Test a real non-production source release event against a protected test Hub repository before enabling the App on production repositories.
5. Verify production rollout with one component patch release, one generated PR, maintainer approval, Auto-merge, and a manually initiated Hub patch release.

## Rollout sequence

1. Register and install the GitHub App; configure organization secrets/variables and Hub branch protection/Auto-merge requirements.
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
