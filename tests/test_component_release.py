# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Unit tests for component Release event validation."""

import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / ".github" / "scripts" / "component_release.py"
UPGRADE_MODULE_PATH = ROOT / ".github" / "scripts" / "component_upgrade.py"


def read_workflow(relative_path: str) -> str:
    """Return a workflow contract as UTF-8 text."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


def branch_for(component_id: str) -> str:
    """Return the one stable upgrade branch for a component."""
    return f"bot/component-upgrade/{component_id}"


def load_upgrade_helper():
    """Load the component-upgrade helper without importing package state."""
    spec = importlib.util.spec_from_file_location("component_upgrade", UPGRADE_MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


spec = importlib.util.spec_from_file_location("component_release", MODULE_PATH)
assert spec is not None and spec.loader is not None
component_release = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = component_release
spec.loader.exec_module(component_release)

ComponentRef = component_release.ComponentRef
ComponentReleaseEvent = component_release.ComponentReleaseEvent
ValidationError = component_release.ValidationError
decide_upgrade = component_release.decide_upgrade
load_components = component_release.load_components
validate_release_event = component_release.validate_release_event


class ComponentReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        components_dir = self.root / "components.d"
        components_dir.mkdir()
        (components_dir / "bsp-skills.yml").write_text(
            "name: BSP Skills\nrepo: D-Robotics/bsp-skills\nref: v1.0.0\n",
            encoding="utf-8",
        )
        self.component = load_components(self.root)[0]

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_accepts_registered_published_stable_release(self):
        event = ComponentReleaseEvent(
            "D-Robotics/bsp-skills",
            "v1.0.1",
            "a" * 40,
            "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
            "2026-08-31T00:00:00Z",
            is_draft=False,
            is_prerelease=False,
        )

        self.assertEqual(decide_upgrade(self.component, event).action, "upgrade")

    def test_rejects_unknown_repo_prerelease_and_sha_mismatch(self):
        with self.assertRaisesRegex(ValidationError, "unregistered source repository"):
            validate_release_event(
                ComponentReleaseEvent(
                    "D-Robotics/unknown",
                    "v1.0.1",
                    "a" * 40,
                    "https://github.com/D-Robotics/unknown/releases/tag/v1.0.1",
                    "2026-08-31T00:00:00Z",
                ),
                self.component,
            )
        with self.assertRaisesRegex(ValidationError, "stable release tag"):
            validate_release_event(
                ComponentReleaseEvent(
                    self.component.repo,
                    "v1.0.1-rc.1",
                    "a" * 40,
                    "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1-rc.1",
                    "2026-08-31T00:00:00Z",
                ),
                self.component,
            )
        with self.assertRaisesRegex(ValidationError, "target SHA mismatch"):
            validate_release_event(
                ComponentReleaseEvent(
                    self.component.repo,
                    "v1.0.1",
                    "b" * 40,
                    "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
                    "2026-08-31T00:00:00Z",
                    is_draft=False,
                    is_prerelease=False,
                ),
                self.component,
                verified_target_sha="a" * 40,
            )

    def test_rejects_release_that_is_draft_or_prerelease(self):
        for event in (
            ComponentReleaseEvent(
                self.component.repo,
                "v1.0.1",
                "a" * 40,
                "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
                "2026-08-31T00:00:00Z",
                is_draft=True,
            ),
            ComponentReleaseEvent(
                self.component.repo,
                "v1.0.1",
                "a" * 40,
                "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
                "2026-08-31T00:00:00Z",
                is_prerelease=True,
            ),
        ):
            with self.subTest(event=event), self.assertRaisesRegex(
                ValidationError, "published, non-draft, non-prerelease"
            ):
                validate_release_event(event, self.component)

    def test_requires_boolean_release_status_facts(self):
        event = ComponentReleaseEvent(
            self.component.repo,
            "v1.0.1",
            "a" * 40,
            "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
            "2026-08-31T00:00:00Z",
            is_draft=None,
        )

        with self.assertRaisesRegex(
            ValidationError, "published, non-draft, non-prerelease"
        ):
            validate_release_event(event, self.component)

    def test_rejects_event_without_workflow_release_status_facts(self):
        event = ComponentReleaseEvent(
            self.component.repo,
            "v1.0.1",
            "a" * 40,
            "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
            "2026-08-31T00:00:00Z",
        )

        with self.assertRaisesRegex(
            ValidationError, "published, non-draft, non-prerelease"
        ):
            decide_upgrade(self.component, event)

    def test_rejects_noncanonical_url_and_invalid_sha(self):
        with self.assertRaisesRegex(ValidationError, "release URL"):
            validate_release_event(
                ComponentReleaseEvent(
                    self.component.repo,
                    "v1.0.1",
                    "a" * 40,
                    "https://example.invalid/release",
                    "2026-08-31T00:00:00Z",
                ),
                self.component,
            )
        with self.assertRaisesRegex(ValidationError, "40-character SHA"):
            validate_release_event(
                ComponentReleaseEvent(
                    self.component.repo,
                    "v1.0.1",
                    "not-a-sha",
                    "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
                    "2026-08-31T00:00:00Z",
                ),
                self.component,
            )

    def test_returns_noop_only_for_the_exact_current_ref(self):
        event = ComponentReleaseEvent(
            self.component.repo,
            "v1.0.0",
            "a" * 40,
            "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.0",
            "2026-08-31T00:00:00Z",
            is_draft=False,
            is_prerelease=False,
        )

        self.assertEqual(decide_upgrade(self.component, event).action, "noop")

    def test_rejects_a_stable_release_older_than_the_main_pin(self):
        """A delayed formal Release must not downgrade protected main."""
        newer_component = ComponentRef(
            self.component.component_id,
            self.component.repo,
            "v1.2.0",
            self.component.path,
        )
        delayed_event = ComponentReleaseEvent(
            self.component.repo,
            "v1.1.9",
            "a" * 40,
            "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.1.9",
            "2026-08-31T00:00:00Z",
            is_draft=False,
            is_prerelease=False,
        )

        with self.assertRaisesRegex(ValidationError, "older than the current"):
            decide_upgrade(newer_component, delayed_event)

    def test_stable_tag_contract_rejects_leading_zero_identifiers(self):
        """Every Hub entry point must share the source notifier's canonical SemVer."""
        invalid_tags = ("v01.2.3", "v1.02.3", "v1.2.03")
        for tag in invalid_tags:
            event = ComponentReleaseEvent(
                self.component.repo,
                tag,
                "a" * 40,
                f"https://github.com/D-Robotics/bsp-skills/releases/tag/{tag}",
                "2026-08-31T00:00:00Z",
                is_draft=False,
                is_prerelease=False,
            )
            with self.subTest(tag=tag), self.assertRaisesRegex(
                ValidationError, "stable release tag"
            ):
                decide_upgrade(self.component, event)

    def test_load_components_requires_unique_registered_repositories(self):
        (self.root / "components.d" / "duplicate.yml").write_text(
            "name: Duplicate\nrepo: D-Robotics/bsp-skills\nref: v1.0.1\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValidationError, "exactly one component"):
            load_components(self.root)

    def test_event_and_decision_are_immutable(self):
        event = ComponentReleaseEvent(
            self.component.repo,
            "v1.0.1",
            "a" * 40,
            "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
            "2026-08-31T00:00:00Z",
            is_draft=False,
            is_prerelease=False,
        )
        decision = decide_upgrade(self.component, event)

        with self.assertRaises((AttributeError, TypeError)):
            event.tag = "v1.0.2"
        with self.assertRaises((AttributeError, TypeError)):
            decision.action = "noop"


class ComponentUpgradeWorkflowContractTests(unittest.TestCase):
    def test_upgrade_workflow_is_dispatch_driven_and_dry_run_safe(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        document = yaml.load(workflow, Loader=yaml.BaseLoader)

        self.assertEqual(set(document["on"]), {"workflow_dispatch"})
        inputs = document["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(
            set(inputs),
            {
                "schema_version",
                "source_repo",
                "tag",
                "release_url",
                "target_sha",
                "published_at",
                "dry_run",
            },
        )
        self.assertNotIn("git push origin main", workflow)

    def test_branch_is_stable_per_component(self):
        self.assertEqual(
            branch_for("bsp-skills"), "bot/component-upgrade/bsp-skills"
        )

    def test_upgrade_workflow_validates_dispatches_before_pr_mutation(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        self.assertIn("RDK_RELEASE_DISPATCHER_ACTOR", workflow)
        self.assertIn("github.actor", workflow)
        self.assertIn("require-dispatch-authority", workflow)
        self.assertIn("gh api", workflow)
        self.assertIn("component_release.py", workflow)
        self.assertIn("component-upgrade-", workflow)

    def test_pr_upsert_preserves_main_and_applies_component_labels(self):
        script = read_workflow(".github/scripts/publish-component-pr.sh")
        self.assertIn('branch="bot/component-upgrade/${component_id}"', script)
        self.assertIn("component-upgrade", script)
        self.assertIn('source:${component_id}', script)
        self.assertNotIn("gh pr merge", script)
        self.assertNotIn("refs/heads/main", script)

    def test_workflow_splits_pr_and_branch_credentials_without_app_contents_write(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        document = yaml.load(workflow, Loader=yaml.BaseLoader)
        upsert = document["jobs"]["upsert-pr"]
        token_step = next(
            step
            for step in upsert["steps"]
            if step.get("uses") == "actions/create-github-app-token@v2"
        )

        self.assertEqual(
            token_step["with"]["app-id"],
            "${{ vars.RDK_COMPONENT_PR_BOT_APP_ID }}",
        )
        self.assertEqual(
            token_step["with"]["private-key"],
            "${{ secrets.RDK_COMPONENT_PR_BOT_PRIVATE_KEY }}",
        )
        self.assertIn("repositories: ${{ github.event.repository.name }}", workflow)
        self.assertEqual(token_step["with"]["permission-pull-requests"], "write")
        self.assertNotIn("permission-contents", token_step["with"])
        self.assertIn("RDK_COMPONENT_BRANCH_DEPLOY_KEY", workflow)
        self.assertNotIn("permission-contents: write", workflow)
        self.assertNotIn("RDK_RELEASE_BOT_", workflow)

    def test_source_derived_build_job_has_no_repository_write_credential(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        build_job = workflow.split("  build-proposal:", maxsplit=1)[1].split(
            "  upsert-pr:", maxsplit=1
        )[0]

        self.assertIn("contents: read", build_job)
        for forbidden in (
            "create-github-app-token",
            "RDK_COMPONENT_BRANCH_DEPLOY_KEY",
            "RDK_COMPONENT_PR_BOT_PRIVATE_KEY",
            "permission-contents: write",
            "git push",
            "gh pr ",
        ):
            self.assertNotIn(forbidden, build_job)

    def test_existing_bot_branch_is_never_checked_out_as_executable_input(self):
        script = read_workflow(".github/scripts/publish-component-pr.sh")
        self.assertIn('git switch --force-create "$branch" "$candidate_sha"', script)
        self.assertIn("--force-with-lease", script)
        self.assertNotIn('"origin/$branch"', script)

    def test_dry_run_and_verified_noop_cannot_reach_the_mutation_job(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        build_job = workflow.split("  build-proposal:", maxsplit=1)[1].split(
            "  upsert-pr:", maxsplit=1
        )[0]
        self.assertIn(
            "needs.validate.outputs.dry_run != 'true' && needs.validate.outputs.action == 'upgrade'",
            build_job,
        )
        self.assertIn("Verify a candidate noop has no mirror or artifact drift", workflow)

    def test_failed_upgrade_uses_only_job_scoped_github_token_for_issue_reporting(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        document = yaml.load(workflow, Loader=yaml.BaseLoader)
        reporter = document["jobs"]["report-failure"]

        self.assertEqual(reporter["permissions"]["issues"], "write")
        self.assertEqual(reporter["permissions"]["contents"], "read")
        reporter_text = workflow.split("  report-failure:", maxsplit=1)[1]
        self.assertIn("always()", reporter["if"])
        self.assertIn("component-upgrade-failure", reporter_text)
        self.assertIn("GH_TOKEN: ${{ github.token }}", reporter_text)
        self.assertNotIn("create-github-app-token", reporter_text)


class ComponentReconciliationWorkflowContractTests(unittest.TestCase):
    def test_reconciliation_is_scheduled_and_detects_drift_in_a_temporary_worktree(self):
        """Removing isolated reconciliation must fail this safety contract."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")

        self.assertIn("schedule:", workflow)
        self.assertIn("mktemp -d", workflow)
        self.assertIn("git worktree add --detach", workflow)
        self.assertIn("sync-components.sh", workflow)
        self.assertIn("build-plugins.sh", workflow)
        self.assertIn("regenerate-readme.sh", workflow)
        self.assertIn("git -C \"$verify_root\" add -A -f .", workflow)
        self.assertIn("git -C \"$verify_root\" diff --cached --quiet", workflow)
        self.assertNotIn("git -C \"$verify_root\" diff --quiet", workflow)

    def test_reconciliation_requires_a_published_formal_release_for_every_pin(self):
        """A peeled tag without a published formal Release remains invalid drift."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")

        self.assertIn('gh api "repos/$source_repo/releases/tags/$source_ref"', workflow)
        self.assertIn('gh api "repos/$source_repo/git/ref/tags/$source_ref"', workflow)
        self.assertIn('gh api "repos/$source_repo/git/tags/$tag_object_sha"', workflow)
        self.assertIn("validate-facts --facts-json", workflow)

    def test_reconciliation_reports_early_execution_failures_through_outputs(self):
        """Malformed YAML or a network failure must still reach the rolling Issue step."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")

        self.assertIn("reconcile_status=$?", workflow)
        self.assertIn("reconciliation execution failed before completing all checks", workflow)
        failure_index = workflow.index("reconciliation execution failed before completing all checks")
        output_index = workflow.index("output_delimiter=", failure_index)
        self.assertGreater(output_index, failure_index)

    def test_reconciliation_cannot_mutate_catalog_history_or_use_an_app_token(self):
        """Adding a catalog write, PR flow, or App token must violate the contract."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")

        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("component-upgrade-failure", workflow)
        self.assertIn("GH_TOKEN: ${{ github.token }}", workflow)
        for forbidden in (
            "git push",
            "git commit",
            "git branch",
            "git tag",
            "gh pr ",
            "create-github-app-token",
        ):
            self.assertNotIn(forbidden, workflow)

    def test_reconciliation_output_resists_multiline_ref_delimiter_injection(self):
        """An invalid multiline ref must not terminate the details output early."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")
        injected_ref = "v1.0.0\nEOF\nhas_drift=false"

        self.assertIn("EOF", injected_ref)
        self.assertIn(
            "output_delimiter=$(python3 -c 'import uuid; print(uuid.uuid4())')",
            workflow,
        )
        self.assertIn("printf 'details<<%s\\n' \"$output_delimiter\"", workflow)
        self.assertIn("printf '%s\\n' \"$output_delimiter\"", workflow)
        self.assertNotIn("details<<EOF", workflow)

    def test_reconciliation_cleanup_removes_results_tempfile(self):
        """The findings tempfile is removed on both successful and failed runs."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")
        cleanup = workflow.split("cleanup() {", maxsplit=1)[1].split("}\n", maxsplit=1)[0]

        self.assertIn('rm -f "$results_file"', cleanup)

    def test_reconciliation_generates_its_delimiter_with_python3(self):
        """Missing uuidgen must not skip the drift Issue reporting path."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")

        self.assertIn(
            "output_delimiter=$(python3 -c 'import uuid; print(uuid.uuid4())')",
            workflow,
        )
        self.assertNotIn("output_delimiter=$(uuidgen)", workflow)

    def test_legacy_sync_has_no_schedule_or_direct_commit(self):
        """The legacy workflow remains a manual, read-only verifier."""
        workflow = read_workflow(".github/workflows/sync-skills.yml")

        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("Commit and push changes", workflow)
        self.assertNotIn("git commit", workflow)
        self.assertNotIn("git push", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)

    def test_catalog_verifier_runs_as_a_read_only_pull_request_check(self):
        """Removing the bot-PR CI gate must fail this required-check contract."""
        workflow = read_workflow(".github/workflows/sync-skills.yml")
        document = yaml.load(workflow, Loader=yaml.BaseLoader)

        self.assertIn("pull_request", document["on"])
        self.assertEqual(document["permissions"], {"contents": "read"})
        self.assertIn("python3 -m unittest discover -s tests", workflow)
        self.assertIn(".github/scripts/validate.py --mode advisory", workflow)
        self.assertIn("generate_plugin_catalog.py --repo-root . --check-plugin-includes", workflow)
        self.assertNotIn("ref: main", workflow)
        for forbidden in ("git commit", "git push", "gh pr ", "git tag"):
            self.assertNotIn(forbidden, workflow)


class ComponentUpgradeHelperTests(unittest.TestCase):
    def test_renderer_preserves_literal_markdown_backticks_without_shell_execution(self):
        helper = load_upgrade_helper()

        body = helper.render_pr_body(
            component_name="BSP $(printf SHOULD_NOT_RUN)",
            component_id="bsp-skills",
            previous_tag="v1.0.0",
            new_tag="v1.0.1",
            release_url="https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
            source_sha="a" * 40,
            catalog_dirs=["bsp-env-setup"],
            generated_artifacts=["README.md"],
            test_result="PASS: test suite",
        )

        self.assertIn("BSP $(printf SHOULD_NOT_RUN)", body)
        self.assertIn("`bsp-skills`", body)
        self.assertIn("`v1.0.0`", body)
        self.assertIn("`v1.0.1`", body)
        self.assertIn("`" + "a" * 40 + "`", body)

    def test_renderer_rejects_nonstable_previous_tag(self):
        helper = load_upgrade_helper()

        with self.assertRaisesRegex(ValueError, "previous tag"):
            helper.render_pr_body(
                component_name="BSP Skills",
                component_id="bsp-skills",
                previous_tag="$(printf INJECTED)",
                new_tag="v1.0.1",
                release_url="https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
                source_sha="a" * 40,
                catalog_dirs=[],
                generated_artifacts=[],
                test_result="PASS",
            )

    def test_sync_summary_sha_mismatch_is_rejected_before_mutation(self):
        helper = load_upgrade_helper()
        summary = {
            "components": [{"source_sha": "b" * 40, "catalog_dirs": ["bsp-env-setup"]}]
        }

        with self.assertRaisesRegex(ValueError, "synchronized source SHA"):
            helper.validate_sync_summary(summary, "a" * 40)

    def test_label_preflight_rejects_missing_labels_before_writes(self):
        helper = load_upgrade_helper()

        with self.assertRaisesRegex(ValueError, "source:bsp-skills"):
            helper.require_labels(["component-upgrade"], "bsp-skills")

    def test_candidate_noop_with_drift_requires_a_repair_pr(self):
        helper = load_upgrade_helper()

        self.assertEqual(helper.resolve_action("noop", has_drift=True), "upgrade")
        self.assertEqual(helper.resolve_action("noop", has_drift=False), "noop")

    def test_tampered_existing_bot_branch_is_not_executed(self):
        """The proposal must run trusted-main helpers, not remote bot code."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            seed = temp / "seed"
            remote = temp / "remote.git"
            runner = temp / "runner"
            marker = temp / "tampered-branch-executed"
            scripts = seed / ".github" / "scripts"
            scripts.mkdir(parents=True)
            (seed / "components.d").mkdir()
            (seed / "tests").mkdir()
            (seed / "tests" / "__init__.py").write_text("", encoding="utf-8")
            (seed / "components.d" / "bsp-skills.yml").write_bytes(
                b"name: BSP Skills\nrepo: D-Robotics/bsp-skills\nref: v1.0.0\n"
            )
            (scripts / "publish-component-pr.sh").write_bytes(
                (ROOT / ".github" / "scripts" / "publish-component-pr.sh")
                .read_bytes()
                .replace(b"\r\n", b"\n")
            )
            (scripts / "publish-component-pr.sh").chmod(0o755)
            shutil.copy2(ROOT / ".github" / "scripts" / "component_upgrade.py", scripts)
            shutil.copy2(ROOT / ".github" / "scripts" / "release_contract.py", scripts)
            (scripts / "sync-components.sh").write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "while [[ $# -gt 0 ]]; do\n"
                "  if [[ $1 == --summary-file ]]; then summary=$2; shift 2; else shift; fi\n"
                "done\n"
                "printf '{\"components\":[{\"source_sha\":\"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\",\"catalog_dirs\":[\"bsp-env-setup\"]}]}' > \"$summary\"\n",
                encoding="utf-8",
            )
            (scripts / "build-plugins.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            (scripts / "regenerate-readme.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
            for script in scripts.glob("*.sh"):
                script.chmod(0o755)

            def git(*args: str, cwd: Path) -> None:
                subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

            git("init", "-b", "main", cwd=seed)
            git("add", ".", cwd=seed)
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "main", cwd=seed)
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            git("remote", "add", "origin", str(remote), cwd=seed)
            git("push", "origin", "main", cwd=seed)
            git("switch", "-c", "bot/component-upgrade/bsp-skills", cwd=seed)
            (scripts / "sync-components.sh").write_text(
                f"#!/usr/bin/env bash\ntouch '{marker.as_posix()}'\n",
                encoding="utf-8",
            )
            (scripts / "sync-components.sh").chmod(0o755)
            git("add", ".github/scripts/sync-components.sh", cwd=seed)
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "tamper", cwd=seed)
            git("push", "origin", "bot/component-upgrade/bsp-skills", cwd=seed)
            git("switch", "main", cwd=seed)
            subprocess.run(
                ["git", "-c", "core.autocrlf=false", "clone", "--branch", "main", str(remote), str(runner)],
                check=True,
                capture_output=True,
            )
            git("config", "core.autocrlf", "false", cwd=runner)
            remote_posix = remote.as_posix()
            if len(remote_posix) > 2 and remote_posix[1] == ":":
                remote_url_path = f"/mnt/{remote_posix[0].lower()}{remote_posix[2:]}"
            else:
                remote_url_path = remote_posix
            git("remote", "set-url", "origin", f"file://{remote_url_path}", cwd=runner)

            temp_posix = temp.as_posix()
            if len(temp_posix) > 2 and temp_posix[1] == ":":
                temp_shell_path = f"/mnt/{temp_posix[0].lower()}{temp_posix[2:]}"
            else:
                temp_shell_path = temp_posix

            patch_file = temp / "proposal.patch"
            metadata_file = temp / "proposal.json"
            summary_file = temp / "result.json"
            component_file = runner / "components.d" / "bsp-skills.yml"
            candidate_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=runner, check=True, text=True,
                capture_output=True,
            ).stdout.strip()
            component_file.write_bytes(
                b"name: BSP Skills\nrepo: D-Robotics/bsp-skills\nref: v1.0.1\n"
            )
            git("add", "components.d/bsp-skills.yml", cwd=runner)
            patch_file.write_bytes(
                subprocess.run(
                    ["git", "diff", "--cached", "--binary", "--full-index", "--no-ext-diff"],
                    cwd=runner,
                    check=True,
                    capture_output=True,
                ).stdout
            )
            git("restore", "--staged", "components.d/bsp-skills.yml", cwd=runner)
            git("restore", "components.d/bsp-skills.yml", cwd=runner)
            metadata_file.write_text(
                json.dumps(
                    {
                        "candidate_sha": candidate_sha,
                        "component_id": "bsp-skills",
                        "component_name": "BSP Skills",
                        "component_repo": "D-Robotics/bsp-skills",
                        "component_file": "components.d/bsp-skills.yml",
                        "previous_tag": "v1.0.0",
                        "new_tag": "v1.0.1",
                        "release_url": "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
                        "source_sha": "a" * 40,
                        "repair": False,
                        "catalog_dirs": ["bsp-env-setup"],
                        "generated_artifacts": [],
                        "staged_paths": ["components.d/bsp-skills.yml"],
                        "title": "chore: upgrade BSP Skills to v1.0.1",
                        "body": "Validated inert proposal body.\n",
                        "test_result": "PASS",
                    }
                ),
                encoding="utf-8",
            )

            fake_bin = temp / "fake-bin"
            fake_bin.mkdir()
            (fake_bin / "gh").write_bytes(
                b"#!/usr/bin/env bash\n"
                b"if [[ $1 == label ]]; then echo '[{\"name\":\"component-upgrade\"},{\"name\":\"source:bsp-skills\"}]'; "
                b"elif [[ $1 == pr && $2 == list ]]; then echo ''; "
                b"elif [[ $1 == pr && $2 == create ]]; then echo 'https://example.invalid/pr/1'; fi\n",
            )
            (fake_bin / "gh").chmod(0o755)
            env = dict(os.environ)
            for key in list(env):
                if key.upper() == "GITHUB_REPOSITORY":
                    del env[key]
            env.update(
                {
                    "GITHUB_REPOSITORY": "D-Robotics/rdk-skills",
                    "GH_TOKEN": "test-pr-token",
                }
            )
            command = " ".join(
                [
                    f'PATH="{temp_shell_path}/fake-bin:$PATH"', "GITHUB_REPOSITORY=D-Robotics/rdk-skills",
                    "GH_TOKEN=test-pr-token", "exec", "bash", ".github/scripts/publish-component-pr.sh",
                    "--patch-file", shlex.quote(f"{temp_shell_path}/proposal.patch"),
                    "--metadata-file", shlex.quote(f"{temp_shell_path}/proposal.json"),
                    "--summary-file", shlex.quote(f"{temp_shell_path}/result.json"),
                ]
            )
            result = subprocess.run(
                ["bash", "-c", command],
                cwd=runner,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
            )

            status = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=runner,
                text=True,
                capture_output=True,
            ).stdout
            shell_status = subprocess.run(
                ["bash", "-c", "git status --porcelain --untracked-files=all"],
                cwd=runner,
                text=True,
                capture_output=True,
            ).stdout
            self.assertEqual(
                result.returncode,
                0,
                f"{result.stderr}\nWindows status:\n{status}\nShell status:\n{shell_status}",
            )
            self.assertFalse(marker.exists(), "tampered bot-branch helper was executed")


if __name__ == "__main__":
    unittest.main()
