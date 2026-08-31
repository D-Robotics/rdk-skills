# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Integration tests for selective component synchronization."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "sync-components.sh"


def hash_tree(root: Path) -> str:
    """Return a stable digest of a directory's paths and file content."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(path.relative_to(root).as_posix().encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def bash_path(path: Path) -> str:
    """Convert a Windows path to the POSIX spelling used by Git Bash."""
    value = str(path.resolve())
    return f"/mnt/{value[0].lower()}{value[2:]}".replace("\\", "/")


class SelectiveSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.hub_root = self.root / "hub"
        self.hub_root.mkdir()
        self.components_dir = self.hub_root / "components.d"
        self.components_dir.mkdir()
        self.repo_base = self.root / "repos"
        self.source_root = self.repo_base / "acme" / "bsp-skills"
        self.source_root.mkdir(parents=True)
        self._write_source()
        self._git("init", "-q", "-b", "main", cwd=self.source_root)
        self._git("config", "user.email", "tests@example.invalid", cwd=self.source_root)
        self._git("config", "user.name", "Test Runner", cwd=self.source_root)
        self._git("add", ".", cwd=self.source_root)
        self._git("commit", "-qm", "fixture", cwd=self.source_root)
        self._git("clone", "--bare", "-q", str(self.source_root), str(self.source_root) + ".git")

        (self.components_dir / "bsp-skills.yml").write_text(
            "repo: acme/bsp-skills\nref: main\nskills:\n"
            "  - path: source/bsp-env-setup\n    catalog_dir: bsp-env-setup\n",
            encoding="utf-8",
        )
        stale = self.hub_root / "skills" / "bsp-env-setup" / "stale.txt"
        stale.parent.mkdir(parents=True)
        stale.write_text("remove me\n", encoding="utf-8")
        diagnostic = self.hub_root / "skills" / "rdk-diagnostic" / "keep.txt"
        diagnostic.parent.mkdir(parents=True)
        diagnostic.write_text("unchanged\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_source(self):
        skill = self.source_root / "source" / "bsp-env-setup" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: bsp-env-setup\n---\n", encoding="utf-8")

    def _git(self, *args, cwd=None):
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
        )

    def run_sync(self, component: str):
        summary_file = self.root / "sync-summary.json"
        return subprocess.run(
            [
                "bash", bash_path(SCRIPT),
                "--components-dir", bash_path(self.components_dir),
                "--component", component,
                "--repo-base-url", bash_path(self.repo_base),
                "--work-root", bash_path(self.root / "work"),
                "--summary-file", bash_path(summary_file),
            ],
            cwd=self.hub_root,
            env={**os.environ, "PYTHONPATH": str(ROOT / ".github")},
            capture_output=True,
            text=True,
        )

    def test_requested_component_sync_prunes_only_its_catalog_tree(self):
        diagnostic_before = hash_tree(self.hub_root / "skills" / "rdk-diagnostic")

        result = self.run_sync(component="bsp-skills")

        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads((self.root / "sync-summary.json").read_text())
        component_summary = summary["components"][0]
        self.assertEqual(component_summary["component_id"], "bsp-skills")
        self.assertEqual(component_summary["source_ref"], "main")
        self.assertRegex(component_summary["source_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(component_summary["catalog_dirs"], ["bsp-env-setup"])
        self.assertTrue(component_summary["changed"])
        self.assertIsNone(component_summary["failure"])
        self.assertFalse((self.hub_root / "skills" / "bsp-env-setup" / "stale.txt").exists())
        self.assertEqual(
            hash_tree(self.hub_root / "skills" / "rdk-diagnostic"), diagnostic_before
        )


if __name__ == "__main__":
    unittest.main()
