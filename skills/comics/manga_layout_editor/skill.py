# skills/comics/manga_layout_editor/skill.py
"""
漫画排版编辑器
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class MangaLayoutEditor:
    """漫画排版编辑器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_layout_editor"
        self.version = "1.0.0"
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"MangaLayoutEditor v{self.version} 初始化完成")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """排版漫画"""
        image_paths = kwargs.get('image_paths', [])
        layout_type = kwargs.get('layout_type', 'grid')
        title = kwargs.get('title', '漫画')
        
        if not image_paths:
            return {"status": "error", "error": "image_paths 是必填参数"}
        
        if not PIL_AVAILABLE:
            return {"status": "error", "error": "PIL 未安装"}
        
        try:
            # 加载图片
            images = []
            for path in image_paths:
                if Path(path).exists():
                    img = Image.open(path)
                    images.append(img)
            
            if not images:
                return {"status": "error", "error": "没有有效的图片"}
            
            # 统一大小
            target_w, target_h = 512, 768
            resized = []
            for img in images:
                resized.append(img.resize((target_w, target_h), Image.Resampling.LANCZOS))
            
            # 根据布局类型排版
            if layout_type == 'grid':
                result = self._grid_layout(resized, title)
            elif layout_type == 'vertical':
                result = self._vertical_layout(resized, title)
            elif layout_type == 'horizontal':
                result = self._horizontal_layout(resized, title)
            else:
                result = self._grid_layout(resized, title)
            
            # 保存
            from datetime import datetime
            output_path = self.output_dir / f"layout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            result.save(output_path)
            
            return {
                "status": "success",
                "output_path": str(output_path),
                "pages": len(images),
                "layout_type": layout_type
            }
            
        except Exception as e:
            logger.error(f"排版失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def _grid_layout(self, images: List[Image.Image], title: str) -> Image.Image:
        """网格布局"""
        num = len(images)
        cols = 2 if num > 2 else num
        rows = (num + cols - 1) // cols
        
        w, h = images[0].size
        padding = 20
        
        canvas_w = cols * w + (cols + 1) * padding
        canvas_h = rows * h + (rows + 1) * padding + 80
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        # 标题
        try:
            font = ImageFont.truetype("simhei.ttf", 36)
        except:
            font = ImageFont.load_default()
        draw.text((canvas_w//2 - len(title)*9, 20), title, fill='black', font=font)
        
        # 粘贴图片
        for i, img in enumerate(images):
            row = i // cols
            col = i % cols
            x = padding + col * (w + padding)
            y = 80 + row * (h + padding)
            canvas.paste(img, (x, y))
        
        return canvas
    
    def _vertical_layout(self, images: List[Image.Image], title: str) -> Image.Image:
        """垂直布局（条漫风格）"""
        w, h = images[0].size
        padding = 20
        
        canvas_w = w + padding * 2
        canvas_h = sum(h for _ in images) + padding * (len(images) + 1) + 80
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        try:
            font = ImageFont.truetype("simhei.ttf", 36)
        except:
            font = ImageFont.load_default()
        draw.text((canvas_w//2 - len(title)*9, 20), title, fill='black', font=font)
        
        y = 80 + padding
        for img in images:
            canvas.paste(img, (padding, y))
            y += h + padding
        
        return canvas
    
    def _horizontal_layout(self, images: List[Image.Image], title: str) -> Image.Image:
        """水平布局"""
        w, h = images[0].size
        padding = 20
        
        canvas_w = sum(w for _ in images) + padding * (len(images) + 1)
        canvas_h = h + padding * 2 + 80
        
        canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
        draw = ImageDraw.Draw(canvas)
        
        try:
            font = ImageFont.truetype("simhei.ttf", 36)
        except:
            font = ImageFont.load_default()
        draw.text((canvas_w//2 - len(title)*9, 20), title, fill='black', font=font)
        
        x = padding
        y = 80 + padding
        for img in images:
            canvas.paste(img, (x, y))
            x += w + padding
        
        return canvas
    
    def __repr__(self):
        return f"<MangaLayoutEditor(name={self.name})>"