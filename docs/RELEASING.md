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

## Release procedure

1. Choose the next version and create a release branch or otherwise isolate the release work.
2. Normalize every current `SKILL.md` frontmatter version and applicable `VERSION` resource to the selected version.
3. Update source repositories first. Run their release contracts and create annotated `vX.Y.Z` tags.
4. Update the Hub component files in `components.d/` so every source `ref` is `vX.Y.Z`; synchronize mirrors, regenerate catalog files and plugins, and run Hub contracts.
5. Perform a clean-clone smoke test from the candidate Hub tag. Verify flat-skill discovery and each workspace-pack installation anchor.
6. Publish the source repositories, then the Hub `main` branch and annotated Hub tag. Confirm the remote dereferenced tag equals the intended commit in every repository.
7. Copy [`.github/RELEASE_TEMPLATE.md`](../.github/RELEASE_TEMPLATE.md), replace every placeholder, and create the public GitHub Release only after all previous checks pass:

   ```bash
   gh release create vX.Y.Z \
     --repo D-Robotics/rdk-skills \
     --title "RDK Skills vX.Y.Z" \
     --notes-file /path/to/final-release-notes.md
   ```

8. Re-open the public Release page and verify the title, English body, tag target, publication state, and generated source-code links.

## Required evidence

Record the following in the pull request, release issue, or release log:

- Candidate commit and dereferenced tag SHA for all four source repositories and the Hub.
- Results of source release contracts, Hub test suite, plugin/catalog generation, and clean-clone smoke tests.
- The exact final release body used to create the GitHub Release.
- Any known baseline failures, their scope, and why they are not release regressions.

## Release checklist

- [ ] All current Skill frontmatters use the release version.
- [ ] Source resource `VERSION` files and Hub registry references match the release version and tag.
- [ ] Every component source is pinned to an annotated `vX.Y.Z` tag.
- [ ] Source and Hub release contracts pass.
- [ ] Generated catalogs and plugin copies are deterministic and current.
- [ ] Clean-clone installation smoke tests pass.
- [ ] The Hub and source `main` refs match their published dereferenced tags.
- [ ] The GitHub Release title is `RDK Skills vX.Y.Z` and its English body follows the template.
- [ ] No published tag was force-moved.
