import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / ".github" / "scripts" / "generate_plugin_catalog.py"

spec = importlib.util.spec_from_file_location("generate_plugin_catalog", MODULE_PATH)
assert spec is not None and spec.loader is not None
catalog = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = catalog
spec.loader.exec_module(catalog)


class PackRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        components_dir = self.repo / "components.d"
        components_dir.mkdir()
        (components_dir / "oe-tool-chain-x5.yml").write_text(
            """\
name: OE Tool Chain (X5)
repo: D-Robotics/oe-skills-x5
ref: v1.0.0
install_type: workspace
install_script: setup.sh
workspace_dir: .drobotics
verify_paths:
  - .drobotics/X5.md
  - .drobotics/VERSION
  - .drobotics/skill-index.json
  - .drobotics/skills/x5-router/SKILL.md
skills:
  - catalog_dir: oe-skills-x5
""",
            encoding="utf-8",
        )
        (components_dir / "oe-tool-chain-s.yml").write_text(
            """\
name: OE Tool Chain (S)
repo: D-Robotics/oe-skills-s
ref: v1.0.0
install_type: workspace
install_script: setup.sh
workspace_dir: .horizon
verify_paths:
  - .horizon/HORIZON.md
  - .horizon/VERSION
  - .horizon/skill-index.json
  - .horizon/skills/horizon-router/SKILL.md
skills:
  - catalog_dir: oe-skills-s
""",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pack_registry_contains_declared_workspace_contracts(self):
        registry = catalog.build_pack_registry(self.repo, catalog.load_components(self.repo))
        packs = {item["repo"]: item for item in registry["packs"]}
        self.assertEqual(packs["D-Robotics/oe-skills-x5"]["workspace_dir"], ".drobotics")
        self.assertIn(
            ".drobotics/skills/x5-router/SKILL.md",
            packs["D-Robotics/oe-skills-x5"]["verify_paths"],
        )
        self.assertEqual(packs["D-Robotics/oe-skills-s"]["workspace_dir"], ".horizon")
        self.assertIn(
            ".horizon/skills/horizon-router/SKILL.md",
            packs["D-Robotics/oe-skills-s"]["verify_paths"],
        )

    def test_pack_registry_declares_hub_catalog_dir(self):
        registry = catalog.build_pack_registry(self.repo, catalog.load_components(self.repo))
        packs = {item["repo"]: item for item in registry["packs"]}
        self.assertEqual(packs["D-Robotics/oe-skills-x5"]["catalog_dir"], "oe-skills-x5")
        self.assertEqual(packs["D-Robotics/oe-skills-s"]["catalog_dir"], "oe-skills-s")

    def test_pack_registry_preserves_pinned_refs(self):
        registry = catalog.build_pack_registry(self.repo, catalog.load_components(self.repo))

        self.assertEqual(
            {pack["repo"]: pack["ref"] for pack in registry["packs"]},
            {
                "D-Robotics/oe-skills-s": "v1.0.0",
                "D-Robotics/oe-skills-x5": "v1.0.0",
            },
        )

    def test_pack_registry_defaults_missing_ref_to_main(self):
        component = {
            "name": "Unpinned Workspace",
            "repo": "D-Robotics/unpinned-workspace",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "workspace_dir": ".workspace",
            "verify_paths": [".workspace/VERSION"],
            "skills": [{"catalog_dir": "unpinned"}],
        }
        registry = catalog.build_pack_registry(Path("."), [component])

        self.assertEqual(registry["packs"][0]["ref"], "main")


class SkillIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        components_dir = self.repo / "components.d"
        components_dir.mkdir()
        (components_dir / "device.yml").write_text(
            """\
name: RDK Device Skills
repo: D-Robotics/rdk-device-skills
skills:
  - catalog_dir: rdk-diagnostic
""",
            encoding="utf-8",
        )
        (components_dir / "x5.yml").write_text(
            """\
name: OE Tool Chain (X5)
repo: D-Robotics/oe-skills-x5
install_type: workspace
skills:
  - catalog_dir: oe-skills-x5
""",
            encoding="utf-8",
        )
        (self.repo / "catalog-exceptions.yml").write_text(
            """\
exceptions:
  - dir: rdk-pack-installer
    component: D-Robotics Skills
""",
            encoding="utf-8",
        )
        self._write_skill("skills/rdk-diagnostic/SKILL.md", "rdk-diagnostic")
        self._write_skill("skills/oe-skills-x5/x5-router/SKILL.md", "x5-router")
        self._write_skill("skills/rdk-pack-installer/SKILL.md", "rdk-pack-installer")
        self.components = catalog.load_components(self.repo)
        self.exceptions = [{"dir": "rdk-pack-installer", "component": "D-Robotics Skills"}]

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_skill(self, relative_path, name):
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name}\ndescription: Test skill {name}.\n---\n",
            encoding="utf-8",
        )

    def test_skill_index_contains_flat_workspace_and_hub_records(self):
        index = catalog.build_skill_index(self.repo, self.components, self.exceptions)
        records = {item["name"]: item for item in index["skills"]}
        self.assertEqual(records["rdk-diagnostic"]["install_type"], "flat")
        self.assertEqual(records["x5-router"]["install_type"], "workspace")
        self.assertEqual(records["rdk-pack-installer"]["repo"], "D-Robotics/rdk-skills")

    def test_generated_json_is_byte_for_byte_deterministic(self):
        index = catalog.build_skill_index(self.repo, self.components, self.exceptions)
        first = catalog.render_json(index)
        second = catalog.render_json(index)
        self.assertEqual(first, second)
        self.assertTrue(first.endswith("\n"))

    def test_rejects_invalid_frontmatter(self):
        (self.repo / "skills/rdk-diagnostic/SKILL.md").write_text(
            "name: rdk-diagnostic\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "invalid frontmatter: skills/rdk-diagnostic/SKILL.md",
        ):
            catalog.build_skill_index(self.repo, self.components, self.exceptions)

    def test_rejects_duplicate_skill_names(self):
        (self.repo / "components.d/other.yml").write_text(
            """\
name: Other Skills
repo: D-Robotics/other-skills
skills:
  - catalog_dir: other-skill
""",
            encoding="utf-8",
        )
        self._write_skill("skills/other-skill/SKILL.md", "rdk-diagnostic")

        with self.assertRaisesRegex(catalog.CatalogError, "duplicate skill name: rdk-diagnostic"):
            catalog.build_skill_index(self.repo, catalog.load_components(self.repo), self.exceptions)

    def test_rejects_duplicate_catalog_paths(self):
        (self.repo / "components.d/duplicate.yml").write_text(
            """\
name: Duplicate Catalog Directory
repo: D-Robotics/duplicate-skills
skills:
  - catalog_dir: rdk-diagnostic
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "duplicate catalog path: skills/rdk-diagnostic",
        ):
            catalog.build_skill_index(self.repo, catalog.load_components(self.repo), self.exceptions)


class CatalogValidationTests(unittest.TestCase):
    def test_rejects_unsafe_repository_slugs(self):
        unsafe_repositories = (
            "",
            "owner",
            "/repo",
            "owner/",
            "owner/repo/extra",
            "owner name/repo",
            "owner/repo name",
            "owner/../repo",
            "owner/re..po",
            "owner/repo;echo-owned",
            "owner/repo$(echo-owned)",
            "owner\\repo",
        )
        for repository in unsafe_repositories:
            with self.subTest(repository=repository):
                component = {
                    "name": "Unsafe Repository",
                    "repo": repository,
                    "install_type": "workspace",
                    "install_script": "setup.sh",
                    "workspace_dir": ".workspace",
                    "verify_paths": [".workspace/VERSION"],
                }

                with self.assertRaisesRegex(
                    catalog.CatalogError,
                    "repo must use exact owner/repo syntax",
                ):
                    catalog.build_pack_registry(Path("."), [component])

    def test_rejects_workspace_component_without_workspace_dir(self):
        component = {
            "name": "Missing Workspace Directory",
            "repo": "D-Robotics/missing-workspace-dir",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "verify_paths": [".workspace/VERSION"],
        }

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "workspace_dir is required for workspace components",
        ):
            catalog.build_pack_registry(Path("."), [component])

    def test_rejects_workspace_component_with_empty_verify_paths(self):
        component = {
            "name": "Empty Verification Paths",
            "repo": "D-Robotics/empty-verify-paths",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "workspace_dir": ".workspace",
            "verify_paths": [],
        }

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "verify_paths must be a non-empty list for workspace components",
        ):
            catalog.build_pack_registry(Path("."), [component])

    def test_rejects_workspace_component_without_skills_entry(self):
        component = {
            "name": "Missing Skills Entry",
            "repo": "D-Robotics/missing-skills-entry",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "workspace_dir": ".workspace",
            "verify_paths": [".workspace/VERSION"],
        }

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "workspace component must declare exactly one skills entry",
        ):
            catalog.build_pack_registry(Path("."), [component])

    def test_rejects_workspace_component_with_multiple_skills_entries(self):
        component = {
            "name": "Split Workspace",
            "repo": "D-Robotics/split-workspace",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "workspace_dir": ".workspace",
            "verify_paths": [".workspace/VERSION"],
            "skills": [
                {"catalog_dir": "split-a"},
                {"catalog_dir": "split-b"},
            ],
        }

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "workspace component must declare exactly one skills entry",
        ):
            catalog.build_pack_registry(Path("."), [component])

    def test_rejects_workspace_component_without_catalog_dir(self):
        component = {
            "name": "Missing Catalog Dir",
            "repo": "D-Robotics/missing-catalog-dir",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "workspace_dir": ".workspace",
            "verify_paths": [".workspace/VERSION"],
            "skills": [{"path": "pkg/"}],
        }

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "catalog_dir is required for workspace component",
        ):
            catalog.build_pack_registry(Path("."), [component])

    def test_rejects_unsafe_catalog_dir(self):
        for catalog_dir in ("/absolute", "../parent", "a\\b"):
            with self.subTest(catalog_dir=catalog_dir):
                component = {
                    "name": "Unsafe Catalog Dir",
                    "repo": "D-Robotics/unsafe-catalog-dir",
                    "install_type": "workspace",
                    "install_script": "setup.sh",
                    "workspace_dir": ".workspace",
                    "verify_paths": [".workspace/VERSION"],
                    "skills": [{"catalog_dir": catalog_dir}],
                }

                with self.assertRaisesRegex(
                    catalog.CatalogError,
                    "catalog_dir must be a safe POSIX relative path",
                ):
                    catalog.build_pack_registry(Path("."), [component])

    def test_rejects_absolute_and_parent_workspace_paths(self):
        for workspace_dir in ("/absolute", "../parent"):
            with self.subTest(workspace_dir=workspace_dir):
                component = {
                    "name": "Unsafe Workspace Directory",
                    "repo": "D-Robotics/unsafe-workspace-dir",
                    "install_type": "workspace",
                    "install_script": "setup.sh",
                    "workspace_dir": workspace_dir,
                    "verify_paths": [".workspace/VERSION"],
                }

                with self.assertRaisesRegex(
                    catalog.CatalogError,
                    "workspace_dir must be a safe POSIX relative path",
                ):
                    catalog.build_pack_registry(Path("."), [component])

    def test_rejects_windows_drive_qualified_workspace_path(self):
        component = {
            "name": "Windows Drive Workspace Directory",
            "repo": "D-Robotics/windows-drive-workspace-dir",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "workspace_dir": "C:/outside",
            "verify_paths": [".workspace/VERSION"],
        }

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "workspace_dir must be a safe POSIX relative path",
        ):
            catalog.build_pack_registry(Path("."), [component])

    def test_rejects_parent_verify_path(self):
        component = {
            "name": "Unsafe Verification Path",
            "repo": "D-Robotics/unsafe-verify-path",
            "install_type": "workspace",
            "install_script": "setup.sh",
            "workspace_dir": ".workspace",
            "verify_paths": ["../parent"],
        }

        with self.assertRaisesRegex(
            catalog.CatalogError,
            "verify_paths must be a safe POSIX relative path",
        ):
            catalog.build_pack_registry(Path("."), [component])

    def test_rejects_missing_plugin_include_skill_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            plugins_dir = repo / "plugins.d"
            plugins_dir.mkdir()
            (plugins_dir / "example.yml").write_text(
                "include_skills:\n  - skills/not-present/\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                catalog.CatalogError,
                "missing include_skills path: skills/not-present/",
            ):
                catalog.validate_plugin_includes(repo)

    def test_rejects_invalid_plugin_yaml(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            plugins_dir = repo / "plugins.d"
            plugins_dir.mkdir()
            (plugins_dir / "invalid.yml").write_text(
                "description: value: not-valid-yaml\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                catalog.CatalogError,
                "invalid plugin file: .*plugins.d.*invalid.yml",
            ):
                catalog.validate_plugin_includes(repo)


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        components_dir = self.repo / "components.d"
        components_dir.mkdir()
        (components_dir / "x5.yml").write_text(
            """\
name: OE Tool Chain (X5)
repo: D-Robotics/oe-skills-x5
install_type: workspace
install_script: setup.sh
workspace_dir: .drobotics
verify_paths:
  - .drobotics/VERSION
skills:
  - catalog_dir: oe-skills-x5
""",
            encoding="utf-8",
        )
        (self.repo / "catalog-exceptions.yml").write_text(
            """\
exceptions:
  - dir: rdk-pack-installer
    component: D-Robotics Skills
""",
            encoding="utf-8",
        )
        self._write_skill("skills/oe-skills-x5/x5-router/SKILL.md", "x5-router")
        self._write_skill("skills/rdk-pack-installer/SKILL.md", "rdk-pack-installer")
        (self.repo / "skills/rdk-pack-installer/references").mkdir(parents=True)
        (self.repo / "skills/rdk-skill-finder/references").mkdir(parents=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_skill(self, relative_path, name):
        path = self.repo / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nname: {name}\ndescription: Test skill {name}.\n---\n",
            encoding="utf-8",
        )

    def test_generate_writes_both_catalog_files(self):
        written = catalog.generate(self.repo)

        self.assertEqual(
            {path.relative_to(self.repo).as_posix() for path in written},
            {
                "skills/rdk-pack-installer/references/pack-registry.json",
                "skills/rdk-skill-finder/references/skill-index.json",
            },
        )
        pack_registry = json.loads(written[0].read_text(encoding="utf-8"))
        skill_index = json.loads(written[1].read_text(encoding="utf-8"))
        self.assertEqual(pack_registry["packs"][0]["repo"], "D-Robotics/oe-skills-x5")
        self.assertEqual(skill_index["skills"][0]["name"], "rdk-pack-installer")

    def test_generate_writes_utf8_json_with_lf_terminator(self):
        written = catalog.generate(self.repo, target="pack")
        content = written[0].read_bytes()

        self.assertTrue(content.endswith(b"\n"))
        self.assertNotIn(b"\r\n", content)

    def test_cli_target_writes_pack_registry(self):
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "--repo-root", str(self.repo), "--target", "pack"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(
            (self.repo / "skills/rdk-pack-installer/references/pack-registry.json").is_file()
        )
        self.assertFalse(
            (self.repo / "skills/rdk-skill-finder/references/skill-index.json").exists()
        )

    def test_cli_check_plugin_includes_reports_missing_directory(self):
        plugins_dir = self.repo / "plugins.d"
        plugins_dir.mkdir()
        (plugins_dir / "example.yml").write_text(
            "include_skills:\n  - skills/not-present/\n",
            encoding="utf-8",
        )

        result = subprocess.run(
            [
                sys.executable,
                str(MODULE_PATH),
                "--repo-root",
                str(self.repo),
                "--check-plugin-includes",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing include_skills path: skills/not-present/", result.stderr)


if __name__ == "__main__":
    unittest.main()
