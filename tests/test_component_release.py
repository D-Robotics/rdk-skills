# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Unit tests for component Release event validation."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / ".github" / "scripts" / "component_release.py"


def read_workflow(relative_path: str) -> str:
    """Return a workflow contract as UTF-8 text."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


def branch_for(component_id: str) -> str:
    """Return the one stable upgrade branch for a component."""
    return f"bot/component-upgrade/{component_id}"


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


if __name__ == "__main__":
    unittest.main()
