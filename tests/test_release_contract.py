"""Release-level invariants for upgrade-safe Hub assembly."""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / ".github" / "scripts" / "generate_plugin_catalog.py"
CANONICAL_STABLE_TAG = re.compile(
    r"^v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)
CANONICAL_SEMVER = re.compile(
    r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)

spec = importlib.util.spec_from_file_location("release_catalog_generator", GENERATOR_PATH)
assert spec is not None and spec.loader is not None
catalog = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = catalog
spec.loader.exec_module(catalog)


class ReleaseContractTests(unittest.TestCase):
    def assert_skill_version_is_canonical(self, path: Path) -> None:
        version = catalog._read_frontmatter(path).get("version")
        self.assertIsInstance(version, str)
        self.assertIsNotNone(CANONICAL_SEMVER.fullmatch(version))

    def test_dco_workflow_uses_resolvable_action_ref(self):
        workflow = (ROOT / ".github" / "workflows" / "dco.yml").read_text(encoding="utf-8")

        self.assertIn("christophebedard/dco-check@0.5.1", workflow)
        self.assertNotIn("christophebedard/dco-check@v0.5.2", workflow)

    def test_dco_action_receives_the_builtin_github_token(self):
        workflow = (ROOT / ".github" / "workflows" / "dco.yml").read_text(encoding="utf-8")

        self.assertIn("GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}", workflow)

    def test_plugin_builder_is_executable_for_the_sync_workflow(self):
        """The workflow invokes this script directly, so its Git mode must be executable."""
        output = subprocess.check_output(
            ["git", "ls-files", "-s", ".github/scripts/build-plugins.sh"],
            cwd=ROOT,
            text=True,
        )
        self.assertEqual(output.split(maxsplit=1)[0], "100755")

    def test_every_component_ref_is_a_canonical_stable_tag(self):
        components = catalog.load_components(ROOT)

        self.assertTrue(components)
        for component in components:
            with self.subTest(component=component.get("name")):
                self.assertIsInstance(component.get("ref"), str)
                self.assertRegex(component["ref"], CANONICAL_STABLE_TAG)

    def test_catalog_loader_rejects_noncanonical_or_nonstable_component_refs(self):
        invalid_refs = (
            "v01.2.3",
            "v1.02.3",
            "v1.2.03",
            "v1.2.3-rc.1",
            "v1.2",
            "1.2.3",
            "main",
        )
        for invalid_ref in invalid_refs:
            with self.subTest(ref=invalid_ref), tempfile.TemporaryDirectory() as temp_dir:
                repo_root = Path(temp_dir)
                components_dir = repo_root / "components.d"
                components_dir.mkdir()
                (components_dir / "component.yml").write_text(
                    yaml.safe_dump(
                        {
                            "name": "Test Component",
                            "repo": "D-Robotics/test-component",
                            "ref": invalid_ref,
                            "skills": [],
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

                with self.assertRaisesRegex(
                    catalog.CatalogError, "canonical stable tag"
                ):
                    catalog.load_components(repo_root)

    def test_catalog_loader_accepts_mixed_canonical_stable_component_refs(self):
        expected_refs = {
            "component-a.yml": "v0.0.0",
            "component-b.yml": "v1.2.3",
            "component-c.yml": "v10.20.30",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            components_dir = repo_root / "components.d"
            components_dir.mkdir()
            for index, (filename, ref) in enumerate(expected_refs.items()):
                (components_dir / filename).write_text(
                    yaml.safe_dump(
                        {
                            "name": f"Test Component {index}",
                            "repo": f"D-Robotics/test-component-{index}",
                            "ref": ref,
                            "skills": [],
                        },
                        sort_keys=False,
                    ),
                    encoding="utf-8",
                )

            components = catalog.load_components(repo_root)

        self.assertEqual(
            {component["ref"] for component in components}, set(expected_refs.values())
        )

    def test_every_current_skill_uses_canonical_semver_frontmatter(self):
        paths = sorted((ROOT / "skills").rglob("SKILL.md"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path):
                self.assert_skill_version_is_canonical(path)

    def test_rejects_malformed_skill_frontmatter_versions(self):
        malformed_versions = {
            "terminal-newline-block-scalar": "version: |\n  1.2.3\n\n",
            "leading-zero": "version: 01.2.3\n",
            "v-prefix": "version: v1.2.3\n",
            "prerelease": "version: 1.2.3-rc.1\n",
            "wrong-type": "version: 123\n",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            for name, version_yaml in malformed_versions.items():
                skill_path = temp_root / name / "SKILL.md"
                skill_path.parent.mkdir()
                skill_path.write_text(
                    "---\n"
                    f"name: {name}\n"
                    "description: Invalid version fixture.\n"
                    f"{version_yaml}"
                    "---\n",
                    encoding="utf-8",
                )
                if name == "terminal-newline-block-scalar":
                    self.assertEqual(
                        catalog._read_frontmatter(skill_path)["version"], "1.2.3\n"
                    )

                with self.subTest(name=name), self.assertRaises(AssertionError):
                    self.assert_skill_version_is_canonical(skill_path)

    def test_generated_catalogs_match_component_inputs_and_plugin_copies(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_root = Path(temporary_directory)
            pack = catalog.render_json(
                catalog.build_pack_registry(ROOT, catalog.load_components(ROOT))
            ).encode("utf-8")
            skills = catalog.render_json(
                catalog.build_skill_index(
                    ROOT, catalog.load_components(ROOT), catalog._load_exceptions(ROOT)
                )
            ).encode("utf-8")
            (temp_root / "pack-registry.json").write_bytes(pack)
            (temp_root / "skill-index.json").write_bytes(skills)
            self.assertEqual(
                pack,
                (ROOT / "skills/rdk-pack-installer/references/pack-registry.json").read_bytes(),
            )
            self.assertEqual(
                skills,
                (ROOT / "skills/rdk-skill-finder/references/skill-index.json").read_bytes(),
            )
        plugin_root = ROOT / "plugins/d-robotics-skills/skills"
        self.assertEqual(
            (ROOT / "skills/rdk-pack-installer/references/pack-registry.json").read_bytes(),
            (plugin_root / "rdk-pack-installer/references/pack-registry.json").read_bytes(),
        )
        self.assertEqual(
            (ROOT / "skills/rdk-skill-finder/references/skill-index.json").read_bytes(),
            (plugin_root / "rdk-skill-finder/references/skill-index.json").read_bytes(),
        )
        components = catalog.load_components(ROOT)
        expected_workspace_refs = [
            (component["repo"], component["ref"])
            for component in components
            if component.get("install_type") == "workspace"
        ]
        committed_pack_registry = json.loads(
            (ROOT / "skills/rdk-pack-installer/references/pack-registry.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [
                (pack["repo"], pack["ref"])
                for pack in committed_pack_registry["packs"]
            ],
            expected_workspace_refs,
        )


if __name__ == "__main__":
    unittest.main()
