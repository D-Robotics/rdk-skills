<!-- SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0 -->
<!-- Copyright (c) 2026 D-Robotics. All rights reserved. -->

# Release and Tagging Guide

This guide is the maintenance contract for formal RDK Skills releases. It applies to the Hub and its four product-source repositories: BSP Skills, RDK Device Skills, OE Skills X5, and OE Skills S.

## Release identity

- Use semantic versions without a leading `v` in file metadata, for example `1.2.0`.
- Use the matching annotated Git tag with a leading `v`, for example `v1.2.0`.
- The GitHub Release title must be exactly `RDK Skills vX.Y.Z`.
- The release body must be written in English and start from [`.github/RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md).
- GitHub's generated `Source code (zip)` and `Source code (tar.gz)` labels are platform-owned and cannot be renamed. Do not upload a duplicate archive merely to change its display name; attach only additional artifacts that carry distinct value and checksums.

## Tag immutability

Published tags are immutable release identities.

1. Create and validate the tag before creating the GitHub Release.
2. Never force-push, delete, or recreate a published tag.
3. If a published release needs a correction, publish the next patch version (for example, `v1.0.1`) with release notes explaining the correction.
4. Do not point a Hub component at a mutable branch for a formal release; use the corresponding annotated source tag.

## Component-upgrade automation prerequisites

Before enabling the Hub component-upgrade workflow, a maintainer must install
the organization-owned `rdk-release-bot` App with only Hub `Contents: write`,
`Pull requests: write`, and implicit `Metadata: read` access. Scope the App's
Actions variable and private-key secret to the approved repositories only.

Maintainers must also provision these PR labels in the Hub before the first
dispatch: `component-upgrade` and one `source:<component-id>` label for every
registered component. The workflow performs a read-only label preflight before
creating or updating a bot branch or PR; it intentionally does not create
labels or request Issues permission. Missing labels are an operations blocker,
not a reason to expand the App's privileges.

## Release procedure

1. A product-source repository publishes an annotated stable source tag and a formal GitHub Release. A formal source Release is published, non-draft, non-prerelease, and has the canonical URL for that tag.
2. The component-upgrade automation creates or updates a reviewable Hub PR. Maintainers review and merge it through the protected `main` branch; it is never merged by the release bot.
3. Choose the independent Hub version. It does not need to equal any component version. Verify every `components.d/*.yml` ref points to a published, annotated formal source Release.
4. Manually dispatch **Publish Hub release** from `main` with `version` in `MAJOR.MINOR.PATCH` form (without `v`), `confirm` exactly `PUBLISH`, and optional maintainer-approved additions written in English ASCII text.
5. The workflow runs Hub contracts, artifact-currentness checks, and a clean-clone workspace-pack smoke test. It renders the English Release body from [`.github/RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md), the merged `component-upgrade` PR metadata since the previous Hub tag, and the approved additions.
6. Only after these checks pass does the `release` Environment approval allow publication. The workflow rechecks that both remote `vX.Y.Z` and its GitHub Release are absent, creates one annotated tag, pushes it without force, and runs `gh release create` with title `RDK Skills vX.Y.Z`.
7. Re-open the public Release page and verify the exact English title/body, tag target, publication state, and generated source-code links.

## Release Environment and safeguards

The GitHub `release` Environment must require an authorized maintainer review before the `publish` job can run. The workflow has no scheduled, push, pull-request, or repository-dispatch trigger; release publication is possible only through the manual dispatch above.

All remote tag and GitHub Release collision checks, formal source Release checks, Hub tests, smoke checks, and note rendering run before the workflow creates a local or remote tag. A failed check therefore cannot write a tag or a GitHub Release. Published tags remain immutable: do not force-push, delete, or recreate them.

## Mixed component versions

The Hub is an assembler, not a version mirror. Its four component refs can legitimately differ, for example BSP at `v1.0.1`, Device Skills at `v1.2.0`, OE Skills X5 at `v1.0.0`, and OE Skills S at `v1.3.4`. The Hub Release notes list those exact pinned tags and identify merged component-upgrade PRs; never rewrite rows to match the Hub version.

## Required evidence

Record the following in the pull request, release issue, or release log:

- Candidate commit and dereferenced tag SHA for all four source repositories and the Hub.
- Results of source release contracts, Hub test suite, plugin/catalog generation, and clean-clone smoke tests.
- The exact final release body used to create the GitHub Release.
- Any known baseline failures, their scope, and why they are not release regressions.

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
