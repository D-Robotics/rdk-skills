# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Unit tests for component Release event validation."""

import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
        self.assertIn("rdk-component-release", workflow)
        self.assertIn("dry_run", workflow)
        self.assertNotIn("git push origin main", workflow)

    def test_branch_is_stable_per_component(self):
        self.assertEqual(
            branch_for("bsp-skills"), "bot/component-upgrade/bsp-skills"
        )

    def test_upgrade_workflow_validates_dispatches_before_pr_mutation(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        self.assertIn("actions/create-github-app-token@v2", workflow)
        self.assertIn("github.event.sender.login", workflow)
        self.assertIn("rdk-release-bot[bot]", workflow)
        self.assertIn("gh api", workflow)
        self.assertIn("component_release.py", workflow)
        self.assertIn("component-upgrade-", workflow)

    def test_pr_upsert_preserves_main_and_applies_component_labels(self):
        script = read_workflow(".github/scripts/upsert-component-pr.sh")
        self.assertIn('branch="bot/component-upgrade/${component_id}"', script)
        self.assertIn("component-upgrade", script)
        self.assertIn('source:${component_id}', script)
        self.assertNotIn("gh pr merge", script)
        self.assertNotIn("refs/heads/main", script)

    def test_workflow_scopes_the_mutation_token_to_the_current_hub_only(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        self.assertIn("repositories: ${{ github.event.repository.name }}", workflow)
        self.assertNotIn("permission-issues: write", workflow)

    def test_existing_bot_branch_is_never_checked_out_as_executable_input(self):
        script = read_workflow(".github/scripts/upsert-component-pr.sh")
        self.assertIn('git switch --force-create "$branch" origin/main', script)
        self.assertIn("--force-with-lease", script)
        self.assertNotIn('"origin/$branch"', script)

    def test_dry_run_and_verified_noop_cannot_reach_the_mutation_job(self):
        workflow = read_workflow(".github/workflows/component-upgrade.yml")
        mutation_job = workflow.split("  upsert-pr:", maxsplit=1)[1]
        self.assertIn(
            "needs.validate.outputs.dry_run != 'true' && needs.validate.outputs.action == 'upgrade'",
            mutation_job,
        )
        self.assertIn("Verify a candidate noop has no mirror or artifact drift", workflow)


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
        self.assertIn("git -C \"$verify_root\" diff --quiet", workflow)

    def test_reconciliation_cannot_mutate_catalog_history_or_use_an_app_token(self):
        """Adding a catalog write, PR flow, or App token must violate the contract."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")

        self.assertIn("contents: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("component-upgrade-failure", workflow)
        self.assertIn("GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}", workflow)
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
        self.assertIn("output_delimiter=$(uuidgen)", workflow)
        self.assertIn("printf 'details<<%s\\n' \"$output_delimiter\"", workflow)
        self.assertIn("printf '%s\\n' \"$output_delimiter\"", workflow)
        self.assertNotIn("details<<EOF", workflow)

    def test_reconciliation_cleanup_removes_results_tempfile(self):
        """The findings tempfile is removed on both successful and failed runs."""
        workflow = read_workflow(".github/workflows/reconcile-components.yml")
        cleanup = workflow.split("cleanup() {", maxsplit=1)[1].split("}\n", maxsplit=1)[0]

        self.assertIn('rm -f "$results_file"', cleanup)

    def test_legacy_sync_has_no_schedule_or_direct_commit(self):
        """The legacy workflow remains a manual, read-only verifier."""
        workflow = read_workflow(".github/workflows/sync-skills.yml")

        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("Commit and push changes", workflow)
        self.assertNotIn("git commit", workflow)
        self.assertNotIn("git push", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)


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
            (seed / "components.d" / "bsp-skills.yml").write_text(
                "name: BSP Skills\nrepo: D-Robotics/bsp-skills\nref: v1.0.0\n",
                encoding="utf-8",
            )
            (scripts / "upsert-component-pr.sh").write_bytes(
                (ROOT / ".github" / "scripts" / "upsert-component-pr.sh")
                .read_bytes()
                .replace(b"\r\n", b"\n")
            )
            (scripts / "upsert-component-pr.sh").chmod(0o755)
            shutil.copy2(ROOT / ".github" / "scripts" / "component_upgrade.py", scripts)
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
            remote_posix = remote.as_posix()
            if len(remote_posix) > 2 and remote_posix[1] == ":":
                remote_url_path = f"/mnt/{remote_posix[0].lower()}{remote_posix[2:]}"
            else:
                remote_url_path = remote_posix
            git("remote", "set-url", "origin", f"file://{remote_url_path}", cwd=runner)

            fake_bin = runner
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
                }
            )
            command = " ".join(
                [
                    'PATH=".:$PATH"', "GITHUB_REPOSITORY=D-Robotics/rdk-skills",
                    "exec", "bash", ".github/scripts/upsert-component-pr.sh",
                    "--component", "bsp-skills",
                    "--tag", "v1.0.1",
                    "--release-url", "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
                    "--source-sha", "a" * 40,
                    "--summary-file", shlex.quote(str(temp / "result.json")),
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

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(marker.exists(), "tampered bot-branch helper was executed")


if __name__ == "__main__":
    unittest.main()
