# Task 7 Review-Fix Report

## Scope

This review-fix pass hardens the protected manual Hub Release workflow. No
remote tag, GitHub Release, or push was performed.

## Review fixes

- The workflow-level token is read-only. Only the `publish` job requests
  `contents: write`, and that job is protected by the `release` Environment.
- Preflight records the exact verified `origin/main` SHA. The gated publish
  job checks out that SHA, rejects a changed remote `main`, and creates the
  annotated tag explicitly at the recorded SHA.
- Formal source Release verification is now a testable renderer boundary. It
  validates GitHub API release facts (repository/tag mapping, canonical URL,
  published/non-draft/non-prerelease state) and the annotated tag's resolved
  commit SHA. Merged component-upgrade metadata is checked against the same
  API facts rather than its PR-supplied URL or boolean flag.
- Duplicate component-upgrade metadata (duplicate PR number or identical
  component transition) is rejected before notes are rendered.

## Evidence

- Focused: `python -B -m unittest tests/test_render_hub_release_notes.py -v`
  passed: 6 tests.
- Static: Python compilation, workflow YAML permission contract, and every
  workflow shell block passed syntax checks; `git diff --check` passed.
- Full: `python -B -m unittest discover -s tests -v` ran 106 tests with 7
  documented Windows skips. One unrelated baseline failure remains:
  `test_generated_catalogs_match_component_inputs_and_plugin_copies` compares
  generator LF output with existing working-tree CRLF catalog files. Git reports
  these files as `i/lf w/crlf`; they were not modified in this task.

## External validation blockers

The repository still needs a real protected `release` Environment approval and
branch-protection configuration, plus a non-production GitHub Actions exercise
with read access to all four source repositories. Those external controls were
not changed locally.

## Re-review round 2

- Component-upgrade PR bodies now publish `Source SHA` as a 40-character
  hexadecimal value. The Hub release workflow parses that exact field from
  every merged upgrade PR.
- Missing or malformed `Source SHA` fields fail note generation. The parsed
  SHA is compared case-insensitively and exactly with the corresponding GitHub
  API annotated-tag dereference; any mismatch fails before rendering, tagging,
  pushing, or Release creation.
- Focused evidence: `tests/test_render_hub_release_notes.py` passed 7 tests,
  including dedicated missing, malformed, and mismatched upgrade-SHA cases.
  `tests/test_component_release.py` passed 28 tests. Python compilation,
  workflow YAML/shell syntax, and `git diff --check` also passed.
