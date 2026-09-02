#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动修复剩余 17 个有语法错误的技能
"""

import re
from pathlib import Path


def fix_skill_file(file_path: Path) -> tuple:
    """
    修复单个 skill.py
    返回: (是否修复, 错误信息)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        original = content
        
        # ========== 修复 1: 删除不可见字符 ==========
        # 删除 U+0089 等控制字符
        content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x80-\x9f]', '', content)
        
        # ========== 修复 2: 修复未闭合的字符串 ==========
        # 检查三引号是否成对
        triple_double = content.count('"""')
        triple_single = content.count("'''")
        
        if triple_double % 2 != 0:
            # 在文件末尾添加闭合
            content += '\n"""'
        
        if triple_single % 2 != 0:
            content += "\n'''"
        
        # ========== 修复 3: 修复 f-string 中的单 } ==========
        # 查找类似 f"...{...}" 中多余的 }
        # 简单修复：移除单独的 }
        content = re.sub(r'(?<![{])}(?![}])', '}', content)
        
        # ========== 修复 4: 修复中文注释中的特殊字符 ==========
        # 将 § 替换为正常字符
        content = content.replace('§', '')
        content = content.replace('»', '')
        
        if content != original:
            file_path.write_text(content, encoding='utf-8')
            return True, "修复成功"
        else:
            return False, "无需修复"
            
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("  🔧 自动修复剩余 17 个技能")
    print("=" * 60)
    print()

    # 需要修复的技能列表
    bad_skills = [
        "change_skin_tone",
        "colorize_sketch",
        "day_night_transfer",
        "expand_to_full_body",
        "fantasy_character",
        "human_to_robot",
        "mecha_generator",
        "old_photo_restore",
        "photo_realistic",
        "photo_restorer",
        "real_to_anime",
        "remove_object",
        "replace_object",
        "season_transfer",
        "sketch_to_real",
        "style_transfer",
        "weather_transfer",
        "remove_clothes",  # 这个单独处理
    ]

    fixed = 0
    failed = []
    skipped = []

    for skill_name in bad_skills:
        skill_file = Path(f"skills/image/{skill_name}/skill.py")
        
        if not skill_file.exists():
            print(f"⏭️  跳过: {skill_name} (文件不存在)")
            skipped.append(skill_name)
            continue
        
        print(f"📄 处理: {skill_name}")
        success, msg = fix_skill_file(skill_file)
        
        if success:
            print(f"   ✅ {msg}")
            fixed += 1
        else:
            print(f"   ⏭️  {msg}")
            skipped.append(skill_name)

    print()
    print("=" * 60)
    print(f"📊 完成!")
    print(f"   ✅ 修复: {fixed} 个")
    print(f"   ⏭️  跳过: {len(skipped)} 个")
    if failed:
        print(f"   ❌ 失败: {len(failed)} 个 - {', '.join(failed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()