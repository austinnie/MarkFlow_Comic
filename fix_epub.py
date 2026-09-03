import zipfile
from pathlib import Path
import shutil
import tempfile

def fix_epub(epub_path, output_path=None):
    epub_path = Path(epub_path)
    
    if not epub_path.exists():
        print(f"❌ 文件不存在: {epub_path}")
        return None
    
    if output_path is None:
        output_path = epub_path.parent / "manga_fixed.epub"
    else:
        output_path = Path(output_path)
    
    print(f"📖 修复 EPUB: {epub_path.name}")
    print(f"📁 输出: {output_path.name}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        
        # 1. 解压原 EPUB
        with zipfile.ZipFile(epub_path, 'r') as zf:
            zf.extractall(tmp)
        print("   ✅ 解压完成")
        
        # 2. 创建 nav.xhtml
        nav_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="UTF-8"/>
  <title>星际冒险</title>
</head>
<body>
  <nav epub:type="toc">
    <h1>目录</h1>
    <ol>
      <li><a href="images/page_001.jpg">第1页</a></li>
      <li><a href="images/page_002.jpg">第2页</a></li>
      <li><a href="images/page_003.jpg">第3页</a></li>
      <li><a href="images/page_004.jpg">第4页</a></li>
    </ol>
  </nav>
</body>
</html>'''
        
        nav_path = tmp / 'OEBPS' / 'nav.xhtml'
        with open(nav_path, 'w', encoding='utf-8') as f:
            f.write(nav_content)
        print("   ✅ 创建 nav.xhtml")
        
        # 3. 更新 content.opf
        opf_path = tmp / 'OEBPS' / 'content.opf'
        with open(opf_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 在 manifest 中添加 nav.xhtml
        if '<item id="nav"' not in content:
            content = content.replace(
                '<manifest>',
                '<manifest>\n    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
            )
            print("   ✅ 更新 manifest")
        else:
            print("   ⏭️ nav 已存在，跳过")
        
        # 在 spine 中添加 nav
        if '<itemref idref="nav"/>' not in content:
            content = content.replace(
                '<spine toc="ncx">',
                '<spine toc="ncx">\n    <itemref idref="nav"/>'
            )
            print("   ✅ 更新 spine")
        
        with open(opf_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 4. 重新打包
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in tmp.rglob('*'):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(tmp))
        
        print(f"   ✅ 打包完成")
    
    size_kb = output_path.stat().st_size / 1024
    print(f"\n✅ 修复完成: {output_path}")
    print(f"📊 大小: {size_kb:.1f} KB")
    return output_path

if __name__ == "__main__":
    epub_file = "E:/SD_OpenVINO/MarkFlow_Comic/skills/comics/manga_to_epub/output/manga_20260903_224002.epub"
    fix_epub(epub_file)