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

    def test_exact_name_preserves_token_order_against_competing_name(self):
        competing_index = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "a-b",
                    "description": "First competing workflow.",
                    "pack": "rdk-core",
                    "repo": "d-robotics/rdk-skills",
                    "catalog_path": "skills/a-b",
                    "install_type": "flat",
                },
                {
                    "name": "b-a",
                    "description": "Second competing workflow.",
                    "pack": "rdk-core",
                    "repo": "d-robotics/rdk-skills",
                    "catalog_path": "skills/b-a",
                    "install_type": "flat",
                },
            ],
        }
        result = self.finder.search(competing_index, "b-a")
        self.assertEqual([match["name"] for match in result["matches"]], ["b-a", "a-b"])
        self.assertEqual(result["matches"][0]["score"], 120)
        self.assertEqual(result["matches"][1]["score"], 20)

    def test_workspace_filter_returns_installer_handoff(self):
        result = self.finder.search(
            self.index, "模型量化", platform="X5", install_type="workspace"
        )
        self.assertEqual(result["matches"][0]["install_type"], "workspace")
        self.assertEqual(result["matches"][0]["action"], "use rdk-pack-installer")

    def test_pack_filter_is_case_insensitive_and_exact(self):
        result = self.finder.search(self.index, "rdk", pack="RDK-CORE")
        self.assertEqual([match["name"] for match in result["matches"]], ["rdk-diagnostic"])
        no_exact_pack = self.finder.search(self.index, "rdk", pack="rdk")
        self.assertEqual(no_exact_pack["matches"], [])
        self.assertEqual(no_exact_pack["fallback"], "rdk-docs-reference")

    def test_cli_limit_returns_at_most_requested_matches(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "X5",
                "--install-type",
                "workspace",
                "--limit",
                "1",
            ],
            capture_output=True,
            check=False,
        )
        payload = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(len(payload["matches"]), 1)

    def test_cli_rejects_zero_limit_instead_of_false_fallback(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "X5", "--limit", "0"],
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, b"")
        self.assertIn(b"--limit must be at least 1", completed.stderr)

    def test_flat_match_has_required_fields_and_fixed_install_action(self):
        match = self.finder.search(self.index, "rdk-diagnostic")["matches"][0]
        self.assertEqual(
            set(match),
            {
                "name",
                "description",
                "pack",
                "repo",
                "catalog_path",
                "install_type",
                "score",
                "action",
            },
        )
        self.assertEqual(
            match["action"],
            "npx skills add d-robotics/rdk-skills --skill rdk-diagnostic",
        )

    def test_scores_use_name_and_description_weights_with_stable_tie_break(self):
        weighted_index = {
            "schema_version": 1,
            "skills": [
                {
                    "name": "b-common",
                    "description": "Second name match.",
                    "pack": "rdk-core",
                    "repo": "d-robotics/rdk-skills",
                    "catalog_path": "skills/b-common",
                    "install_type": "flat",
                },
                {
                    "name": "a-common",
                    "description": "First name match.",
                    "pack": "rdk-core",
                    "repo": "d-robotics/rdk-skills",
                    "catalog_path": "skills/a-common",
                    "install_type": "flat",
                },
                {
                    "name": "description-only",
                    "description": "common workflow",
                    "pack": "rdk-core",
                    "repo": "d-robotics/rdk-skills",
                    "catalog_path": "skills/description-only",
                    "install_type": "flat",
                },
            ],
        }
        result = self.finder.search(weighted_index, "common")
        self.assertEqual(
            [(match["name"], match["score"]) for match in result["matches"]],
            [("a-common", 10), ("b-common", 10), ("description-only", 3)],
        )

    def test_cli_writes_utf8_json_under_cp936_output_encoding(self):
        environment = {
            key: value
            for key, value in os.environ.items()
            if key not in {"PYTHONIOENCODING", "PYTHONUTF8"}
        }
        environment["PYTHONIOENCODING"] = "cp936"
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "模型量化", "--install-type", "workspace"],
            env=environment,
            capture_output=True,
            check=False,
        )
        try:
            stdout = completed.stdout.decode("utf-8")
        except UnicodeDecodeError as error:
            self.fail(f"CLI stdout was not UTF-8: {error}")
        payload = json.loads(stdout)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("cp936"))
        self.assertEqual(payload["matches"][0]["install_type"], "workspace")
        self.assertEqual(payload["matches"][0]["action"], "use rdk-pack-installer")

    def test_cli_emits_canonical_utf8_json_bytes_for_success_and_error(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write("{not-json")
            index_path = handle.name
        self.addCleanup(lambda: os.unlink(index_path))
        commands = [
            ([sys.executable, str(SCRIPT), "rdk-diagnostic", "--limit", "1"], os.environ),
            (
                [sys.executable, str(SCRIPT), "diagnostic"],
                {**os.environ, "RDK_SKILL_INDEX": index_path},
            ),
        ]
        for command, environment in commands:
            completed = subprocess.run(
                command,
                env=environment,
                capture_output=True,
                check=False,
            )
            stdout = completed.stdout.decode("utf-8")
            payload = json.loads(stdout)
            self.assertEqual(
                completed.stdout,
                (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
                    "utf-8"
                ),
            )
            self.assertTrue(completed.stdout.endswith(b"\n"))
            self.assertNotIn(b"\r\n", completed.stdout)

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

    def test_missing_index_returns_structured_cli_error(self):
        with tempfile.TemporaryDirectory() as directory:
            missing_index = Path(directory) / "missing-index.json"
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "diagnostic"],
                env={**os.environ, "RDK_SKILL_INDEX": str(missing_index)},
                capture_output=True,
                check=False,
            )
        payload = json.loads(completed.stdout.decode("utf-8"))
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(payload["matches"], [])
        self.assertIsNone(payload["fallback"])

    def test_unsupported_schema_version_returns_structured_cli_error(self):
        invalid_index = {**self.index, "schema_version": 2}
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            json.dump(invalid_index, handle)
            index_path = handle.name
        self.addCleanup(lambda: os.unlink(index_path))
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "diagnostic"],
            env={**os.environ, "RDK_SKILL_INDEX": index_path},
            capture_output=True,
            check=False,
        )
        payload = json.loads(completed.stdout.decode("utf-8"))
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(payload["matches"], [])
        self.assertIsNone(payload["fallback"])


if __name__ == "__main__":
    unittest.main()
