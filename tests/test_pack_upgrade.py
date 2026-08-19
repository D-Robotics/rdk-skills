"""End-to-end tests for the workspace packs' setup.sh `--update` flow.

Runs the real setup.sh from the Hub's self-installable mirrors
(`skills/oe-skills-x5/`, `skills/oe-skills-s/`) against throwaway projects,
covering the P1 upgrade contract:

- fresh install records the pack VERSION plus an INSTALLED_REF anchor,
- `--update` is a no-op while versions match,
- `--update` on a version change rebuilds the workspace (no stale files),
- `--force` rebuilds even at the same version,
- the legacy plain-argument form `bash setup.sh <project-root>` keeps working.

The test bails out without `bash` on PATH (Windows CI-less environments) and
normalizes CRLF materialized by Windows checkouts before running bash.
"""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


def _find_bash():
    """Locate a bash usable from a native process, probing it first.

    A bare `bash` in CreateProcess resolves through System32 first, which on
    Windows 10/11 is the WSL launcher that cannot see Windows script paths.
    `shutil.which("bash")` already skips System32, but still probe: the PATH
    bash must be able to open a script whose path points into the temp dir.
    """
    candidates = []
    found = shutil.which("bash")
    if found:
        candidates.append(found)
    candidates += [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
    ]
    with tempfile.TemporaryDirectory() as temporary_directory:
        probe = Path(temporary_directory) / "probe.sh"
        probe.write_text("exit 0\n", encoding="utf-8")
        for candidate in candidates:
            if not Path(candidate).exists():
                continue
            result = subprocess.run(
                [candidate, str(probe)], capture_output=True, check=False
            )
            if result.returncode == 0:
                return candidate
    return None


BASH = _find_bash()


@unittest.skipUnless(BASH, "no usable bash found")
class PackSetupUpgradeTests(unittest.TestCase):
    # catalog_dir -> (workspace_dir, routing marker)
    PACKS = {
        "x5": ("oe-skills-x5", ".drobotics", "# X5 Workspace Rules"),
        "s": ("oe-skills-s", ".horizon", "# Horizon Workspace Rules"),
    }

    @classmethod
    def setUpClass(cls):
        repo = Path(__file__).resolve().parents[1]
        cls.mirrors = {}
        for pack, (catalog_dir, _ws_dir, _marker) in cls.PACKS.items():
            work = Path(tempfile.mkdtemp(prefix=f"setup-mirror-{pack}-"))
            mirror = work / catalog_dir
            shutil.copytree(repo / "skills" / catalog_dir, mirror)
            script = mirror / "setup.sh"
            script.write_text(
                script.read_text(encoding="utf-8"), encoding="utf-8", newline="\n"
            )
            cls.mirrors[pack] = mirror

    def _run_setup(self, mirror, project, *flags):
        """Run `bash setup.sh [flags...] <project>` from the mirror copy.

        Paths are passed with backslashes on Windows so the MSYS runtime
        converts them to POSIX form for bash; on CI they are plain POSIX.
        """
        return subprocess.run(
            [BASH, str(mirror / "setup.sh"), *flags, str(project)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(mirror),
            check=False,
        )

    def _install(self, pack, project):
        """Fresh plain install, asserting the legacy argument form works."""
        result = self._run_setup(self.mirrors[pack], project)
        self.assertEqual(
            result.returncode, 0, f"{result.stdout}\n{result.stderr}"
        )
        return result

    def test_fresh_install_records_version_and_ref_anchor(self):
        for pack, (catalog_dir, ws_dir, marker) in self.PACKS.items():
            with self.subTest(pack=pack), tempfile.TemporaryDirectory() as td:
                project = Path(td)
                (project / "CLAUDE.md").write_text("# my project\n", encoding="utf-8")

                self._install(pack, project)

                ws = project / ws_dir
                src_version = (
                    self.mirrors[pack] / "VERSION"
                ).read_text(encoding="utf-8").strip()
                self.assertTrue(ws.is_dir(), f"{ws_dir} not created")
                self.assertEqual(
                    (ws / "VERSION").read_text(encoding="utf-8").strip(),
                    src_version,
                )
                # Without --ref the anchor falls back to the resource VERSION.
                self.assertEqual(
                    (ws / "INSTALLED_REF").read_text(encoding="utf-8").strip(),
                    src_version,
                )
                self.assertIn(
                    marker,
                    (project / "CLAUDE.md").read_text(encoding="utf-8"),
                )
                self.assertGreater(
                    len(list((ws / "skills").glob("*/SKILL.md"))), 0
                )

    def test_update_is_noop_when_versions_match(self):
        for pack, (catalog_dir, ws_dir, marker) in self.PACKS.items():
            with self.subTest(pack=pack), tempfile.TemporaryDirectory() as td:
                project = Path(td)
                (project / "CLAUDE.md").write_text("# my project\n", encoding="utf-8")
                self._install(pack, project)

                # --update with matching VERSION must skip without rebuilding.
                result = self._run_setup(self.mirrors[pack], project, "--update")
                self.assertEqual(
                    result.returncode, 0, f"{result.stdout}\n{result.stderr}"
                )
                self.assertIn("Already up to date", result.stdout)
                self.assertNotIn("Upgrade:", result.stdout)
                version = (
                    project / ws_dir / "VERSION"
                ).read_text(encoding="utf-8").strip()
                self.assertEqual(
                    version,
                    (self.mirrors[pack] / "VERSION").read_text(encoding="utf-8").strip(),
                )

    def test_update_rebuilds_on_version_change_and_removes_stale_files(self):
        for pack, (catalog_dir, ws_dir, marker) in self.PACKS.items():
            with self.subTest(pack=pack), tempfile.TemporaryDirectory() as td:
                project = Path(td)
                (project / "CLAUDE.md").write_text("# my project\n", encoding="utf-8")
                self._install(pack, project)

                ws = project / ws_dir
                stale = ws / "docs" / "stale-from-old-version.md"
                if not stale.parent.is_dir():  # x5/s both mirror docs/ today
                    stale = ws / "stale-from-old-version.md"
                    stale.parent.mkdir(parents=True, exist_ok=True)
                stale.write_text("stale\n", encoding="utf-8")

                mirror = self.mirrors[pack]
                real_version = (mirror / "VERSION").read_text(encoding="utf-8")
                try:
                    # Simulate a new release being mirrored.
                    (mirror / "VERSION").write_text("9.1.0\n", encoding="utf-8")
                    result = self._run_setup(
                        mirror, project, "--update", "--ref", "v9.1.0"
                    )
                finally:
                    (mirror / "VERSION").write_text(real_version, encoding="utf-8")

                self.assertEqual(
                    result.returncode, 0, f"{result.stdout}\n{result.stderr}"
                )
                self.assertIn("Upgrade:", result.stdout)
                self.assertEqual(
                    (ws / "VERSION").read_text(encoding="utf-8").strip(), "9.1.0"
                )
                # The provided --ref is the recorded provenance anchor.
                self.assertEqual(
                    (ws / "INSTALLED_REF").read_text(encoding="utf-8").strip(),
                    "v9.1.0",
                )
                self.assertFalse(stale.exists(), "stale file survived the rebuild")

    def test_force_rebuilds_even_when_versions_match(self):
        for pack, (catalog_dir, ws_dir, marker) in self.PACKS.items():
            with self.subTest(pack=pack), tempfile.TemporaryDirectory() as td:
                project = Path(td)
                (project / "CLAUDE.md").write_text("# my project\n", encoding="utf-8")
                self._install(pack, project)

                ws = project / ws_dir
                stale = ws / "docs" / "user-removed-later.md"
                if not stale.parent.is_dir():
                    stale = ws / "user-removed-later.md"
                    stale.parent.mkdir(parents=True, exist_ok=True)
                stale.write_text("stale\n", encoding="utf-8")

                result = self._run_setup(
                    self.mirrors[pack], project, "--update", "--force"
                )
                self.assertEqual(
                    result.returncode, 0, f"{result.stdout}\n{result.stderr}"
                )
                self.assertIn("Upgrade:", result.stdout)
                self.assertFalse(stale.exists(), "--force did not rebuild")

    def test_unknown_flag_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td)
            (project / "CLAUDE.md").write_text("# my project\n", encoding="utf-8")
            result = self._run_setup(self.mirrors["s"], project, "--bogus")
            self.assertEqual(result.returncode, 2)
            self.assertIn("未知参数", result.stderr)


if __name__ == "__main__":
    unittest.main()