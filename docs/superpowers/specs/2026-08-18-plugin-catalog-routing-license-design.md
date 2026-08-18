# Plugin Catalog, Routing, and License Reconciliation Design

## Status

Approved in chat on 2026-08-18. This design covers the first remediation phase for the D-Robotics Skills Hub.

## Goal

Make the Hub plugin self-contained and truthful: it must ship the pack data its installer consumes, provide a real catalog finder, stop routing users to missing D-Robotics Skills, and explain the repository's accepted dual-license policy without changing that policy.

## Scope

This phase includes four deliverables:

1. A generated workspace-Pack registry bundled with `rdk-pack-installer`.
2. A new Hub-native `rdk-skill-finder` with a generated searchable Skill index.
3. Removal or replacement of known stale D-Robotics Skill routes in `rdk-device-skills`, followed by a mirror refresh in `rdk-skills`.
4. Consistent license language derived from ADR 0004.

This phase does not add new domain Skills such as `rdk-ros`, redesign the complete synchronization pipeline, enforce all existing L1/L2 violations, or migrate legacy OE Skill metadata.

## Governing Decisions

### Catalog data is generated and bundled

Runtime fetching from GitHub is rejected because discovery and installation must work without a network request beyond the installation operation itself. Copying the raw `components.d/` tree into the plugin is also rejected because it exposes the Hub's internal registration layout as the plugin interface.

Instead, build-time tooling generates two small JSON documents:

- `skills/rdk-pack-installer/references/pack-registry.json`
- `skills/rdk-skill-finder/references/skill-index.json`

Each Hub-native Skill therefore remains independently installable. The generated files are committed so marketplace consumers receive the same reviewed data as the repository.

### Missing routes map only to current capabilities

This phase does not create replacement domain Skills. A stale route is handled in one of two ways:

- Point to an existing Skill that covers the request.
- State that the workflow is not currently covered and route factual lookup to `rdk-docs-reference`.

### ADR 0004 remains authoritative

No license is being relicensed in this phase. The accepted policy is:

- Code and scripts: Apache-2.0.
- Documentation, `SKILL.md`, `skill-card.md`, and references: CC-BY-4.0.
- The ecosystem-compatible top-level Skill frontmatter remains `license: Apache-2.0`, as explicitly required by ADR 0004.

Documentation will explain this scope and recommend `metadata.content-license: CC-BY-4.0` for new or edited Skills. The validator will continue requiring a non-empty `license` field; expanding license enforcement across legacy Packs is outside this phase.

## Architecture

### Catalog generator

A focused Python module under `.github/scripts/` owns catalog generation. Its command-line interface accepts the repository root and writes the two deterministic JSON outputs.

Inputs:

- `components.d/*.yml`
- Every registered `SKILL.md`
- `catalog-exceptions.yml` for Hub-native Skills

Pack-registry output contains only workspace-integrated Packs and these fields:

```json
{
  "schema_version": 1,
  "packs": [
    {
      "name": "OE Tool Chain (X5)",
      "repo": "D-Robotics/oe-skills-x5",
      "ref": "main",
      "install_type": "workspace",
      "install_script": "setup.sh",
      "workspace_dir": ".drobotics",
      "verify_paths": [
        ".drobotics/X5.md",
        ".drobotics/VERSION",
        ".drobotics/skill-index.json",
        ".drobotics/skills/x5-router/SKILL.md"
      ]
    }
  ]
}
```

Skill-index output contains one record per discovered Skill:

```json
{
  "schema_version": 1,
  "skills": [
    {
      "name": "rdk-diagnostic",
      "description": "...",
      "pack": "RDK Device Skills",
      "catalog_path": "skills/rdk-diagnostic",
      "install_type": "flat",
      "repo": "D-Robotics/rdk-device-skills"
    }
  ]
}
```

Generation is deterministic: records are sorted by stable keys, JSON uses UTF-8 with a trailing newline, and a second run produces no Git diff.

### Component installation contract

Workspace registrations gain two required fields:

- `workspace_dir`: project-relative directory written by the Pack.
- `verify_paths`: non-empty list of project-relative paths that prove installation succeeded.

For this phase:

- OE X5 uses `.drobotics` and verifies X5 metadata, version, index, and router files.
- OE S uses `.horizon` and verifies HORIZON metadata, version, index, and router files.

`components.d/README.md` documents these fields. The generator fails on missing or unsafe workspace installation fields instead of emitting an incomplete registry.

### Pack installer

`rdk-pack-installer` reads `references/pack-registry.json` relative to its own Skill directory. It no longer requires `components.d` at runtime.

Its workflow remains confirmation-gated:

1. Match the request to a registry Pack.
2. Confirm the exact project root.
3. Show the declared workspace directory and files that will be verified.
4. Clone the declared repository to a temporary directory.
5. Read `agent-setup.md` when present, then run the declared install script after final approval.
6. Verify every declared path.
7. Remove the temporary clone and report results.

Unknown Pack names and malformed registry data are terminal errors. The installer must not guess repository names or verification paths.

### Skill finder

The new `rdk-skill-finder` is a read-only Hub-native Skill. It contains:

- `SKILL.md`
- `skill-card.md`
- `evals/tasks.yaml`
- `scripts/search_catalog.py`
- generated `references/skill-index.json`

The search script accepts one or more query terms plus optional filters for Pack, board/platform token, and installation type. It returns deterministic JSON ranked by exact name match, trigger/description token overlap, then Skill name.

Finder behavior:

- For a flat Skill, return its name, short explanation, and `npx skills add d-robotics/rdk-skills --skill <name>`.
- For a workspace Skill, return its Pack and hand off installation to `rdk-pack-installer`.
- If no result clears a small deterministic overlap threshold, report no match and suggest `rdk-docs-reference`; do not invent a Skill name.

The plugin includes the finder, installer, and documentation reference Skill. Marketplace and README language describes discovery and installation, not transparent loading of every catalog Skill.

## Route Reconciliation

Edits are made in `rdk-device-skills`, the source repository. The corresponding Hub mirror is refreshed in the same implementation so local verification reflects the source.

Known mappings:

| Stale route | Replacement |
|---|---|
| `rdk-doc-finder` | `rdk-docs-reference` |
| `rdk-mipi-camera-bringup` | `rdk-camera-setup` |
| `rdk-device` for on-board inference | `rdk-model-deploy` |
| `rdk-device` for custom model conversion | `x5-router` for X5 or `horizon-router` for S-series; mention workspace Pack installation when absent |
| `rdk-ros` for TROS installation/environment | `rdk-tros-setup` |
| `rdk-ros` for ROS node/application development | State that no dedicated Skill is currently cataloged; use `rdk-docs-reference` against official TROS documentation |
| `rdk-perf-investigator` | Remove the nonexistent name and retain a generic diagnostic-orchestration statement |

No replacement may imply that a narrower Skill covers work outside its documented scope.

## License Reconciliation

The following documents are updated together:

- `README.md`
- `README_cn.md`
- `CONTRIBUTING.md`
- `docs/PR-SUBMISSION.md`
- `components.d/README.md` where relevant to mirrored license policy

They will state that repository files are dual-licensed by file type, while the required top-level frontmatter value remains `Apache-2.0` per ADR 0004. New or materially edited Skills should add:

```yaml
metadata:
  content-license: CC-BY-4.0
```

This metadata is explanatory in this phase, not an enforcing gate, so legacy OE Packs do not acquire new failures.

## Error Handling

- Missing or invalid frontmatter in a registered Skill causes catalog generation to fail with the catalog-relative path.
- Duplicate Skill names cause generation to fail; the finder cannot safely disambiguate them.
- Duplicate catalog paths cause generation to fail.
- Missing workspace verification fields cause pack-registry generation to fail.
- Missing `include_skills` paths cause plugin build failure rather than silent omission.
- Finder parse errors and zero-match results produce structured errors without fallback fabrication.
- Route validation reports the source file and missing route name.

## Testing

Implementation follows TDD. Tests use temporary repository fixtures and exercise public command behavior.

Required tests:

1. Catalog generation emits X5 and S workspace records with their correct workspace directories and verification paths.
2. Catalog generation emits flat and workspace Skill index records and is byte-for-byte deterministic.
3. Generator rejects duplicate Skill names, unsafe verification paths, and missing workspace fields.
4. Finder ranks exact name matches first and filters flat versus workspace records.
5. Finder returns the flat install command and workspace installer handoff.
6. Plugin build fails for a missing included Skill and packages all three Hub-native Skills.
7. Pack installer instructions refer only to its bundled registry, not runtime `components.d` access.
8. A route-integrity test finds none of the five retired route names in `rdk-device-skills/skills/*/SKILL.md`.
9. Documentation tests assert that ADR 0004's code/content split and frontmatter rule are stated consistently.
10. Existing Hub validation and source-Pack validation continue to run, with no new L1/L2 violations introduced by this phase.

## Repository Changes

### `rdk-skills`

- Add the generator and tests.
- Add `rdk-skill-finder` and its tests/evals.
- Add generated registry/index files.
- Extend workspace component registrations.
- Update installer instructions and plugin composition.
- Rebuild committed plugin artifacts and marketplace files.
- Refresh the mirrored RDK Device Skills after source edits.
- Reconcile license and plugin claims in documentation.

### `rdk-device-skills`

- Replace the known stale routes.
- Add a route-integrity regression test to the existing validation/test entry point.
- Update affected eval expectations if route names appear in them.

## Acceptance Criteria

- A standalone installed Hub plugin can discover a Skill and identify a workspace Pack without access to the Hub's `components.d` directory.
- The Pack installer resolves X5 and S installation/verification data from its bundled registry.
- The plugin contains `rdk-skill-finder`, `rdk-pack-installer`, and `rdk-docs-reference`.
- No known stale D-Robotics route name remains in the RDK Device Skill source or Hub mirror.
- License documentation agrees with ADR 0004 and does not relicense existing content.
- All new tests demonstrate red-green behavior and the complete verification suite passes before completion is claimed.
