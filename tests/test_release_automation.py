# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Behavioral regressions for release-automation security boundaries."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / ".github" / "scripts" / "release_contract.py"
UPGRADE_PATH = ROOT / ".github" / "scripts" / "component_upgrade.py"


def load_contract():
    spec = importlib.util.spec_from_file_location("release_contract", CONTRACT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_upgrade():
    spec = importlib.util.spec_from_file_location("component_upgrade_safety", UPGRADE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GitHubResponseTests(unittest.TestCase):
    def test_extracts_numeric_404_from_current_gh_http2_status(self):
        """Changing protocol spelling must not turn an absent Release into an error."""
        contract = load_contract()
        response = "HTTP/2.0 404 Not Found\r\ncontent-type: application/json\r\n\r\n{}"

        self.assertEqual(contract.github_http_status(response), 404)


class HubReleaseRecoveryTests(unittest.TestCase):
    def test_recovery_excludes_the_half_release_tag_when_selecting_previous_tag(self):
        """Recovery notes must use the same prior-tag boundary as the failed normal run."""
        contract = load_contract()

        self.assertEqual(
            contract.previous_release_tag(
                ["v1.0.0", "v1.1.0", "v1.2.0"], destination_tag="v1.2.0"
            ),
            "v1.1.0",
        )
        self.assertEqual(
            contract.previous_release_tag(
                ["v1.0.0", "v1.1.0"], destination_tag="v1.2.0"
            ),
            "v1.1.0",
        )

    def test_recovery_notes_must_match_the_digest_preserved_in_the_tag(self):
        """A recovery retry cannot silently publish different validated notes."""
        contract = load_contract()
        notes = b"Validated release notes.\n"
        digest = contract.release_notes_sha256(notes)
        tag_object = (
            "object " + "a" * 40 + "\n"
            "type commit\n"
            "tag v1.2.3\n"
            "tagger Test <test@example.invalid> 0 +0000\n\n"
            "RDK Skills v1.2.3\n\n"
            f"Release-Notes-SHA256: {digest}\n"
        )

        contract.require_release_notes_digest(tag_object, notes)
        with self.assertRaisesRegex(ValueError, "do not match"):
            contract.require_release_notes_digest(tag_object, b"Changed notes.\n")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            contract.require_release_notes_digest(
                tag_object + f"Release-Notes-SHA256: {digest}\n", notes
            )

    def test_recovery_accepts_only_an_exact_existing_annotated_tag_without_release(self):
        """Release-only recovery must never create, move, or replace a tag."""
        contract = load_contract()
        candidate = "a" * 40
        tag_object = "b" * 40
        exact_tag = (
            f"{tag_object}\trefs/tags/v1.2.3\n"
            f"{candidate}\trefs/tags/v1.2.3^{{}}\n"
        )

        self.assertEqual(
            contract.plan_release_destination(
                exact_tag,
                tag="v1.2.3",
                candidate_sha=candidate,
                release_status=404,
                recover_existing_tag=True,
            ),
            "release-only",
        )

        rejected = (
            ("", True, "recovery requires an existing"),
            (exact_tag, False, "destination tag already exists"),
            (
                exact_tag.replace(candidate, "c" * 40),
                True,
                "does not resolve to the candidate",
            ),
        )
        for refs, recovery, message in rejected:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                contract.plan_release_destination(
                    refs,
                    tag="v1.2.3",
                    candidate_sha=candidate,
                    release_status=404,
                    recover_existing_tag=recovery,
                )

    def test_normal_publication_requires_both_tag_and_release_to_be_absent(self):
        """A present Release or recovery request without a tag must fail closed."""
        contract = load_contract()
        candidate = "a" * 40

        self.assertEqual(
            contract.plan_release_destination(
                "",
                tag="v1.2.3",
                candidate_sha=candidate,
                release_status=404,
                recover_existing_tag=False,
            ),
            "create-tag",
        )
        with self.assertRaisesRegex(ValueError, "GitHub Release already exists"):
            contract.plan_release_destination(
                "",
                tag="v1.2.3",
                candidate_sha=candidate,
                release_status=200,
                recover_existing_tag=False,
            )


def release_fact(*, published_at="2026-09-01T00:00:00Z", source_sha=None):
    """Return a complete hand-authored formal Release API fixture."""
    source_sha = source_sha or "c" * 40
    return {
        "repo": "D-Robotics/bsp-skills",
        "tag": "v1.2.3",
        "release": {
            "tag_name": "v1.2.3",
            "draft": False,
            "prerelease": False,
            "published_at": published_at,
            "html_url": "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.2.3",
        },
        "tag_ref": {"object": {"type": "tag", "sha": "b" * 40}},
        "tag_object": {
            "sha": "b" * 40,
            "object": {"type": "commit", "sha": source_sha},
        },
    }


class SourceReleaseEvidenceTests(unittest.TestCase):
    def test_rejects_unpublished_or_noncanonical_release_evidence(self):
        """Reconciliation must report a tag that lacks a published formal Release."""
        contract = load_contract()
        unpublished = release_fact()
        unpublished["release"]["draft"] = True
        with self.assertRaisesRegex(ValueError, "published formal source Release"):
            contract.normalize_release_facts([unpublished])

        noncanonical = release_fact()
        noncanonical["release"]["html_url"] = "https://example.invalid/release"
        with self.assertRaisesRegex(ValueError, "published formal source Release"):
            contract.normalize_release_facts([noncanonical])

    def test_environment_revalidation_rejects_any_changed_source_release_tuple(self):
        """Approval latency must not permit tag, publication, or SHA facts to go stale."""
        contract = load_contract()
        expected = [release_fact()]
        self.assertEqual(
            contract.require_release_facts_unchanged(expected, [release_fact()]),
            contract.normalize_release_facts(expected),
        )

        changed_cases = (
            [release_fact(published_at="2026-09-02T00:00:00Z")],
            [release_fact(source_sha="d" * 40)],
        )
        for current in changed_cases:
            with self.subTest(current=current), self.assertRaisesRegex(
                ValueError, "changed during Environment approval"
            ):
                contract.require_release_facts_unchanged(expected, current)


class ProposalStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "components.d").mkdir()
        (self.root / "skills" / "catalog").mkdir(parents=True)
        (self.root / "components.d" / "bsp.yml").write_text(
            "repo: D-Robotics/bsp-skills\nref: v1.0.0\n",
            encoding="utf-8",
        )
        (self.root / "skills" / "catalog" / "existing.txt").write_text(
            "base\n", encoding="utf-8"
        )
        (self.root / "README.md").write_text("base\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("*.secret\n", encoding="utf-8")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test Runner")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("add", ".")
        self.git("commit", "-qm", "base")

    def tearDown(self):
        self.temp_dir.cleanup()

    def git(self, *args):
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            text=True,
            capture_output=True,
        )

    def test_force_stages_additive_and_ignored_files_inside_selected_catalog(self):
        """A source file matching a Hub ignore rule must still enter the proposal."""
        helper = load_upgrade()
        (self.root / "skills" / "catalog" / "new.txt").write_text(
            "new\n", encoding="utf-8"
        )
        (self.root / "skills" / "catalog" / "credentials.secret").write_text(
            "inert fixture\n", encoding="utf-8"
        )

        paths = helper.stage_and_validate_proposal(
            self.root,
            component_file="components.d/bsp.yml",
            catalog_dirs=["catalog"],
            repair=True,
        )

        self.assertIn("skills/catalog/new.txt", paths)
        self.assertIn("skills/catalog/credentials.secret", paths)
        staged = self.git("diff", "--cached", "--name-only").stdout.splitlines()
        self.assertIn("skills/catalog/credentials.secret", staged)

    def test_rejects_untracked_and_ignored_files_outside_the_allowlist(self):
        """A generator must not smuggle an unexpected path into or beside the patch."""
        helper = load_upgrade()
        for name in ("unexpected.txt", "unexpected.secret"):
            with self.subTest(name=name):
                path = self.root / name
                path.write_text("unexpected\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "unexpected .* path"):
                    helper.stage_and_validate_proposal(
                        self.root,
                        component_file="components.d/bsp.yml",
                        catalog_dirs=["catalog"],
                        repair=True,
                    )
                path.unlink()


class UpgradeOrderingAndAuthorityTests(unittest.TestCase):
    def test_delayed_event_cannot_replace_a_newer_open_proposal(self):
        """The stable component branch must move only forward under release events."""
        helper = load_upgrade()
        helper.require_release_order(
            incoming_tag="v1.2.0",
            main_tag="v1.0.0",
            proposal_tag="v1.1.0",
        )
        with self.assertRaisesRegex(ValueError, "older than the existing proposal"):
            helper.require_release_order(
                incoming_tag="v1.1.9",
                main_tag="v1.0.0",
                proposal_tag="v1.2.0",
            )

    def test_only_expected_dispatcher_actor_can_request_non_dry_run(self):
        """Maintainers may dry-run manually but cannot impersonate automated writes."""
        helper = load_upgrade()
        helper.require_dispatch_authority(
            dry_run=False,
            actor="rdk-release-dispatcher[bot]",
            expected_actor="rdk-release-dispatcher[bot]",
        )
        helper.require_dispatch_authority(
            dry_run=True,
            actor="maintainer",
            expected_actor="",
        )
        with self.assertRaisesRegex(ValueError, "expected dispatcher bot"):
            helper.require_dispatch_authority(
                dry_run=False,
                actor="maintainer",
                expected_actor="rdk-release-dispatcher[bot]",
            )


class UpgradeFailureReportTests(unittest.TestCase):
    def test_failure_issue_is_bounded_and_uses_only_redacted_structured_diagnostics(self):
        """Pre-validation failures must not copy payloads, logs, or credentials to Issues."""
        helper = load_upgrade()
        secret = "ghp_SUPER_SECRET_VALUE"

        title, body = helper.render_failure_issue(
            component_id=None,
            source_repo=f"bad\nTOKEN={secret}",
            tag=f"v1.2.3\n{secret}",
            job_results={
                "validate": "failure",
                "build-proposal": "skipped",
                "upsert-pr": "skipped",
                secret: secret,
            },
            run_url="https://github.com/D-Robotics/rdk-skills/actions/runs/1234",
        )

        self.assertEqual(title, "Component upgrade failure tracker: general")
        self.assertLessEqual(len(body), 2000)
        self.assertNotIn(secret, title + body)
        self.assertNotIn("TOKEN=", body)
        self.assertIn("validate: failure", body)
        self.assertIn("Most recent run", body)

    def test_failure_issue_replaces_oversized_valid_looking_fields(self):
        """Attacker-sized inputs must not prevent the redacted tracker from rendering."""
        helper = load_upgrade()

        title, body = helper.render_failure_issue(
            component_id="a" * 5000,
            source_repo=f"{'a' * 5000}/repo",
            tag=f"v{'1' * 5000}.2.3",
            job_results={"validate": "failure"},
            run_url="https://github.com/D-Robotics/rdk-skills/actions/runs/1234",
        )

        self.assertEqual(title, "Component upgrade failure tracker: general")
        self.assertLessEqual(len(body), 2000)
        self.assertNotIn("a" * 100, title + body)
        self.assertIn("**Source:** `unavailable`", body)
        self.assertIn("**Tag:** `unavailable`", body)


if __name__ == "__main__":
    unittest.main()
