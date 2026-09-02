# skills/comics/manga_to_epub/skill.py
"""
漫画导出为 EPUB
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class MangaToEpub:
    """漫画 EPUB 导出器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_to_epub"
        self.version = "1.0.0"
        
        self.skill_dir = Path(__file__).parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        logger.info(f"MangaToEpub v{self.version} 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """导出为 EPUB"""
        start_time = time.time()
        
        image_paths = kwargs.get('image_paths', [])
        output_path = kwargs.get('output_path')
        title = kwargs.get('title', '漫画')
        author = kwargs.get('author', 'AI 生成')
        description = kwargs.get('description', 'AI 生成的漫画')
        
        if not image_paths:
            return {"status": "error", "error": "image_paths 是必填参数"}
        
        if not output_path:
            from datetime import datetime
            output_path = str(self.output_dir / f"manga_{datetime.now().strftime('%Y%m%d_%H%M%S')}.epub")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📖 导出 EPUB: {output_path.name}")
        logger.info(f"📁 图片数: {len(image_paths)}")
        
        try:
            # 方法1: 使用 doc_generator
            try:
                from markflow.cli.commands import execute_skill
                
                # 构建内容
                content = f"# {title}\n\n"
                content += f"**作者**: {author}\n\n"
                content += f"{description}\n\n---\n\n"
                
                for i, img_path in enumerate(image_paths):
                    if Path(img_path).exists():
                        content += f"## 第{i+1}页\n\n![Page {i+1}]({img_path})\n\n"
                
                result = execute_skill(
                    "doc_generator",
                    doc_type="epub",
                    content=content,
                    output_path=str(output_path),
                    title=title,
                    author=author
                )
                
                if result and result.get('status') == 'success':
                    return {
                        "status": "success",
                        "output_path": str(output_path),
                        "pages": len(image_paths),
                        "method": "doc_generator",
                        "size": output_path.stat().st_size if output_path.exists() else 0,
                        "metadata": {
                            "title": title,
                            "author": author,
                            "generation_time": f"{time.time() - start_time:.2f}s"
                        }
                    }
            except Exception as e:
                logger.warning(f"doc_generator 失败: {e}")
            
            # 方法2: 手动构建 EPUB (简化版)
            try:
                import zipfile
                from datetime import datetime
                
                # 创建 EPUB 结构
                epub_dir = self.output_dir / f"epub_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                epub_dir.mkdir(exist_ok=True)
                
                # 创建 META-INF
                meta_inf = epub_dir / "META-INF"
                meta_inf.mkdir(exist_ok=True)
                
                # container.xml
                with open(meta_inf / "container.xml", 'w', encoding='utf-8') as f:
                    f.write('''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>''')
                
                # OEBPS
                oebps = epub_dir / "OEBPS"
                oebps.mkdir(exist_ok=True)
                
                # 复制图片
                images_dir = oebps / "images"
                images_dir.mkdir(exist_ok=True)
                
                image_filenames = []
                for i, img_path in enumerate(image_paths):
                    if Path(img_path).exists():
                        img_name = f"page_{i+1:03d}.jpg"
                        from PIL import Image
                        img = Image.open(img_path)
                        img = img.convert('RGB')
                        img.save(images_dir / img_name, 'JPEG', quality=90)
                        image_filenames.append(img_name)
                
                # content.opf
                with open(oebps / "content.opf", 'w', encoding='utf-8') as f:
                    f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:description>{description}</dc:description>
    <dc:date>{datetime.now().isoformat()}</dc:date>
    <dc:language>zh-CN</dc:language>
    <meta property="dcterms:modified">{datetime.now().isoformat()}Z</meta>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
''')
                    for i, name in enumerate(image_filenames):
                        f.write(f'    <item id="page_{i+1}" href="images/{name}" media-type="image/jpeg"/>\n')
                    f.write('''  </manifest>
  <spine>
''')
                    for i in range(len(image_filenames)):
                        f.write(f'    <itemref idref="page_{i+1}"/>\n')
                    f.write('''  </spine>
</package>''')
                
                # toc.ncx
                with open(oebps / "toc.ncx", 'w', encoding='utf-8') as f:
                    f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="123456789X"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{title}</text></docTitle>
  <navMap>
''')
                    for i in range(len(image_filenames)):
                        f.write(f'''    <navPoint id="page_{i+1}" playOrder="{i+1}">
      <navLabel><text>第{i+1}页</text></navLabel>
      <content src="images/{image_filenames[i]}"/>
    </navPoint>
''')
                    f.write('''  </navMap>
</ncx>''')
                
                # 打包
                import zipfile
                with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in epub_dir.rglob('*'):
                        if file_path.is_file():
                            zf.write(file_path, file_path.relative_to(epub_dir))
                
                # 清理
                import shutil
                shutil.rmtree(epub_dir)
                
                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "pages": len(image_filenames),
                    "method": "manual",
                    "size": output_path.stat().st_size if output_path.exists() else 0,
                    "metadata": {
                        "title": title,
                        "author": author,
                        "generation_time": f"{time.time() - start_time:.2f}s"
                    }
                }
                
            except ImportError as e:
                logger.warning(f"EPUB 手动构建失败: {e}")
            
            return {"status": "error", "error": "所有 EPUB 导出方法都失败了"}
            
        except Exception as e:
            logger.error(f"EPUB 导出失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def __repr__(self):
        return f"<MangaToEpub(name={self.name}, version={self.version})>"