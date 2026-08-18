import unittest
from pathlib import Path


POLICY_FILES = (
    "README.md",
    "README_cn.md",
    "CONTRIBUTING.md",
    "docs/PR-SUBMISSION.md",
    "components.d/README.md",
)
CHINESE_POLICY_FILES = set(POLICY_FILES) - {"README.md"}


class LicenseContractTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]

    def test_policy_docs_explain_frontmatter_and_content_license(self):
        for relative in POLICY_FILES:
            text = (self.repo / relative).read_text(encoding="utf-8")

            self.assertIn("Apache-2.0", text, relative)
            self.assertIn("CC-BY-4.0", text, relative)
            self.assertIn("metadata.content-license", text, relative)
            self.assertIn("license: Apache-2.0", text, relative)
            self.assertIn("SKILL.md", text, relative)
            self.assertIn("skill-card.md", text, relative)
            self.assertIn("references", text, relative)
            self.assertIn("ADR 0004", text, relative)
            if relative in CHINESE_POLICY_FILES:
                self.assertIn("建议同时声明", text, relative)
            else:
                self.assertIn("are recommended to declare", text, relative)

    def test_policy_docs_preserve_the_non_retroactive_dual_license_rule(self):
        for relative in POLICY_FILES:
            text = (self.repo / relative).read_text(encoding="utf-8")
            if relative in CHINESE_POLICY_FILES:
                self.assertIn("代码和脚本", text, relative)
                self.assertIn(
                    "不对既有内容追溯性重新授权", text.replace("\n", ""), relative
                )
            else:
                self.assertIn("code and scripts", text.lower(), relative)
                self.assertIn("does not retroactively relicense existing content", text, relative)


if __name__ == "__main__":
    unittest.main()
