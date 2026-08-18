import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "rdk-skill-finder" / "scripts" / "search_catalog.py"


def load_finder():
    spec = importlib.util.spec_from_file_location("search_catalog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SearchCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.finder = load_finder()
        cls.index = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "rdk-diagnostic",
                    "description": "Diagnose common RDK device issues.",
                    "pack": "rdk-core",
                    "repo": "d-robotics/rdk-skills",
                    "catalog_path": "skills/rdk-diagnostic",
                    "install_type": "flat",
                },
                {
                    "name": "x5-router",
                    "description": "RDK X5 模型量化和 ONNX 编译工具链。",
                    "pack": "rdk-x5-toolchain",
                    "repo": "d-robotics/rdk-skills",
                    "catalog_path": "components.d/rdk-x5-toolchain",
                    "install_type": "workspace",
                },
            ],
        }

    def test_exact_skill_name_ranks_first(self):
        result = self.finder.search(self.index, "rdk-diagnostic")
        self.assertEqual(result["matches"][0]["name"], "rdk-diagnostic")

    def test_workspace_filter_returns_installer_handoff(self):
        result = self.finder.search(
            self.index, "模型量化", platform="X5", install_type="workspace"
        )
        self.assertEqual(result["matches"][0]["install_type"], "workspace")
        self.assertEqual(result["matches"][0]["action"], "use rdk-pack-installer")

    def test_no_match_uses_docs_fallback_without_inventing_skill(self):
        result = self.finder.search(self.index, "完全无关的诗歌创作")
        self.assertEqual(result["matches"], [])
        self.assertEqual(result["fallback"], "rdk-docs-reference")

    def test_invalid_index_returns_structured_cli_error(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write("{not-json")
            index_path = handle.name
        self.addCleanup(lambda: os.unlink(index_path))
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "diagnostic"],
            env={**os.environ, "PYTHONUTF8": "1", "RDK_SKILL_INDEX": index_path},
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(completed.stdout)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(payload["matches"], [])
        self.assertIsNone(payload["fallback"])

    def test_boolean_schema_version_returns_structured_cli_error(self):
        invalid_index = {**self.index, "schema_version": True}
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            json.dump(invalid_index, handle)
            index_path = handle.name
        self.addCleanup(lambda: os.unlink(index_path))
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "diagnostic"],
            env={**os.environ, "PYTHONUTF8": "1", "RDK_SKILL_INDEX": index_path},
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(completed.stdout)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(payload["matches"], [])
        self.assertIsNone(payload["fallback"])


if __name__ == "__main__":
    unittest.main()
