"""Contracts for rendering a protected, mixed-component Hub Release."""

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER_PATH = ROOT / ".github" / "scripts" / "render_hub_release_notes.py"


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


if __name__ == "__main__":
    unittest.main()
