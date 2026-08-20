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

    def test_installer_validates_repo_slug_and_uses_fixed_clone_target(self):
        text = self.skill_md.read_text(encoding="utf-8")

        self.assertIn("exact `owner/repo` syntax", text)
        self.assertIn("no whitespace, `..`, shell metacharacters, or extra path segments", text)
        self.assertIn("https://github.com/<repo>.git <tmp>/pack", text)
        self.assertIn("bash <tmp>/pack/<install_script> <PROJECT_ROOT>", text)
        self.assertNotIn("<tmp>/<repo>", text)

    def test_installer_installs_workspace_packs_from_the_hub_mirror_first(self):
        text = self.skill_md.read_text(encoding="utf-8")

        # Primary source: the Hub itself, not the pack repo.
        self.assertIn(
            "git clone --depth 1 https://github.com/D-Robotics/rdk-skills.git <tmp>/rdk-skills",
            text,
        )
        self.assertIn(
            "bash <tmp>/rdk-skills/skills/<catalog_dir>/<install_script> <PROJECT_ROOT>",
            text,
        )
        # The self-installable mirror contract (mirrored resource tree plus
        # the overlaid setup.sh) must be described.
        self.assertIn("self-installable catalog dir", text)
        self.assertIn("setup entry is `<tmp>/rdk-skills/skills/<catalog_dir>/<install_script>`", text)

    def test_installer_treats_agent_setup_as_read_only_context(self):
        text = self.skill_md.read_text(encoding="utf-8")

        self.assertIn("optional read-only context", text)
        self.assertIn("must not replace or add to the validated `install_script`", text)
        self.assertIn("separate explicit confirmation", text)
        self.assertIn("within the confirmed `PROJECT_ROOT`", text)

    def test_installer_upgrade_flow_compares_installed_anchor_with_registry_ref(self):
        text = self.skill_md.read_text(encoding="utf-8")

        # Installed-state anchor: INSTALLED_REF first, VERSION as fallback,
        # compared against the registry ref after normalizing a leading "v".
        self.assertIn("INSTALLED_REF", text)
        self.assertIn("stripping a leading `v`", text)
        self.assertIn("already up to date", text)

        # Upgrade runs the mirrored setup.sh with --update --ref; forced
        # reinstall at the same version appends --force.
        self.assertIn(
            "bash <tmp>/rdk-skills/skills/<catalog_dir>/<install_script> --update --ref <ref> <PROJECT_ROOT>",
            text,
        )
        self.assertIn("append `--force`", text)
        self.assertIn(
            "bash <tmp>/pack/<install_script> --update --ref <ref> <PROJECT_ROOT>",
            text,
        )
        self.assertIn("pre-upgrade `setup.sh`", text)

        # Upgrade rebuilds the workspace dir — local edits are lost, so it
        # needs its own confirmation gate.
        self.assertIn("local edits inside `.drobotics/` / `.horizon/` are lost", text)
        self.assertIn("Never run an upgrade without the explicit confirmation", text)

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

    def test_workspace_router_handoffs_have_install_fallbacks(self):
        expected_routes = {
            "rdk-board-delegate": {"horizon-router": "OE Tool Chain (S)"},
            "rdk-board-knowledge": {
                "x5-router": "OE Tool Chain (X5)",
                "horizon-router": "OE Tool Chain (S)",
            },
            "rdk-embodied-lerobot": {
                "x5-router": "OE Tool Chain (X5)",
                "horizon-router": "OE Tool Chain (S)",
            },
            "rdk-hardware": {
                "x5-router": "OE Tool Chain (X5)",
                "horizon-router": "OE Tool Chain (S)",
            },
            "rdk-model-zoo": {
                "x5-router": "OE Tool Chain (X5)",
                "horizon-router": "OE Tool Chain (S)",
            },
        }
        for skill_name, routes in expected_routes.items():
            text = (self.repo / "skills" / skill_name / "SKILL.md").read_text(
                encoding="utf-8"
            )
            frontmatter = text.split("---", 2)[1]
            self.assertIn("availability-gated", frontmatter, skill_name)
            self.assertIn("## Workspace router availability gate", text, skill_name)
            self.assertIn("`rdk-pack-installer`", text, skill_name)
            self.assertIn("restart", text.casefold(), skill_name)
            self.assertIn("retry", text.casefold(), skill_name)
            for router, pack in routes.items():
                atomic_fallback = (
                    f"check whether `{router}` is available in the current session. "
                    f"If unavailable, do not hand off: use `rdk-pack-installer` "
                    f"to install `{pack}`"
                )
                self.assertIn(atomic_fallback, text, skill_name)

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

    def test_finder_docs_show_exact_flat_install_command(self):
        command = "npx skills add d-robotics/rdk-skills --skill <skill-name>"
        for relative_path in ("README.md", "README_cn.md", "docs/SKILL-USAGE.md"):
            with self.subTest(relative_path=relative_path):
                text = (self.repo / relative_path).read_text(encoding="utf-8")
                self.assertIn(command, text)

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
