#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量修正技能中的导入路径
将 skills.controlnet_img2img 改为 skills.image.controlnet_img2img
"""

import re
from pathlib import Path

def fix_import_paths(file_path: Path) -> bool:
    """修复文件中的导入路径"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # 修复错误的导入路径
        # 1. from skills.controlnet_img2img → from skills.image.controlnet_img2img
        content = re.sub(
            r'from skills\.controlnet_img2img\.skill import',
            r'from skills.image.controlnet_img2img.skill import',
            content
        )
        
        # 2. import skills.controlnet_img2img → import skills.image.controlnet_img2img
        content = re.sub(
            r'import skills\.controlnet_img2img',
            r'import skills.image.controlnet_img2img',
            content
        )
        
        # 3. from skills.controlnet_img2img import → from skills.image.controlnet_img2img import
        content = re.sub(
            r'from skills\.controlnet_img2img import',
            r'from skills.image.controlnet_img2img import',
            content
        )
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True
        return False
        
    except Exception as e:
        print(f"   ❌ 读取失败: {e}")
        return False


def main():
    print("=" * 60)
    print("  🔧 批量修正导入路径")
    print("  skills.controlnet_img2img → skills.image.controlnet_img2img")
    print("=" * 60)
    print()

    skills_dir = Path("skills")
    fixed = 0
    skipped = 0

    # 查找所有 skill.py
    skill_files = list(skills_dir.rglob("skill.py"))
    skill_files = [f for f in skill_files if "tests" not in str(f).lower()]

    print(f"📁 找到 {len(skill_files)} 个技能")
    print()

    for skill_file in sorted(skill_files):
        rel_path = f"{skill_file.parent.parent.name}/{skill_file.parent.name}"
        
        if fix_import_paths(skill_file):
            print(f"✅ 修复: {rel_path}")
            fixed += 1
        else:
            # print(f"⏭️  跳过: {rel_path}")
            skipped += 1

    print()
    print("=" * 60)
    print(f"📊 完成!")
    print(f"   ✅ 修复: {fixed} 个")
    print(f"   ⏭️  跳过: {skipped} 个")
    print("=" * 60)


if __name__ == "__main__":
    main()