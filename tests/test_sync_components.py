# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Integration tests for selective component synchronization."""

import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "sync-components.sh"
BASH = os.environ.get("SYNC_TEST_BASH") or (
    r"C:\Program Files\Git\bin\bash.exe"
    if os.name == "nt" and Path(r"C:\Program Files\Git\bin\bash.exe").exists()
    else ("/bin/bash" if Path("/bin/bash").exists() else shutil.which("bash") or "bash")
)
BASH_UNAME = subprocess.check_output([BASH, "-lc", "uname -s"], text=True).strip()
IS_GIT_FOR_WINDOWS = BASH_UNAME.startswith(("MINGW", "MSYS"))
requires_local_bare_sparse = unittest.skipIf(
    IS_GIT_FOR_WINDOWS,
    "Git for Windows local file:// sparse integration hang; exercised in Ubuntu CI/WSL",
)


def hash_tree(root: Path) -> str:
    """Return a stable digest of a directory's paths and file content."""
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        digest.update(path.relative_to(root).as_posix().encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def bash_path(path: Path) -> str:
    """Translate paths for the actual shell executing the integration test."""
    if not (len(str(path.resolve())) >= 2 and str(path.resolve())[1] == ":"):
        return str(path.resolve())
    value = str(path.resolve())
    mount = "/" if BASH_UNAME.startswith(("MINGW", "MSYS")) else "/mnt/"
    return f"{mount}{value[0].lower()}{value[2:]}".replace("\\", "/")


def file_url(path: Path) -> str:
    return "file://" + bash_path(path)


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

    def bash_command(self, args):
        return [BASH, "-c", 'cd -- "$1" && shift && exec bash "$@"', "bash", bash_path(self.hub_root), *args]

    def run_sync(self, component: str, work_root=None, fail_after=None, fail_compare=None):
        summary_file = self.root / "sync-summary.json"
        work_root = work_root or self.hub_root / ".tmp" / "component-sync-test"
        return subprocess.run(
            self.bash_command([
                bash_path(SCRIPT),
                "--components-dir", bash_path(self.components_dir),
                "--component", component,
                "--repo-base-url", file_url(self.repo_base),
                "--work-root", bash_path(work_root),
                "--summary-file", bash_path(summary_file),
            ] + (["--fail-after-replace", str(fail_after)] if fail_after else [])
              + (["--fail-compare", fail_compare] if fail_compare else [])),
            env={**os.environ, "PYTHONPATH": str(ROOT / ".github"), "PYTHON_BIN": "python" if BASH_UNAME.startswith(("MINGW", "MSYS")) else "python3"},
            capture_output=True,
            text=True,
        )

    @requires_local_bare_sparse
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

    def test_rejects_existing_unrelated_catalog_as_work_root(self):
        diagnostic = self.hub_root / "skills" / "rdk-diagnostic"
        before = hash_tree(diagnostic)

        result = self.run_sync("bsp-skills", work_root=diagnostic)

        self.assertNotEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.assertIn("unsafe work root", result.stderr)
        self.assertEqual(hash_tree(diagnostic), before)

    def test_rejects_unknown_component(self):
        unknown = self.run_sync("unknown")
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn("unknown component", unknown.stderr)

    @requires_local_bare_sparse
    def test_rejects_empty_source(self):
        (self.components_dir / "bsp-skills.yml").write_text(
            "repo: acme/bsp-skills\nref: main\nskills:\n"
            "  - path: source/missing\n    catalog_dir: bsp-env-setup\n",
            encoding="utf-8",
        )
        empty = self.run_sync("bsp-skills")
        self.assertNotEqual(empty.returncode, 0)
        self.assertIn("source path is empty or missing", empty.stderr)

    @requires_local_bare_sparse
    def test_rejects_clone_failure(self):
        (self.components_dir / "bsp-skills.yml").write_text(
            "repo: acme/missing\nref: main\nskills:\n"
            "  - path: source/bsp-env-setup\n    catalog_dir: bsp-env-setup\n",
            encoding="utf-8",
        )
        clone = self.run_sync("bsp-skills")
        self.assertNotEqual(clone.returncode, 0)
        self.assertIn("could not clone", clone.stderr)

    def test_rejects_summary_directory_before_catalog_changes(self):
        target = self.hub_root / "skills" / "bsp-env-setup"
        before = hash_tree(target)
        command = self.bash_command([
            bash_path(SCRIPT), "--components-dir", bash_path(self.components_dir),
            "--component", "bsp-skills", "--repo-base-url", file_url(self.repo_base),
            "--work-root", bash_path(self.hub_root / ".tmp" / "component-sync-summary"),
            "--summary-file", bash_path(self.root),
        ])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid summary destination", result.stderr)
        self.assertEqual(hash_tree(target), before)

    def test_rolls_back_all_catalog_dirs_when_replacement_fails(self):
        (self.components_dir / "bsp-skills.yml").write_text(
            "repo: acme/bsp-skills\nref: main\nskills:\n"
            "  - path: source/bsp-env-setup\n    catalog_dir: bsp-env-setup\n"
            "  - path: source/bsp-env-setup\n    catalog_dir: bsp-env-second\n",
            encoding="utf-8",
        )
        second = self.hub_root / "skills" / "bsp-env-second" / "old.txt"
        second.parent.mkdir(parents=True)
        second.write_text("old\n", encoding="utf-8")
        first_before = hash_tree(self.hub_root / "skills" / "bsp-env-setup")
        second_before = hash_tree(second.parent)

        result = self.run_sync("bsp-skills", fail_after=1)

        self.assertNotEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.assertEqual(hash_tree(self.hub_root / "skills" / "bsp-env-setup"), first_before)
        self.assertEqual(hash_tree(second.parent), second_before)

    def test_compare_failure_rolls_back_prior_catalog_dir(self):
        (self.components_dir / "bsp-skills.yml").write_text(
            "repo: acme/bsp-skills\nref: main\nskills:\n"
            "  - path: source/bsp-env-setup\n    catalog_dir: bsp-env-setup\n"
            "  - path: source/bsp-env-setup\n    catalog_dir: bsp-env-second\n",
            encoding="utf-8",
        )
        second = self.hub_root / "skills" / "bsp-env-second"
        second.mkdir(parents=True)
        (second / "old.txt").write_text("old\n", encoding="utf-8")
        first_before, second_before = hash_tree(self.hub_root / "skills" / "bsp-env-setup"), hash_tree(second)
        result = self.run_sync("bsp-skills", fail_compare="bsp-env-second")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not compare catalog directory: bsp-env-second", result.stderr)
        self.assertEqual(hash_tree(self.hub_root / "skills" / "bsp-env-setup"), first_before)
        self.assertEqual(hash_tree(second), second_before)

    @unittest.skipIf(os.name == "nt", "Git Bash signal delivery is not POSIX on Windows")
    def test_term_during_backup_move_window_restores_original_tree(self):
        target = self.hub_root / "skills" / "bsp-env-setup"
        before = hash_tree(target)
        command = self.bash_command([
            bash_path(SCRIPT), "--components-dir", bash_path(self.components_dir),
            "--component", "bsp-skills", "--repo-base-url", file_url(self.repo_base),
            "--work-root", bash_path(self.hub_root / ".tmp" / "component-sync-signal"),
            "--summary-file", bash_path(self.root / "signal-summary.json"),
            "--pause-after-backup", "10",
        ])
        ready = self.root / "backup-ready"
        command.extend(["--ready-file", bash_path(ready)])
        process = subprocess.Popen(command, start_new_session=True)
        deadline = time.monotonic() + 15
        while not ready.exists() and time.monotonic() < deadline:
            if process.poll() is not None:
                self.fail(f"sync exited before ready marker: {process.returncode}")
            time.sleep(0.05)
        self.assertTrue(ready.exists(), "sync did not reach backup-ready transition")
        os.killpg(process.pid, signal.SIGTERM)
        self.assertEqual(process.wait(timeout=10), 143)
        self.assertEqual(hash_tree(target), before)


if __name__ == "__main__":
    unittest.main()
