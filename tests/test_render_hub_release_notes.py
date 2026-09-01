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
            "formal_release": True,
        }
    ]


class HubReleaseNoteTests(unittest.TestCase):
    def setUp(self):
        self.renderer = load_renderer()

    def test_release_title_is_exact_and_component_versions_are_independent(self):
        """Collapsing component refs to the Hub version must fail this contract."""
        notes = self.renderer.render_notes("1.0.1", mixed_components(), upgrades())

        self.assertEqual(notes.title, "RDK Skills v1.0.1")
        self.assertIn("BSP Skills | `v1.0.1`", notes.body)
        self.assertIn("OE Skills X5 | `v1.0.0`", notes.body)
        self.assertIn("BSP Skills: `v1.0.0` to `v1.0.1`", notes.body)
        self.assertFalse(self.renderer.contains_cjk(notes.body))

    def test_rejects_non_english_additions_and_unresolved_template_markers(self):
        """Accepting CJK text or publishing a template placeholder is a release defect."""
        with self.assertRaisesRegex(ValueError, "English"):
            self.renderer.render_notes("1.0.1", mixed_components(), upgrades(), "新增说明")
        with self.assertRaisesRegex(ValueError, "marker"):
            self.renderer.render_notes("1.0.1", mixed_components(), upgrades(), "{{REPLACE_ME}}")

    def test_rejects_invalid_versions_duplicate_components_and_unpublished_sources(self):
        """Weak input validation could publish a Hub tag with unverifiable source content."""
        with self.assertRaisesRegex(ValueError, "version"):
            self.renderer.render_notes("v1.0.1", mixed_components(), upgrades())
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.renderer.render_notes("1.0.1", mixed_components() + [mixed_components()[0]], upgrades())
        unpublished = mixed_components()
        unpublished[0]["formal_release"] = False
        with self.assertRaisesRegex(ValueError, "formal source Release"):
            self.renderer.render_notes("1.0.1", unpublished, upgrades())

    def test_accepts_existing_oe_component_upgrade_metadata_names(self):
        """Rejecting the existing component-upgrade PR name would block an otherwise valid release."""
        oe_upgrade = upgrades()
        oe_upgrade[0].update(
            {
                "component": "OE Tool Chain (X5)",
                "from_tag": "v0.9.9",
                "to_tag": "v1.0.0",
                "release_url": "https://github.com/D-Robotics/oe-skills-x5/releases/tag/v1.0.0",
            }
        )

        notes = self.renderer.render_notes("1.0.1", mixed_components(), oe_upgrade)

        self.assertIn("OE Skills X5: `v0.9.9` to `v1.0.0`", notes.body)


if __name__ == "__main__":
    unittest.main()
