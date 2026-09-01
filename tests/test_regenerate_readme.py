# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Behavioral tests for data-only README regeneration."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "regenerate_readme.py"


class ReadmeRegenerationTests(unittest.TestCase):
    def test_source_controlled_directory_name_is_data_not_python_source(self):
        """A source filename that closes triple quotes must remain inert data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = Path(temp_dir)
            (repository / "components.d").mkdir()
            malicious_name = (
                "evil''';__import__('pathlib').Path('PWNED').write_text('owned');'''"
            )
            skill = repository / "skills" / "oe-pack" / malicious_name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text("---\nname: inert\n---\n", encoding="utf-8")
            (repository / "components.d" / "oe.yml").write_text(
                "name: OE Skills\n"
                "repo: D-Robotics/oe-skills-x5\n"
                "description: Workspace skills\n"
                "install_type: workspace\n"
                "skills:\n"
                "  - path: x5\n"
                "    catalog_dir: oe-pack\n"
                "links:\n"
                "  contributing: CONTRIBUTING.md\n"
                "  discussions: true\n",
                encoding="utf-8",
            )
            (repository / "README.md").write_text(
                "<!-- skills-table-start -->\nold\n<!-- skills-table-end -->\n"
                "<!-- help-table-start -->\nold\n<!-- help-table-end -->\n",
                encoding="utf-8",
            )
            env = {**os.environ, "GH_TOKEN": "must-remain-unread"}

            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--root", str(repository)],
                env=env,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((repository / "PWNED").exists())
            readme = (repository / "README.md").read_text(encoding="utf-8")
            self.assertIn("%27%27%27", readme)
            self.assertIn("&#x27;&#x27;&#x27;", readme)


if __name__ == "__main__":
    unittest.main()
