# skills/comics/manga_to_pdf/skill.py
"""
漫画导出为 PDF
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL 未安装")


class MangaToPdf:
    """漫画 PDF 导出器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_to_pdf"
        self.version = "1.0.0"
        
        self.skill_dir = Path(__file__).parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        logger.info(f"MangaToPdf v{self.version} 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """导出为 PDF"""
        start_time = time.time()
        
        image_paths = kwargs.get('image_paths', [])
        output_path = kwargs.get('output_path')
        title = kwargs.get('title', '漫画')
        page_size = kwargs.get('page_size', 'A4')
        
        if not image_paths:
            return {"status": "error", "error": "image_paths 是必填参数"}
        
        if not output_path:
            from datetime import datetime
            output_path = str(self.output_dir / f"manga_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📄 导出 PDF: {output_path.name}")
        logger.info(f"📁 图片数: {len(image_paths)}")
        
        try:
            # 方法1: 使用 img2pdf
            try:
                import img2pdf
                with open(output_path, 'wb') as f:
                    f.write(img2pdf.convert(image_paths))
                
                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "pages": len(image_paths),
                    "method": "img2pdf",
                    "size": output_path.stat().st_size,
                    "metadata": {
                        "title": title,
                        "page_size": page_size,
                        "generation_time": f"{time.time() - start_time:.2f}s"
                    }
                }
            except ImportError:
                logger.warning("img2pdf 未安装，使用 PIL 方法")
            
            # 方法2: 使用 PIL 和 reportlab
            try:
                from reportlab.lib.pagesizes import A4, A3, LETTER
                from reportlab.pdfgen import canvas
                from reportlab.lib.utils import ImageReader
                
                page_sizes = {
                    'A4': A4,
                    'A3': A3,
                    'LETTER': LETTER
                }
                page_size_dims = page_sizes.get(page_size, A4)
                
                c = canvas.Canvas(str(output_path), pagesize=page_size_dims)
                page_w, page_h = page_size_dims
                
                for img_path in image_paths:
                    if not Path(img_path).exists():
                        continue
                    
                    img = Image.open(img_path)
                    
                    # 计算适应页面的尺寸
                    img_w, img_h = img.size
                    ratio = min(page_w / img_w, page_h / img_h) * 0.9
                    
                    draw_w = img_w * ratio
                    draw_h = img_h * ratio
                    x = (page_w - draw_w) / 2
                    y = (page_h - draw_h) / 2
                    
                    # 保存临时文件
                    temp_path = self.output_dir / f"temp_{Path(img_path).stem}.jpg"
                    img = img.convert('RGB')
                    img.save(temp_path, 'JPEG', quality=95)
                    
                    # 添加到 PDF
                    c.drawImage(str(temp_path), x, y, draw_w, draw_h)
                    c.showPage()
                    
                    # 清理临时文件
                    try:
                        temp_path.unlink()
                    except:
                        pass
                
                c.save()
                
                return {
                    "status": "success",
                    "output_path": str(output_path),
                    "pages": len(image_paths),
                    "method": "reportlab",
                    "size": output_path.stat().st_size,
                    "metadata": {
                        "title": title,
                        "page_size": page_size,
                        "generation_time": f"{time.time() - start_time:.2f}s"
                    }
                }
                
            except ImportError:
                logger.warning("reportlab 未安装")
            
            # 方法3: 使用 doc_generator
            try:
                from markflow.cli.commands import execute_skill
                
                # 构建内容
                content = f"# {title}\n\n"
                for i, img_path in enumerate(image_paths):
                    content += f"## 第{i+1}页\n\n![Page]({img_path})\n\n"
                
                result = execute_skill(
                    "doc_generator",
                    doc_type="pdf",
                    content=content,
                    output_path=str(output_path)
                )
                
                if result and result.get('status') == 'success':
                    return {
                        "status": "success",
                        "output_path": str(output_path),
                        "pages": len(image_paths),
                        "method": "doc_generator",
                        "size": output_path.stat().st_size,
                        "metadata": {
                            "title": title,
                            "generation_time": f"{time.time() - start_time:.2f}s"
                        }
                    }
            except Exception as e:
                logger.warning(f"doc_generator 失败: {e}")
            
            return {"status": "error", "error": "所有 PDF 导出方法都失败了"}
            
        except Exception as e:
            logger.error(f"PDF 导出失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def __repr__(self):
        return f"<MangaToPdf(name={self.name}, version={self.version})>"