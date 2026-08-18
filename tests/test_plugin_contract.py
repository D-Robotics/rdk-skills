import re
import unittest
from pathlib import Path


class PluginContractTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]
        self.skill_dir = self.repo / "skills" / "rdk-pack-installer"
        self.skill_md = self.skill_dir / "SKILL.md"

    def test_installer_is_named_rdk_pack_installer(self):
        self.assertTrue(self.skill_md.is_file())
        text = self.skill_md.read_text(encoding="utf-8")

        self.assertIn("name: rdk-pack-installer", text)
        self.assertFalse((self.repo / "skills" / "d-robotics-pack-installer").exists())

    def test_installer_reads_bundled_registry_not_components_directory(self):
        self.assertTrue(self.skill_md.is_file())
        text = self.skill_md.read_text(encoding="utf-8")

        self.assertIn("references/pack-registry.json", text)
        self.assertNotIn("components.d", text)
        self.assertTrue((self.skill_dir / "references" / "pack-registry.json").is_file())

    def test_hub_device_mirror_has_no_retired_routes(self):
        retired = (
            "rdk-device",
            "rdk-doc-finder",
            "rdk-ros",
            "rdk-mipi-camera-bringup",
            "rdk-perf-investigator",
        )
        for path in (self.repo / "skills").glob("rdk-*/SKILL.md"):
            text = path.read_text(encoding="utf-8")
            for route in retired:
                pattern = rf"(?<![a-z0-9-]){re.escape(route)}(?![a-z0-9-])"
                self.assertIsNone(re.search(pattern, text, re.I), f"{path}: {route}")


if __name__ == "__main__":
    unittest.main()
