# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 D-Robotics. All rights reserved.

"""Behavioral tests for data-only README regeneration."""

from collections import Counter
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "regenerate_readme.py"


class ReadmeRegenerationTests(unittest.TestCase):
    def _catalog_rows(self, filename, section):
        content = (ROOT / filename).read_text(encoding="utf-8")
        start = f"<!-- {section}-table-start -->"
        end = f"<!-- {section}-table-end -->"
        self.assertEqual(content.count(start), 1)
        self.assertEqual(content.count(end), 1)
        table = content.split(start)[1].split(end)[0]
        rows = {}
        for name, cells in re.findall(r"^\| \*\*(.*?)\*\* \|(.*)$", table, re.MULTILINE):
            # Translate display labels only; descriptions and row order may differ.
            name = name.replace("OE 工具链", "OE Tool Chain")
            self.assertNotIn(name, rows, f"duplicate component in {filename}")
            rows[name] = Counter(re.findall(r"\]\(([^)]+)\)", cells))
        self.assertTrue(rows, f"missing component rows in {filename}")
        return rows

    def test_bilingual_skill_catalog_matches_per_component(self):
        self.assertEqual(
            self._catalog_rows("README.md", "skills"),
            self._catalog_rows("README_cn.md", "skills"),
            "Chinese skill links must match English links under the same component",
        )

    def test_bilingual_feedback_links_match_per_component(self):
        self.assertEqual(
            self._catalog_rows("README.md", "help"),
            self._catalog_rows("README_cn.md", "help"),
            "Chinese source-repository feedback links must match English links",
        )

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
