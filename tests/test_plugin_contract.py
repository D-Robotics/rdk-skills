import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


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

    def test_plugin_definition_includes_three_hub_skills(self):
        config = yaml.safe_load(
            (self.repo / "plugins.d/d-robotics-skills.yml").read_text(encoding="utf-8")
        )

        self.assertEqual(
            config["include_skills"],
            [
                "skills/rdk-skill-finder/",
                "skills/rdk-pack-installer/",
                "skills/rdk-docs-reference/",
            ],
        )

    def test_generated_plugin_contains_three_hub_skills(self):
        plugin_skills = self.repo / "plugins/d-robotics-skills/skills"
        names = {path.name for path in plugin_skills.iterdir()}

        self.assertEqual(
            names,
            {"rdk-skill-finder", "rdk-pack-installer", "rdk-docs-reference"},
        )
        self.assertTrue(
            (plugin_skills / "rdk-pack-installer/references/pack-registry.json").is_file()
        )
        self.assertTrue(
            (plugin_skills / "rdk-skill-finder/references/skill-index.json").is_file()
        )

    def test_dry_run_does_not_regenerate_catalog_files(self):
        missing = [tool for tool in ("bash", "yq", "rsync") if shutil.which(tool) is None]
        if missing:
            self.skipTest(f"build dependencies unavailable: {', '.join(missing)}")

        catalog_paths = (
            self.repo / "skills/rdk-pack-installer/references/pack-registry.json",
            self.repo / "skills/rdk-skill-finder/references/skill-index.json",
        )
        before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns) for path in catalog_paths
        }

        # Normalize a temporary copy because Windows checkouts materialize the
        # tracked shell script with CRLF while CI executes its LF blob directly.
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = Path(temporary_directory) / "build-plugins.sh"
            script.write_text(
                (self.repo / ".github/scripts/build-plugins.sh").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
                newline="\n",
            )
            result = subprocess.run(
                ["bash", str(script), "--dry-run"],
                cwd=self.repo,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        for path, snapshot in before.items():
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), snapshot)


if __name__ == "__main__":
    unittest.main()
