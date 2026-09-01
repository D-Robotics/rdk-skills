# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Contracts for rendering a protected, mixed-component Hub Release."""

import importlib.util
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT / ".github" / "scripts" / "render_hub_release_notes.py"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "release-hub.yml"
RELEASE_APP_TOKEN_ACTION = (
    "actions/create-github-app-token@fee1f7d63c2ff003460e3d139729b119787bc349"
)
CHECKOUT_ACTION = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
UPLOAD_ARTIFACT_ACTION = (
    "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02"
)
DOWNLOAD_ARTIFACT_ACTION = (
    "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093"
)
PINNED_RELEASE_ACTIONS = {
    CHECKOUT_ACTION,
    UPLOAD_ARTIFACT_ACTION,
    DOWNLOAD_ARTIFACT_ACTION,
    RELEASE_APP_TOKEN_ACTION,
}


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_hub_release_notes", RENDERER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mixed_components():
    return [
        {
            "name": "BSP Skills",
            "repo": "D-Robotics/bsp-skills",
            "ref": "v1.0.1",
            "release_url": "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
            "formal_release": True,
        },
        {
            "name": "RDK Device Skills",
            "repo": "D-Robotics/rdk-device-skills",
            "ref": "v1.2.0",
            "release_url": "https://github.com/D-Robotics/rdk-device-skills/releases/tag/v1.2.0",
            "formal_release": True,
        },
        {
            "name": "OE Skills X5",
            "repo": "D-Robotics/oe-skills-x5",
            "ref": "v1.0.0",
            "release_url": "https://github.com/D-Robotics/oe-skills-x5/releases/tag/v1.0.0",
            "formal_release": True,
        },
        {
            "name": "OE Skills S",
            "repo": "D-Robotics/oe-skills-s",
            "ref": "v1.3.4",
            "release_url": "https://github.com/D-Robotics/oe-skills-s/releases/tag/v1.3.4",
            "formal_release": True,
        },
    ]


def upgrades():
    return [
        {
            "number": 42,
            "title": "chore: upgrade BSP Skills to v1.0.1",
            "merged_at": "2026-09-01T00:00:00Z",
            "component": "BSP Skills",
            "from_tag": "v1.0.0",
            "to_tag": "v1.0.1",
            "release_url": "https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1",
            "source_sha": "5" * 40,
        }
    ]


def release_facts(records):
    """Hand-authored GitHub API fixtures for published annotated source tags."""
    facts = []
    for index, record in enumerate(records, start=1):
        tag_object_sha = f"{index:x}" * 40
        source_sha = f"{index + 4:x}" * 40
        facts.append(
            {
                "repo": record["repo"],
                "tag": record["ref"],
                "release": {
                    "tag_name": record["ref"],
                    "draft": False,
                    "prerelease": False,
                    "published_at": "2026-09-01T00:00:00Z",
                    "html_url": f"https://github.com/{record['repo']}/releases/tag/{record['ref']}",
                },
                "tag_ref": {"object": {"type": "tag", "sha": tag_object_sha}},
                "tag_object": {"object": {"type": "commit", "sha": source_sha}},
            }
        )
    return facts


class HubReleaseNoteTests(unittest.TestCase):
    def setUp(self):
        self.renderer = load_renderer()

    def test_release_title_is_exact_and_component_versions_are_independent(self):
        """Collapsing component refs to the Hub version must fail this contract."""
        components = mixed_components()
        notes = self.renderer.render_notes(
            "1.0.1", components, upgrades(), release_facts=release_facts(components)
        )

        self.assertEqual(notes.title, "RDK Skills v1.0.1")
        self.assertIn("BSP Skills | `v1.0.1`", notes.body)
        self.assertIn("OE Skills X5 | `v1.0.0`", notes.body)
        self.assertIn("BSP Skills: `v1.0.0` to `v1.0.1`", notes.body)
        self.assertFalse(self.renderer.contains_cjk(notes.body))

    def test_rejects_non_english_additions_and_unresolved_template_markers(self):
        """Accepting CJK text or publishing a template placeholder is a release defect."""
        components = mixed_components()
        with self.assertRaisesRegex(ValueError, "English"):
            self.renderer.render_notes(
                "1.0.1", components, upgrades(), "新增说明", release_facts(components)
            )
        with self.assertRaisesRegex(ValueError, "marker"):
            self.renderer.render_notes(
                "1.0.1", components, upgrades(), "{{REPLACE_ME}}", release_facts(components)
            )

    def test_rejects_invalid_versions_duplicate_components_and_unpublished_sources(self):
        """Weak input validation could publish a Hub tag with unverifiable source content."""
        components = mixed_components()
        with self.assertRaisesRegex(ValueError, "version"):
            self.renderer.render_notes(
                "v1.0.1", components, upgrades(), release_facts=release_facts(components)
            )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.renderer.render_notes(
                "1.0.1", components + [components[0]], upgrades(), release_facts=release_facts(components)
            )
        unpublished = release_facts(components)
        unpublished[0]["release"]["draft"] = True
        with self.assertRaisesRegex(ValueError, "formal source Release"):
            self.renderer.render_notes("1.0.1", components, upgrades(), release_facts=unpublished)

    def test_rejects_leading_zero_semver_at_every_release_note_boundary(self):
        """Manual Hub publication must accept the same canonical SemVer as sources."""
        components = mixed_components()
        for version in ("01.2.3", "1.02.3", "1.2.03"):
            with self.subTest(version=version), self.assertRaisesRegex(ValueError, "version"):
                self.renderer.render_notes(
                    version,
                    components,
                    upgrades(),
                    release_facts=release_facts(components),
                )

        invalid_components = mixed_components()
        invalid_components[0]["ref"] = "v01.2.3"
        with self.assertRaisesRegex(ValueError, "component tag"):
            self.renderer.render_notes(
                "1.2.3",
                invalid_components,
                upgrades(),
                release_facts=release_facts(invalid_components),
            )

    def test_accepts_existing_oe_component_upgrade_metadata_names(self):
        """Rejecting the existing component-upgrade PR name would block an otherwise valid release."""
        oe_upgrade = upgrades()
        oe_upgrade[0].update(
            {
                "component": "OE Tool Chain (X5)",
                "from_tag": "v0.9.9",
                "to_tag": "v1.0.0",
                "release_url": "https://github.com/D-Robotics/oe-skills-x5/releases/tag/v1.0.0",
                "source_sha": "7" * 40,
            }
        )

        components = mixed_components()
        notes = self.renderer.render_notes(
            "1.0.1", components, oe_upgrade, release_facts=release_facts(components)
        )

        self.assertIn("OE Skills X5: `v0.9.9` to `v1.0.0`", notes.body)

    def test_api_facts_verify_published_annotated_source_releases(self):
        """Treating a PR-supplied URL and boolean as proof must fail this release gate."""
        raw_components = mixed_components()
        verified = self.renderer.verify_formal_source_releases(
            raw_components, release_facts(raw_components)
        )

        self.assertEqual(verified[0]["source_sha"], "5" * 40)
        tampered = release_facts(raw_components)
        tampered[0]["tag_ref"]["object"]["type"] = "commit"
        with self.assertRaisesRegex(ValueError, "annotated"):
            self.renderer.verify_formal_source_releases(raw_components, tampered)
        wrong_release = release_facts(raw_components)
        wrong_release[0]["release"]["html_url"] = "https://example.invalid/not-a-release"
        with self.assertRaisesRegex(ValueError, "formal source Release"):
            self.renderer.verify_formal_source_releases(raw_components, wrong_release)
        prerelease = release_facts(raw_components)
        prerelease[0]["release"]["prerelease"] = True
        with self.assertRaisesRegex(ValueError, "formal source Release"):
            self.renderer.verify_formal_source_releases(raw_components, prerelease)
        bad_target = release_facts(raw_components)
        bad_target[0]["tag_object"]["object"]["sha"] = "not-a-sha"
        with self.assertRaisesRegex(ValueError, "resolve to a commit"):
            self.renderer.verify_formal_source_releases(raw_components, bad_target)
        missing = release_facts(raw_components)[1:]
        with self.assertRaisesRegex(ValueError, "formal source Release"):
            self.renderer.verify_formal_source_releases(raw_components, missing)

    def test_rejects_duplicate_component_upgrade_metadata_entries(self):
        """Repeating one merged PR must not duplicate public release-note history."""
        components = mixed_components()
        with self.assertRaisesRegex(ValueError, "duplicate component-upgrade"):
            self.renderer.render_notes(
                "1.0.1", components, upgrades() + upgrades(), release_facts=release_facts(components)
            )

    def test_upgrade_body_requires_source_sha_and_matches_the_verified_tag_target(self):
        """A PR body SHA must be present, valid, and equal the dereferenced formal Release tag."""
        components = mixed_components()
        facts = release_facts(components)
        body = """| Component | BSP Skills (`bsp-skills`) |
| Previous tag | `v1.0.0` |
| New tag | `v1.0.1` |
| Source Release | https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1 |
| Source SHA | `5555555555555555555555555555555555555555` |"""
        metadata = self.renderer.parse_merged_upgrade_metadata(
            {"number": 42, "merged_at": "2026-09-01T00:00:00Z", "body": body}
        )
        verified = self.renderer.verify_formal_upgrade_releases([metadata], facts)
        self.assertEqual(verified[0]["source_sha"], "5" * 40)

        with self.assertRaisesRegex(ValueError, "Source SHA"):
            self.renderer.parse_merged_upgrade_metadata(
                {"number": 42, "merged_at": "2026-09-01T00:00:00Z", "body": body.replace("\n| Source SHA | `5555555555555555555555555555555555555555` |", "")}
            )
        invalid = body.replace("5555555555555555555555555555555555555555", "not-a-sha")
        with self.assertRaisesRegex(ValueError, "Source SHA"):
            self.renderer.parse_merged_upgrade_metadata(
                {"number": 42, "merged_at": "2026-09-01T00:00:00Z", "body": invalid}
            )
        mismatched = body.replace("5555555555555555555555555555555555555555", "b" * 40)
        metadata = self.renderer.parse_merged_upgrade_metadata(
            {"number": 42, "merged_at": "2026-09-01T00:00:00Z", "body": mismatched}
        )
        with self.assertRaisesRegex(ValueError, "Source SHA does not match"):
            self.renderer.verify_formal_upgrade_releases([metadata], facts)

    def test_upgrade_body_rejects_repeated_security_fields_instead_of_using_the_first(self):
        """Appending an assertion must not let a parser silently trust the first table row."""
        body = """| Component | BSP Skills (`bsp-skills`) |
| Previous tag | `v1.0.0` |
| New tag | `v1.0.1` |
| Source Release | https://github.com/D-Robotics/bsp-skills/releases/tag/v1.0.1 |
| Source SHA | `5555555555555555555555555555555555555555` |"""
        common = {"number": 42, "merged_at": "2026-09-01T00:00:00Z"}
        duplicate_cases = (
            ("same SHA", body + "\n| Source SHA | `5555555555555555555555555555555555555555` |"),
            ("mismatched SHA", body + "\n| Source SHA | `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb` |"),
            ("invalid SHA", body + "\n| Source SHA | `not-a-sha` |"),
        )
        for name, repeated_body in duplicate_cases:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Source SHA"):
                self.renderer.parse_merged_upgrade_metadata({**common, "body": repeated_body})
        with self.assertRaisesRegex(ValueError, "Component"):
            self.renderer.parse_merged_upgrade_metadata(
                {**common, "body": body + "\n| Component | BSP Skills (`bsp-skills`) |"}
            )


class HubReleaseWorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.workflow = yaml.load(self.text, Loader=yaml.BaseLoader)
        self.jobs = self.workflow["jobs"]

    @staticmethod
    def script(job):
        return "\n".join(step.get("run", "") for step in job["steps"])

    def test_recovery_is_explicit_environment_protected_and_exact_tag_only(self):
        """A half-release retry may create only the missing Release for the exact tag."""
        self.assertEqual(set(self.workflow["on"]), {"workflow_dispatch"})
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        inputs = self.workflow["on"]["workflow_dispatch"]["inputs"]
        self.assertEqual(inputs["recover_existing_tag"]["type"], "boolean")
        self.assertEqual(inputs["recover_existing_tag"]["default"], "false")
        self.assertEqual(self.jobs["publish"]["environment"], "release")
        self.assertEqual(self.jobs["publish"]["permissions"], {"contents": "read"})
        for name, job in self.jobs.items():
            self.assertNotEqual((job.get("permissions") or {}).get("contents"), "write", name)
            for step in job["steps"]:
                action = step.get("uses")
                if action:
                    self.assertRegex(
                        action,
                        r"^[^@\s]+@[0-9a-f]{40}$",
                        f"{name}: {action}",
                    )
                    self.assertIn(action, PINNED_RELEASE_ACTIONS)
                if action == CHECKOUT_ACTION:
                    self.assertEqual(step["with"].get("persist-credentials"), "false", name)

        script = self.script(self.jobs["publish"])
        self.assertIn("destination-state", script)
        self.assertIn("release-only", script)
        self.assertIn("verify-notes-hash", script)
        self.assertIn("Release-Notes-SHA256", script)
        self.assertIn('if [[ "$destination_action" == create-tag ]]', script)
        self.assertLess(script.index("destination-state"), script.index("git push"))

        preflight = self.script(self.jobs["preflight"])
        self.assertIn('recovered_sha=$(awk', preflight)
        self.assertIn('git switch --detach "$candidate_sha"', preflight)
        self.assertIn('git merge-base --is-ancestor "$candidate_sha" origin/main', preflight)
        self.assertIn("release_contract.py previous-tag", preflight)
        self.assertIn('if [[ "$PREFLIGHT_ACTION" == create-tag ]]', script)

    def test_publish_uses_an_environment_scoped_release_app_token_only_for_writes(self):
        """Tag and Release writes require the exact Hub-only Release App capability."""
        publish = self.jobs["publish"]
        self.assertEqual(publish["environment"], "release")
        self.assertEqual(publish["permissions"], {"contents": "read"})

        token_steps = [
            step
            for step in publish["steps"]
            if (step.get("uses") or "").startswith("actions/create-github-app-token@")
        ]
        self.assertEqual(len(token_steps), 1)
        token_step = token_steps[0]
        self.assertEqual(token_step["uses"], RELEASE_APP_TOKEN_ACTION)
        self.assertEqual(token_step.get("id"), "release-app")
        self.assertEqual(
            token_step["with"],
            {
                "app-id": "${{ vars.RDK_HUB_RELEASE_APP_ID }}",
                "private-key": "${{ secrets.RDK_HUB_RELEASE_APP_PRIVATE_KEY }}",
                "owner": "D-Robotics",
                "repositories": "rdk-skills",
                "permission-contents": "write",
            },
        )

        revalidate_steps = [
            step
            for step in publish["steps"]
            if step.get("name") == "Revalidate approved Release evidence"
        ]
        publish_steps = [
            step
            for step in publish["steps"]
            if step.get("name") == "Publish the immutable destination"
        ]
        self.assertEqual(len(revalidate_steps), 1)
        self.assertEqual(len(publish_steps), 1)
        revalidate_step = revalidate_steps[0]
        publish_step = publish_steps[0]
        self.assertLess(publish["steps"].index(revalidate_step), publish["steps"].index(token_step))
        self.assertLess(publish["steps"].index(token_step), publish["steps"].index(publish_step))
        self.assertEqual(revalidate_step["env"]["GH_TOKEN"], "${{ github.token }}")
        self.assertNotIn("RDK_HUB_RELEASE_TOKEN", revalidate_step["env"])
        self.assertIn("release_contract.py notes-sha", revalidate_step["run"])
        self.assertEqual(
            publish_step["env"]["RDK_HUB_RELEASE_TOKEN"],
            "${{ steps.release-app.outputs.token }}",
        )
        self.assertEqual(
            publish_step["env"]["APPROVED_NOTES_SHA"],
            "${{ steps.approved.outputs.notes_sha }}",
        )
        self.assertNotIn("GH_TOKEN", publish_step["env"])
        self.assertEqual(
            sum(
                (step.get("uses") or "").startswith("actions/create-github-app-token@")
                for job in self.jobs.values()
                for step in job["steps"]
            ),
            1,
        )
        self.assertEqual(self.text.count("secrets.RDK_HUB_RELEASE_APP_PRIVATE_KEY"), 1)

        script = " ".join(publish_step["run"].split())
        self.assertIn(
            "git -c user.name=rdk-hub-release "
            "-c user.email=rdk-hub-release@users.noreply.github.com tag -a",
            script,
        )
        self.assertIn('[[ "$notes_sha" == "$APPROVED_NOTES_SHA" ]]', script)
        self.assertLess(
            script.index('[[ "$notes_sha" == "$APPROVED_NOTES_SHA" ]]'),
            script.index("git -c user.name=rdk-hub-release"),
        )
        self.assertIn(
            'git push "https://x-access-token:${RDK_HUB_RELEASE_TOKEN}'
            '@github.com/${GITHUB_REPOSITORY}.git" "refs/tags/$tag:refs/tags/$tag"',
            script,
        )
        self.assertIn('GH_TOKEN="$RDK_HUB_RELEASE_TOKEN" gh release create', script)
        self.assertIn('gh release create "$tag" --repo "$GITHUB_REPOSITORY" --verify-tag', script)
        self.assertNotIn("x-access-token:${GH_TOKEN}", script)
        self.assertNotIn("git remote set-url", script)

    def test_publish_revalidates_every_source_release_fact_after_approval(self):
        """Environment approval must not freeze mutable source Release evidence."""
        preflight = self.script(self.jobs["preflight"])
        publish = self.script(self.jobs["publish"])
        for endpoint in ("releases/tags", "git/ref/tags", "git/tags"):
            self.assertIn(endpoint, preflight)
            self.assertIn(endpoint, publish)
        self.assertIn('["git", "merge-base", "--is-ancestor", sha, "HEAD"]', preflight)
        self.assertIn("compare-facts", publish)
        first_write = min(
            publish.index(marker)
            for marker in ("tag -a", "git push", "gh release create")
        )
        self.assertLess(publish.index("compare-facts"), first_write)

    def test_destination_status_is_protocol_independent_and_evidence_is_complete(self):
        """A real HTTP/2.0 404 must reach the state machine without string matching."""
        preflight = self.script(self.jobs["preflight"])
        publish = self.script(self.jobs["publish"])
        self.assertIn("release_contract.py http-status", preflight)
        self.assertIn("release_contract.py http-status", publish)
        self.assertNotIn("HTTP/2 404", self.text)
        self.assertNotIn("HTTP/1.1 404", self.text)
        upload = next(
            step
            for step in self.jobs["preflight"]["steps"]
            if step.get("uses") == UPLOAD_ARTIFACT_ACTION
        )
        self.assertEqual(upload["with"]["name"], "release-evidence")
        for filename in (
            "release-notes.md",
            "release-components.json",
            "release-upgrades.json",
            "release-requests.json",
            "release-facts.json",
        ):
            self.assertIn(filename, upload["with"]["path"])

    def test_every_hub_version_boundary_uses_the_canonical_contract(self):
        """Workflow shell regexes must not diverge from the shared SemVer parser."""
        preflight = self.script(self.jobs["preflight"])
        publish = self.script(self.jobs["publish"])
        self.assertIn('validate-version "$VERSION"', preflight)
        self.assertIn('validate-version "$VERSION"', publish)
        self.assertNotIn("^[0-9]+\\.[0-9]+\\.[0-9]+$", self.text)


if __name__ == "__main__":
    unittest.main()
