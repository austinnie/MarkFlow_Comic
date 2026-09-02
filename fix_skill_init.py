#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量创建技能 __init__.py
为所有包含 skill.py 但缺少 __init__.py 的技能目录自动生成
"""

import os
import re
from pathlib import Path

def extract_class_name(skill_file_path: Path) -> str:
    """从 skill.py 中提取类名"""
    try:
        content = skill_file_path.read_text(encoding='utf-8')
        # 匹配 class ClassName: 或 class ClassName(
        match = re.search(r'class\s+(\w+)\s*[:\(]', content)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "ChangePose"  # 默认类名


def main():
    skills_dir = Path("skills")
    
    if not skills_dir.exists():
        print(f"❌ 技能目录不存在: {skills_dir}")
        return
    
    created = 0
    skipped = 0
    
    print("=" * 60)
    print("  🔧 批量创建技能 __init__.py")
    print("=" * 60)
    print()
    print(f"📂 扫描: {skills_dir.absolute()}")
    print()
    
    # 递归查找所有 skill.py
    skill_files = list(skills_dir.rglob("skill.py"))
    
    # 过滤掉 tests/ 目录下的 skill.py
    skill_files = [f for f in skill_files if "tests" not in str(f).lower()]
    
    print(f"📁 找到 {len(skill_files)} 个技能")
    print()
    
    for skill_file in skill_files:
        skill_dir = skill_file.parent
        init_file = skill_dir / "__init__.py"
        
        # 跳过分类目录本身（如果 skill.py 直接在 image/content 等目录下）
        # 只处理 skills/{类别}/{技能名}/ 这种结构
        if skill_dir.parent.name in ["image", "content", "core", "comics", "utils"]:
            if init_file.exists():
                skipped += 1
                print(f"⏭️  跳过: {skill_dir.parent.name}/{skill_dir.name} (已存在)")
            else:
                class_name = extract_class_name(skill_file)
                init_content = f"from .skill import {class_name}\n"
                init_file.write_text(init_content, encoding='utf-8')
                created += 1
                print(f"✅ 创建: {skill_dir.parent.name}/{skill_dir.name} -> {class_name}")
    
    print()
    print("=" * 60)
    print(f"📊 完成!")
    print(f"   ✅ 创建: {created} 个")
    print(f"   ⏭️  跳过: {skipped} 个（已存在）")
    print("=" * 60)


if __name__ == "__main__":
    main()