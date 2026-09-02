# skills/comics/manga_bubble_adder/skill.py
"""
对话气泡添加器
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
    logger.warning("PIL 未安装，对话气泡功能受限")


class MangaBubbleAdder:
    """对话气泡添加器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_bubble_adder"
        self.version = "1.0.0"
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info(f"MangaBubbleAdder v{self.version} 初始化完成")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """添加对话气泡"""
        image_path = kwargs.get('image_path')
        dialogues = kwargs.get('dialogues', [])
        positions = kwargs.get('positions', [])
        bubble_style = kwargs.get('bubble_style', 'rounded')
        
        if not image_path:
            return {"status": "error", "error": "image_path 是必填参数"}
        
        if not PIL_AVAILABLE:
            return {"status": "error", "error": "PIL 未安装"}
        
        try:
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # 加载字体
            try:
                font = ImageFont.truetype("simhei.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # 添加对话
            for i, dialogue in enumerate(dialogues):
                if i < len(positions):
                    pos = positions[i]
                else:
                    pos = (50, 50 + i * 80)
                
                self._add_bubble(draw, dialogue, pos, font, bubble_style)
            
            # 保存
            output_path = self.output_dir / f"bubbled_{Path(image_path).name}"
            img.save(output_path)
            
            return {
                "status": "success",
                "output_path": str(output_path),
                "bubbles_added": len(dialogues)
            }
            
        except Exception as e:
            logger.error(f"添加气泡失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def _add_bubble(self, draw, text: str, pos: tuple, font, style: str):
        """添加单个气泡"""
        x, y = pos
        
        # 计算文本大小
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        padding = 20
        bubble_w = text_w + padding * 2
        bubble_h = text_h + padding * 2
        
        # 绘制气泡
        if style == 'rounded':
            # 圆角矩形
            draw.rounded_rectangle(
                (x, y, x + bubble_w, y + bubble_h),
                radius=15,
                fill='white',
                outline='black',
                width=2
            )
        else:
            # 普通矩形
            draw.rectangle(
                (x, y, x + bubble_w, y + bubble_h),
                fill='white',
                outline='black',
                width=2
            )
        
        # 绘制小三角（指向说话者）
        triangle_points = [
            (x + 30, y + bubble_h),
            (x + 40, y + bubble_h + 15),
            (x + 50, y + bubble_h)
        ]
        draw.polygon(triangle_points, fill='white', outline='black')
        
        # 绘制文本
        draw.text(
            (x + padding, y + padding),
            text,
            fill='black',
            font=font
        )
    
    def __repr__(self):
        return f"<MangaBubbleAdder(name={self.name})>"