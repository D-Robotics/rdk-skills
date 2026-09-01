# DCO action ref fix

## Scope

Fix the DCO workflow's unresolved action reference with the smallest possible change and preserve a repository contract test.

## Evidence

### RED (before workflow fix)

Command:

```text
python -m unittest tests.test_release_contract.ReleaseContractTests.test_dco_workflow_uses_resolvable_action_ref
```

Result: failed as expected (`exit_code=1`). The assertion reported that `christophebedard/dco-check@0.5.1` was absent while the workflow still contained `christophebedard/dco-check@v0.5.2`.

### GREEN (after workflow fix)

Command:

```text
python -m unittest tests.test_release_contract.ReleaseContractTests.test_dco_workflow_uses_resolvable_action_ref
```

Result: passed (`Ran 1 test ... OK`).

YAML validation:

```text
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path('.github/workflows/dco.yml').read_text(encoding='utf-8')); print('YAML parse: OK')"
```

Result: `YAML parse: OK`.

Relevant full contract suite:

```text
python -m unittest tests.test_release_contract tests.test_license_contract tests.test_plugin_contract
```

Result: 19 tests ran, 1 skipped, 1 pre-existing failure in `test_generated_catalogs_match_component_inputs_and_plugin_copies` due to LF/CRLF byte differences in the generated catalog; the DCO contract test passes.

Diff validation:

```text
git diff --check
```

Result: clean.

## Changes

- Added `test_dco_workflow_uses_resolvable_action_ref` to assert the resolvable `christophebedard/dco-check@0.5.1` ref and reject `@v0.5.2`.
- Changed only the DCO action ref in `.github/workflows/dco.yml` from `@v0.5.2` to `@0.5.1`.

## Commit

Commit SHA: `1b5e7ca`

Commit message: `ci: fix DCO action version`
