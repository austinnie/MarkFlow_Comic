#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整修复：
1. 先检测编码，如果是 GBK 则转为 UTF-8
2. 再修复导入路径
"""

import re
from pathlib import Path


def fix_encoding_and_imports(file_path: Path) -> tuple:
    """
    修复文件的编码和导入路径
    返回: (是否修复了编码, 是否修复了导入)
    """
    # 1. 尝试读取文件
    content = None
    encoding_fixed = False
    
    # 尝试 UTF-8
    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # 尝试 GBK
        try:
            content = file_path.read_text(encoding='gbk')
            encoding_fixed = True
            print(f"   📝 转码: {file_path.parent.name}")
        except UnicodeDecodeError:
            # 尝试 GB2312
            try:
                content = file_path.read_text(encoding='gb2312')
                encoding_fixed = True
                print(f"   📝 转码: {file_path.parent.name}")
            except UnicodeDecodeError:
                # 尝试 latin-1（兜底）
                try:
                    content = file_path.read_text(encoding='latin-1')
                    encoding_fixed = True
                    print(f"   📝 转码(latin-1): {file_path.parent.name}")
                except Exception as e:
                    print(f"   ❌ 无法读取: {file_path.parent.name} - {e}")
                    return (False, False)
    
    if content is None:
        return (False, False)
    
    original = content
    
    # 2. 修复导入路径
    # from skills.controlnet_img2img → from skills.image.controlnet_img2img
    content = re.sub(
        r'from skills\.controlnet_img2img\.skill import',
        r'from skills.image.controlnet_img2img.skill import',
        content
    )
    content = re.sub(
        r'import skills\.controlnet_img2img',
        r'import skills.image.controlnet_img2img',
        content
    )
    content = re.sub(
        r'from skills\.controlnet_img2img import',
        r'from skills.image.controlnet_img2img import',
        content
    )
    
    imports_fixed = (content != original)
    
    # 3. 保存（统一用 UTF-8）
    if encoding_fixed or imports_fixed:
        file_path.write_text(content, encoding='utf-8')
    
    return (encoding_fixed, imports_fixed)


def main():
    print("=" * 60)
    print("  🔧 完整修复：转码 + 修正导入路径")
    print("=" * 60)
    print()

    # 需要修复的技能列表（从错误信息中提取）
    bad_skills = [
        "change_skin_tone", "colorize_sketch",
        "day_night_transfer", "expand_to_full_body",
        "fantasy_character", "human_to_robot",
        "intimate_closeup", "mecha_generator",
        "nude_oil_painting", "nude_sculpture",
        "old_photo_restore", "photo_realistic",
        "photo_restorer", "pool_nude",
        "real_to_anime", "remove_clothes",
        "remove_object", "replace_object",
        "season_transfer", "sketch_to_real",
        "studio_nude", "style_transfer",
        "weather_transfer"
    ]

    fixed_encoding = 0
    fixed_imports = 0
    failed = []

    for skill_name in bad_skills:
        skill_file = Path(f"skills/image/{skill_name}/skill.py")
        if not skill_file.exists():
            print(f"⏭️  跳过: {skill_name} (文件不存在)")
            continue
        
        enc_fixed, imp_fixed = fix_encoding_and_imports(skill_file)
        
        if enc_fixed:
            fixed_encoding += 1
        if imp_fixed:
            fixed_imports += 1
        
        if enc_fixed or imp_fixed:
            status = []
            if enc_fixed:
                status.append("转码")
            if imp_fixed:
                status.append("导入修复")
            print(f"   ✅ {skill_name}: {', '.join(status)}")
        else:
            print(f"   ⏭️  {skill_name}: 无需修改")

    print()
    print("=" * 60)
    print(f"📊 完成!")
    print(f"   📝 转码: {fixed_encoding} 个")
    print(f"   🔧 导入修复: {fixed_imports} 个")
    if failed:
        print(f"   ❌ 失败: {len(failed)} 个 - {', '.join(failed)}")
    print("=" * 60)


if __name__ == "__main__":
    main()