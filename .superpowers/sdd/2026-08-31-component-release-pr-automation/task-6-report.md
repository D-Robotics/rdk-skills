# Task 6 report — read-only component reconciliation

## Outcome

Replaced the scheduled direct-write synchronizer with a scheduled,
disposable-worktree reconciliation check. It detects invalid pinned refs and
mirror/catalog/plugin drift but cannot change the Hub catalog, history,
branches, pull requests, or tags. The existing `component-upgrade.yml`
workflow remains the only state-changing synchronization path.

## Changes

- `.github/workflows/sync-skills.yml`
  - Removes the hourly schedule, `push` trigger, PAT-based synchronization,
    pruning, generated-artifact writes, commit/push, and rolling issue code.
  - Retains a `workflow_dispatch`-only verifier with read-only contents
    permission, no persisted checkout credential, catalog validation, plugin
    include validation, and a final clean-diff assertion.
- `.github/workflows/reconcile-components.yml`
  - Runs daily and on manual dispatch with `contents: read` and `issues: write`
    only; it does not create a GitHub App token.
  - Resolves each registered immutable semver tag to an annotated-tag peeled
    SHA, synchronizes it into a temporary Git worktree, and compares the
    reconstructed source SHA to the pin.
  - Rebuilds mirrors, catalog artifacts, plugins, and README only in that
    temporary worktree, then reports any diff as drift.
  - Creates or updates one rolling issue through the repository-scoped
    `secrets.GITHUB_TOKEN`, labeled `component-upgrade-failure`, then fails the
    run. It preflights that label before any issue write; repository
    administrators must provision the label as part of Task 1 setup.
- `tests/test_component_release.py`
  - Adds workflow contracts for scheduled temporary-worktree reconciliation,
    read-only permissions, current-repository token issue reporting, and the
    explicit absence of push/commit/branch/tag/PR/App-token mutation paths.
  - Adds the legacy-workflow contract preventing a schedule or direct commit
    and push behavior.

## TDD evidence

1. Added the reconciliation and legacy-sync safety contracts first.
2. Ran `python -B -m unittest tests/test_component_release.py -v`; it failed
   as expected because `reconcile-components.yml` was absent and the old sync
   workflow still had its schedule and commit/push implementation.
3. Implemented the two workflows and reran the focused suite green.

## Verification

- PASS: `python -B -m unittest tests/test_component_release.py -v` (25 tests)
- PASS: YAML parse of both changed workflows with PyYAML.
- PASS: Bash syntax parsing for every `run` block in both changed workflows.
- PASS: `git diff --check`.
- Full suite: 97 total; 89 passed, 7 skipped, 1 known baseline failure.
  `tests/test_release_contract.py::ReleaseContractTests::test_generated_catalogs_match_component_inputs_and_plugin_copies`
  compares generated LF bytes with tracked catalog files checked out as CRLF
  in this Windows worktree. Task 4 recorded the same pre-existing condition;
  Task 6 does not change generated catalog artifacts. The optional plugin
  dry-run and selective-sync integration tests retain their existing platform
  skips because `yq` is unavailable locally and Git for Windows is guarded.

`actionlint` and `shellcheck` are not installed in this environment; YAML and
Bash parsing were performed with the available local tooling. No external
workflow dispatch, issue, branch, pull request, tag, or push was attempted.
