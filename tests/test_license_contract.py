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
POLICY_LICENSE_MAPPINGS = {
    "README.md": (
        "License mapping: code and scripts = Apache-2.0; SKILL.md, "
        "skill-card.md, references, and other documentation content = CC-BY-4.0."
    ),
    "README_cn.md": (
        "许可证映射：代码和脚本 = Apache-2.0；SKILL.md、skill-card.md、references "
        "和其他文档内容 = CC-BY-4.0。"
    ),
    "CONTRIBUTING.md": (
        "许可证映射：代码和脚本 = Apache-2.0；SKILL.md、skill-card.md、references "
        "和其他文档内容 = CC-BY-4.0。"
    ),
    "docs/PR-SUBMISSION.md": (
        "许可证映射：代码和脚本 = Apache-2.0；SKILL.md、skill-card.md、references "
        "和其他文档内容 = CC-BY-4.0。"
    ),
    "components.d/README.md": (
        "许可证映射：代码和脚本 = Apache-2.0；SKILL.md、skill-card.md、references "
        "和其他文档内容 = CC-BY-4.0。"
    ),
}


class LicenseContractTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[1]

    def test_policy_docs_bind_file_types_to_licenses(self):
        for relative in POLICY_FILES:
            text = (self.repo / relative).read_text(encoding="utf-8")

            self.assertIn(POLICY_LICENSE_MAPPINGS[relative], text, relative)
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
