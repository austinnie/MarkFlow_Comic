# skills/comics/manga_style_unifier/skill.py
"""
画风统一器 - 将所有页面统一为同一画风
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


# ============================================================
# 画风配置
# ============================================================
STYLE_CONFIG = {
    "manga": {
        "name": "日漫",
        "prompt": "manga style, black and white, high contrast, detailed linework, screentone, japanese manga",
        "negative": "color, realistic, 3d, photo, painting"
    },
    "anime": {
        "name": "动漫",
        "prompt": "anime style, vibrant colors, cel shading, detailed eyes, beautiful, high quality animation",
        "negative": "realistic, 3d, photo, ugly, deformed"
    },
    "comic": {
        "name": "美漫",
        "prompt": "comic book style, bold colors, dramatic shading, american comic, superhero style",
        "negative": "anime, manga, realistic, photo"
    },
    "webtoon": {
        "name": "条漫",
        "prompt": "webtoon style, clean lines, soft colors, korean webcomic, vertical layout, modern",
        "negative": "rough, dark, realistic, 3d"
    },
    "watercolor": {
        "name": "水彩",
        "prompt": "watercolor painting style, soft edges, artistic, flowing colors, painterly",
        "negative": "hard edges, digital, realistic, photo"
    },
    "sketch": {
        "name": "素描",
        "prompt": "pencil sketch, graphite drawing, rough lines, hand-drawn, artistic sketch, white background",
        "negative": "color, photo, realistic, 3d, digital"
    }
}


class MangaStyleUnifier:
    """画风统一器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_style_unifier"
        self.version = "1.0.0"
        
        self.skill_dir = Path(__file__).parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        logger.info(f"MangaStyleUnifier v{self.version} 初始化完成")
        logger.info(f"  支持风格: {list(STYLE_CONFIG.keys())}")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """统一画风"""
        start_time = time.time()
        image_paths = kwargs.get('image_paths', [])
        style = kwargs.get('style', 'anime')
        strength = kwargs.get('strength', 0.65)
        steps = kwargs.get('steps', 30)
        
        if not image_paths:
            return {"status": "error", "error": "image_paths 是必填参数"}
        
        if style not in STYLE_CONFIG:
            return {
                "status": "error", 
                "error": f"未知风格: {style}，可用: {list(STYLE_CONFIG.keys())}"
            }
        
        logger.info(f"🎨 统一画风: {style}")
        logger.info(f"📁 处理 {len(image_paths)} 张图片")
        
        style_info = STYLE_CONFIG[style]
        results = []
        
        for i, img_path in enumerate(image_paths):
            logger.info(f"  处理 [{i+1}/{len(image_paths)}]: {Path(img_path).name}")
            
            try:
                # 调用风格迁移或重新生成
                result = self._apply_style(
                    image_path=img_path,
                    style=style,
                    style_info=style_info,
                    strength=strength,
                    steps=steps
                )
                
                if result and result.get('status') == 'success':
                    results.append({
                        "original": img_path,
                        "output": result.get('output_path'),
                        "success": True
                    })
                else:
                    results.append({
                        "original": img_path,
                        "error": result.get('error', '未知错误') if result else '处理失败',
                        "success": False
                    })
                    
            except Exception as e:
                logger.error(f"  处理失败: {e}")
                results.append({
                    "original": img_path,
                    "error": str(e),
                    "success": False
                })
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            "status": "success" if success_count > 0 else "partial",
            "total": len(image_paths),
            "success": success_count,
            "failed": len(image_paths) - success_count,
            "style": style,
            "results": results,
            "output_dir": str(self.output_dir),
            "metadata": {
                "style_name": style_info['name'],
                "strength": strength,
                "steps": steps,
                "generation_time": f"{time.time() - start_time:.2f}s"
            }
        }
    
    def _apply_style(self, image_path: str, style: str, style_info: Dict,
                     strength: float, steps: int) -> Optional[Dict]:
        """应用风格"""
        
        # 构建提示词
        prompt = style_info['prompt']
        negative = style_info.get('negative', 'ugly, deformed, low quality, blurry')
        
        # 方法1: 使用 style_transfer skill
        try:
            result = execute_skill(
                "style_transfer",
                image_path=image_path,
                style=style,
                strength=strength,
                steps=steps
            )
            if result and result.get('status') == 'success':
                return result
        except Exception as e:
            logger.warning(f"style_transfer 失败: {e}")
        
        # 方法2: 使用 sd_image_generator (img2img)
        try:
            result = execute_skill(
                "sd_image_generator",
                prompt=prompt,
                negative_prompt=negative,
                image_path=image_path,
                strength=strength,
                steps=steps,
                width=kwargs.get('width', 512),
                height=kwargs.get('height', 768)
            )
            if result and result.get('status') == 'success':
                return result
        except Exception as e:
            logger.warning(f"sd_image_generator 失败: {e}")
        
        # 方法3: 使用 real_to_anime (如果目标是动漫风格)
        if style in ['anime', 'manga', 'webtoon']:
            try:
                result = execute_skill(
                    "real_to_anime",
                    image_path=image_path,
                    style=style,
                    strength=strength
                )
                if result and result.get('status') == 'success':
                    return result
            except Exception as e:
                logger.warning(f"real_to_anime 失败: {e}")
        
        return None
    
    def __repr__(self):
        return f"<MangaStyleUnifier(name={self.name}, version={self.version})>"