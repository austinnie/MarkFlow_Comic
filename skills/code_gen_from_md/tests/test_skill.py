"""
code_gen_from_md 单元测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.code_gen_from_md.skill import CodeGenFromMd


class TestCodeGenFromMd(unittest.TestCase):
    """
    CodeGenFromMd 测试类
    """

    def setUp(self):
        """测试前准备"""
        self.skill = CodeGenFromMd()

    def test_execute_with_valid_params(self):
        """测试正常执行"""
        result = self.skill.execute(md_file="", md_content="", language='python', model='qwen2.5:7b', mode='full')
        self.assertEqual(result.get("status"), "success")
        self.assertIn("result", result)

    def test_skill_metadata(self):
        """测试技能元数据"""
        self.assertEqual(self.skill.name, "code_gen_from_md")
        self.assertIsInstance(self.skill.version, str)


if __name__ == "__main__":
    unittest.main()