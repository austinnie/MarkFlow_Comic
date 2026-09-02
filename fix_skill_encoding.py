#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
强制修复技能文件编码问题
1. 检测文件编码
2. 如果非 UTF-8，重新保存为 UTF-8
3. 添加编码声明
"""

import os
import re
from pathlib import Path


def detect_encoding(file_path: Path):
    """检测文件编码"""
    import chardet
    
    with open(file_path, 'rb') as f:
        raw = f.read()
    result = chardet.detect(raw)
    return result['encoding'], raw


def fix_file(file_path: Path) -> bool:
    """修复单个文件"""
    try:
        # 检测编码
        encoding, raw = detect_encoding(file_path)
        
        # 如果检测到的编码不是 UTF-8，重新解码
        if encoding and encoding.lower() not in ['utf-8', 'ascii']:
            try:
                content = raw.decode(encoding)
            except Exception:
                # 尝试 gbk
                content = raw.decode('gbk')
        else:
            # 尝试用 UTF-8 解码
            try:
                content = raw.decode('utf-8')
            except UnicodeDecodeError:
                content = raw.decode('gbk')
        
        # 检查是否有 shebang 行
        lines = content.split('\n')
        modified = False
        
        # 检查是否已有编码声明
        has_coding = False
        for i, line in enumerate(lines[:5]):
            if re.search(r'coding[:=]\s*utf-?8', line, re.IGNORECASE):
                has_coding = True
                break
        
        if not has_coding:
            # 插入编码声明
            if lines and lines[0].startswith('#!'):
                lines.insert(1, '# -*- coding: utf-8 -*-')
            else:
                lines.insert(0, '# -*- coding: utf-8 -*-')
            modified = True
        
        # 重新保存
        if modified:
            file_path.write_text('\n'.join(lines), encoding='utf-8')
            return True
        return False
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return False


def main():
    print("=" * 60)
    print("  🔧 强制修复技能文件编码")
    print("=" * 60)
    print()

    # 尝试安装 chardet
    try:
        import chardet
    except ImportError:
        print("⚠️ 正在安装 chardet...")
        os.system("pip install chardet -q")
        import chardet

    skills_dir = Path("skills")
    fixed = 0
    skipped = 0
    failed = 0

    # 找出所有 skill.py
    skill_files = list(skills_dir.rglob("skill.py"))
    skill_files = [f for f in skill_files if "tests" not in str(f).lower()]

    print(f"📁 找到 {len(skill_files)} 个技能")
    print()

    for skill_file in sorted(skill_files):
        rel_path = f"{skill_file.parent.parent.name}/{skill_file.parent.name}"
        
        try:
            if fix_file(skill_file):
                print(f"✅ 修复: {rel_path}")
                fixed += 1
            else:
                print(f"⏭️  跳过: {rel_path} (已有编码声明)")
                skipped += 1
        except Exception as e:
            print(f"❌ 失败: {rel_path} - {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"📊 完成!")
    print(f"   ✅ 修复: {fixed} 个")
    print(f"   ⏭️  跳过: {skipped} 个")
    print(f"   ❌ 失败: {failed} 个")
    print("=" * 60)


if __name__ == "__main__":
    main()