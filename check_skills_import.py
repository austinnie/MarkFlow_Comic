#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查所有技能是否能正常导入（不执行）
"""

import sys
import importlib
from pathlib import Path
from typing import List, Tuple

# 添加项目根目录到路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def find_all_skills() -> List[Path]:
    """查找所有 skill.py 文件"""
    skills_dir = Path("skills")
    if not skills_dir.exists():
        return []
    
    # 递归查找所有 skill.py
    skill_files = list(skills_dir.rglob("skill.py"))
    # 排除 tests/ 目录
    skill_files = [f for f in skill_files if "tests" not in str(f).lower()]
    return skill_files


def extract_class_name(skill_file: Path) -> str:
    """从 skill.py 提取类名（使用正则，不导入模块）"""
    import re
    try:
        content = skill_file.read_text(encoding='utf-8')
        match = re.search(r'class\s+(\w+)\s*[:\(]', content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return None


def check_import(skill_file: Path) -> Tuple[bool, str]:
    """
    检查技能是否能正常导入
    
    Returns:
        (成功, 错误信息)
    """
    try:
        # 构建模块路径
        rel_path = skill_file.parent.relative_to("skills")
        module_path = f"skills.{'.'.join(rel_path.parts)}"
        
        # 尝试导入
        module = importlib.import_module(module_path)
        
        # 检查是否包含可执行类
        has_class = False
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and hasattr(attr, 'execute'):
                has_class = True
                class_name = attr_name
                break
        
        if has_class:
            return True, f"✅ {class_name}"
        else:
            return False, "❌ 未找到可执行类"
            
    except ImportError as e:
        return False, f"❌ ImportError: {e}"
    except SyntaxError as e:
        return False, f"❌ SyntaxError: {e}"
    except Exception as e:
        return False, f"❌ {type(e).__name__}: {e}"


def main():
    print("=" * 70)
    print("  🔍 检查所有技能是否能正常导入")
    print("=" * 70)
    print()
    
    skill_files = find_all_skills()
    
    if not skill_files:
        print("❌ 未找到任何技能")
        return
    
    print(f"📁 找到 {len(skill_files)} 个技能")
    print()
    print("-" * 70)
    
    success_count = 0
    fail_count = 0
    failed_skills = []
    
    for skill_file in sorted(skill_files):
        rel_path = skill_file.parent.relative_to("skills")
        skill_name = f"{rel_path.parent.name}/{rel_path.name}" if rel_path.parent.name != "skills" else rel_path.name
        
        success, message = check_import(skill_file)
        
        if success:
            success_count += 1
            print(f"  {skill_name:40} {message}")
        else:
            fail_count += 1
            failed_skills.append((skill_name, message))
            print(f"  {skill_name:40} {message}")
    
    print()
    print("-" * 70)
    print()
    print(f"📊 结果:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {fail_count}")
    
    if failed_skills:
        print()
        print("❌ 失败的技能详情:")
        for name, msg in failed_skills:
            print(f"   - {name}: {msg}")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()