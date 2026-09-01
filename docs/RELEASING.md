<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# Release and Tagging Guide

This guide is the maintenance contract for formal RDK Skills releases. It applies to the Hub and its four product-source repositories: BSP Skills, RDK Device Skills, OE Skills X5, and OE Skills S.

## Release identity

- Use semantic versions without a leading `v` in file metadata, for example `1.2.0`.
- Use the matching annotated Git tag with a leading `v`, for example `v1.2.0`.
- Numeric identifiers are canonical: `0` or a nonzero digit followed by digits. Values such as `01.2.3`, `1.02.3`, and `1.2.03` are invalid at every source and Hub boundary.
- The GitHub Release title must be exactly `RDK Skills vX.Y.Z`.
- The release body must be written in English and start from [`.github/RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md).
- GitHub's generated `Source code (zip)` and `Source code (tar.gz)` labels are platform-owned and cannot be renamed. Do not upload a duplicate archive merely to change its display name; attach only additional artifacts that carry distinct value and checksums.

## Tag immutability

Published tags are immutable release identities.

1. Normal publication creates and validates the tag before creating the GitHub Release. Protected release-only recovery may reuse only the exact immutable annotated tag described below.
2. Never force-push, delete, or recreate a published tag.
3. If a published release needs a correction, publish the next patch version (for example, `v1.0.1`) with release notes explaining the correction.
4. Do not point a Hub component at a mutable branch for a formal release; use the corresponding annotated source tag.

## Component-upgrade automation prerequisites

Before enabling the Hub component-upgrade and release workflows, maintainers must provision four isolated capabilities:

1. A dispatcher App installed only on `D-Robotics/rdk-skills`, with only `Actions: write` (plus implicit metadata read). Its ID/private key are exposed to the four source repositories as `RDK_RELEASE_DISPATCHER_APP_ID` and `RDK_RELEASE_DISPATCHER_PRIVATE_KEY`. Each notifier scopes its installation token to exactly `D-Robotics/rdk-skills` and invokes the Hub `component-upgrade.yml` workflow-dispatch endpoint. `Actions: write` can dispatch Hub Actions workflows, but cannot write contents, refs, or Releases; keep all Hub workflows trusted and actor-gated where they mutate state.
2. A PR App installed and available only on `D-Robotics/rdk-skills`, with only `Pull requests: write`, stored as `RDK_COMPONENT_PR_BOT_APP_ID` and `RDK_COMPONENT_PR_BOT_PRIVATE_KEY`. Source repositories must not receive this credential.
3. A Hub-only SSH deploy key stored as `RDK_COMPONENT_BRANCH_DEPLOY_KEY`. Repository rules must permit it to update only `bot/component-upgrade/*` and must reject `main` and every tag ref. Source repositories must not receive this key.
4. A Release App installed only on `D-Robotics/rdk-skills`, with only `Contents: write` (plus implicit metadata read). Configure `RDK_HUB_RELEASE_APP_ID` and `RDK_HUB_RELEASE_APP_PRIVATE_KEY` only on the protected `release` Environment, never as repository- or organization-level credentials. After Environment approval, the workflow invokes `actions/create-github-app-token` at the reviewed, pinned v2 commit and requests a token narrowed to owner `D-Robotics`, repository `rdk-skills`, and `permission-contents: write`. The token is used only to push the approved annotated tag and create the matching GitHub Release.

The Release App is the only App with `Contents: write`. The dispatcher and PR Apps retain their non-content permissions, and the Hub workflow's job-scoped `GITHUB_TOKEN` remains `contents: read`, including for source and destination evidence queries. Set Hub variable `RDK_RELEASE_DISPATCHER_ACTOR` to the exact dispatcher login ending in `[bot]`; every automated non-dry dispatch must match it, while a maintainer manual dry-run remains available.

Protect every Hub tag with two active, overlapping tag rulesets. The creation ruleset covers every tag and grants `always` bypass only to the Release App integration. A second ruleset covers every tag, restricts update and deletion, and has no bypass actors. GitHub layers both rulesets: the approved Release App token may create a new tag, but neither that App, the deploy key, `GITHUB_TOKEN`, nor a maintainer may update or delete an existing tag through a bypass. The Release App bypass cannot itself be scoped to an Environment, so the exact-repository App installation and Environment-only private key are mandatory compensating controls.

Do not add the Release App to any branch-ruleset bypass list, and prove its token cannot push protected `main`. `Contents: write` is repository-wide rather than ref-scoped, so the App can still create an otherwise unprotected branch if its private key is misused. The workflow hard-codes a tag-only push refspec; Environment-only key storage, main-only deployment policy, exact-repository installation, and the absence of branch bypass are the required compensating controls. Do not describe the App permission itself as tag-only.

Maintainers must also provision these PR labels in the Hub before the first
dispatch: `component-upgrade`, `component-upgrade-failure`, and one `source:<component-id>` label for every
registered component. The workflow performs a read-only label preflight before
creating or updating a bot branch or PR; it intentionally does not create
PR labels. Failure reporting uses only the job-scoped `GITHUB_TOKEN` with job-level `issues: write`; it never expands an App credential. Missing labels are an operations blocker, not a reason to expand the dispatcher or PR App privileges.

Protect Hub `main` with maintainer review and exactly these required checks: `DCO Check / dco` and `Verify committed skills catalog / verify`. The catalog check runs the full Hub unittest suite plus catalog and plugin validation against the pull-request candidate. `component-upgrade.yml`'s `validate` job is a pre-PR dispatch gate, not a PR-required check. Enable Auto-merge only after those gates, and configure the `release` Environment with required maintainer approval, self-review prevention, and a deployment branch policy that permits only `main` (not tags or other branches). Before production enablement, prove that the deploy key cannot write `main` or create tags and that the dispatcher and PR Apps cannot write contents or publish a Release. Exercise positive Release App tag/Release creation and update/delete denial only in a protection-equivalent non-production Hub, or bind that evidence to the first planned formal production release; never create a disposable production tag because the no-bypass immutability rules make it intentionally undeletable.

## Release procedure

1. A product-source repository publishes an annotated stable source tag and a formal GitHub Release. A formal source Release is published, non-draft, non-prerelease, and has the canonical URL for that tag.
2. The component-upgrade automation creates or updates a reviewable Hub PR. Maintainers review and merge it through the protected `main` branch; it is never merged by the release bot.
3. Choose the independent Hub version. It does not need to equal any component version. Verify every `components.d/*.yml` ref points to a published, annotated formal source Release.
4. Manually dispatch **Publish Hub release** from `main` with canonical `version` in `MAJOR.MINOR.PATCH` form (without `v`), `confirm` exactly `PUBLISH`, `recover_existing_tag=false`, and optional maintainer-approved additions written in English ASCII text.
5. The workflow runs Hub contracts, artifact-currentness checks, and a clean-clone workspace-pack smoke test. It renders the English Release body from [`.github/RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md), the merged `component-upgrade` PR metadata since the previous Hub tag, and the approved additions.
6. Only after these checks pass does the `release` Environment approval expose the Release App ID/private key and allow publication. The workflow first re-fetches every recorded source Release, tag object, publication time, canonical URL, and dereferenced commit with the read-only `GITHUB_TOKEN`; any changed tuple aborts before a write token exists. It also rechecks that both remote `vX.Y.Z` and its GitHub Release are absent and records the approved notes SHA-256. Only then does it create an exact-repository Release App token, re-hash the notes before any write, use the token to create and push one annotated tag without force, and pass it explicitly to `gh release create --verify-tag` with title `RDK Skills vX.Y.Z`. `--verify-tag` prevents the CLI from synthesizing a missing lightweight tag.
7. Re-open the public Release page and verify the exact English title/body, tag target, publication state, and generated source-code links.

## Release Environment and safeguards

The GitHub `release` Environment must require an authorized maintainer review before the `publish` job can run, prevent the initiating actor from approving their own deployment, and allow deployments only from branch `main`. Store both `RDK_HUB_RELEASE_APP_ID` and `RDK_HUB_RELEASE_APP_PRIVATE_KEY` only in that Environment. The workflow has no scheduled, push, pull-request, or repository-dispatch trigger; release publication is possible only through the manual dispatch above. The publish job retains `contents: read` for `GITHUB_TOKEN`; only its short-lived, exact-repository Release App token performs the tag push and `gh release create`.

All remote tag and GitHub Release state checks, formal source Release checks, Hub tests, smoke checks, evidence rendering, and post-approval source revalidation run before the workflow's first write. Published tags remain immutable: do not force-push, delete, or recreate them.

## Exact-tag Release recovery

Tag creation and GitHub Release creation cannot be atomic. If normal publication pushed the annotated Hub tag but `gh release create` failed, retain the tag and inspect the failed run. Retry **Publish Hub release** with the same `version`, `confirm=PUBLISH`, the same approved notes, and `recover_existing_tag=true`.

Normal publication records `Release-Notes-SHA256` in the annotated tag message. Recovery is accepted only behind the same `release` Environment when no GitHub Release exists, the remote tag is annotated and points to a commit retained in protected `main` history, and the newly validated notes match that preserved digest before and after approval. Recovery checks out that tagged candidate, so a later fast-forward of `main` does not strand the half-release. It never creates, moves, deletes, or force-pushes a tag; it creates only the missing GitHub Release. If the tag target left protected history, the notes differ, source evidence changed, or a Release already exists, stop and investigate rather than altering history.

## Mixed component versions

The Hub is an assembler, not a version mirror. Its four component refs can legitimately differ, for example BSP at `v1.0.1`, Device Skills at `v1.2.0`, OE Skills X5 at `v1.0.0`, and OE Skills S at `v1.3.4`. The Hub Release notes list those exact pinned tags and identify merged component-upgrade PRs; never rewrite rows to match the Hub version.

## Required evidence

Record the following in the pull request, release issue, or release log:

- Candidate commit and dereferenced tag SHA for all four source repositories and the Hub.
- Results of source release contracts, Hub test suite, plugin/catalog generation, and clean-clone smoke tests.
- The exact final release body used to create the GitHub Release.
- Any known baseline failures, their scope, and why they are not release regressions.
- The selected destination action (`create-tag` or `release-only`) and the preflight/post-approval evidence artifact.

Local tests and static workflow contracts are not production pilot evidence. Before enabling source non-dry dispatches, record the authorized dry run, isolated end-to-end event, duplicate-event idempotency result, deploy-key/App denial checks, Auto-merge boundary, normal release rejection cases, and exact-tag recovery exercise. Until those external controls and pilots are recorded, production enablement remains pending.

## Release checklist

- [ ] Hub-owned Skill frontmatters use the selected Hub release version where applicable.
- [ ] Source resource `VERSION` files match their own source release versions.
- [ ] Every component source is pinned to its own annotated, published formal release tag.
- [ ] Source and Hub release contracts pass.
- [ ] Generated catalogs and plugin copies are deterministic and current.
- [ ] Clean-clone installation smoke tests pass.
- [ ] The Hub tag is annotated and immutable; every component ref resolves to its published formal source Release.
- [ ] The GitHub Release title is `RDK Skills vX.Y.Z` and its English body follows the template.
- [ ] No published tag was force-moved.
