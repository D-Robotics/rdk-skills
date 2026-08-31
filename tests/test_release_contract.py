"""Release-level invariants for the unified v1.0.0 Hub assembly."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = ROOT / ".github" / "scripts" / "generate_plugin_catalog.py"
EXPECTED_REFS = {
    "bsp-skills.yml": "v1.0.0",
    "rdk-device.yml": "v1.0.0",
    "oe-tool-chain-x5.yml": "v1.0.0",
    "oe-tool-chain-s.yml": "v1.0.0",
}

spec = importlib.util.spec_from_file_location("release_catalog_generator", GENERATOR_PATH)
assert spec is not None and spec.loader is not None
catalog = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = catalog
spec.loader.exec_module(catalog)


class ReleaseContractTests(unittest.TestCase):
    def test_components_pin_every_release_source_to_v1(self):
        for filename, expected_ref in EXPECTED_REFS.items():
            with self.subTest(filename=filename):
                data = yaml.safe_load((ROOT / "components.d" / filename).read_text(encoding="utf-8"))
                self.assertEqual(data["ref"], expected_ref)

    def test_every_current_skill_uses_v1_frontmatter(self):
        paths = sorted((ROOT / "skills").rglob("SKILL.md"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertRegex(text, r"(?m)^version:\s*1\.0\.0\s*$")

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
        self.assertEqual(
            {item["ref"] for item in json.loads(
                (ROOT / "skills/rdk-pack-installer/references/pack-registry.json").read_text(encoding="utf-8")
            )["packs"]},
            {"v1.0.0"},
        )


if __name__ == "__main__":
    unittest.main()
