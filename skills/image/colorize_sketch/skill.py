# skills/colorize_sketch/skill.py
"""
郤ｿ遞ｿ荳願牡 Skill - 扈咎ｻ醍區郤ｿ遞ｿ/邏謠丈ｸ願牡
螟咲畑騾夂畑 ControlNet 蠑墓梼・・ED + Lineart 蠑ｺ蛻ｶ髞∫ｺｿ・碁ｫ伜ｹ・ｺｦ驥咲ｻ倅ｸ願牡・・
"""

import time
import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("torch 謌・PIL 譛ｪ螳芽｣・)

# ==================== 蠑募・騾夂畑蠑墓梼・域婿譯・・・====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"騾夂畑 ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")

# 荳願牡鬟取ｼ鬚・ｮｾ
COLOR_STYLES = {
    "anime": {
        "prompt": "anime style, vibrant colors, cel shading, beautiful, detailed coloring, masterpiece, best quality, 2d illustration",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed, black and white"
    },
    "realistic": {
        "prompt": "photorealistic, vibrant colors, natural lighting, detailed, high quality, masterpiece, beautiful coloring",
        "negative": "anime, cartoon, ugly, deformed, blurry, black and white"
    },
    "watercolor": {
        "prompt": "watercolor painting, soft colors, artistic, flowing, delicate, masterpiece, high quality, beautiful coloring",
        "negative": "photorealistic, 3d render, hard edges, anime, black and white"
    },
    "vintage": {
        "prompt": "vintage style, warm tones, nostalgic, retro coloring, soft, masterpiece, high quality",
        "negative": "photorealistic, 3d render, ugly, deformed, black and white"
    },
    "pastel": {
        "prompt": "pastel colors, soft, gentle, delicate, beautiful coloring, masterpiece, high quality, cute",
        "negative": "photorealistic, 3d render, dark, ugly, black and white"
    },
    "vibrant": {
        "prompt": "vibrant colors, colorful, rich colors, stunning, eye-catching, masterpiece, high quality, beautiful",
        "negative": "photorealistic, 3d render, ugly, deformed, black and white, dull"
    }
}


class ColorizeSketch:
    """郤ｿ遞ｿ荳願牡謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "colorize_sketch"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 蠑ｺ蛻ｶ譛ｬ謚閭ｽ霎灘・逶ｮ蠖・====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # ==================== 蛻晏ｧ句喧蠎募ｱょｼ墓梼 ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  笨・蠎募ｱ・ControlNet 蠑墓梼蛻晏ｧ句喧謌仙粥")
            except Exception as e:
                logger.warning(f"  蠎募ｱょｼ墓梼蛻晏ｧ句喧螟ｱ雍･: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ColorizeSketch v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  荳願牡鬟取ｼ: {len(COLOR_STYLES)} 遘・)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.85,  # 荳願牡蠢・｡ｻ鬮伜ｼｺ蠎ｦ驥咲ｻ・
            'default_style': 'anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(COLOR_STYLES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """謇ｧ陦檎ｺｿ遞ｿ荳願牡"""
        start_time = time.time()
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name}")

        try:
            # ==================== 荳･譬ｼ霍ｯ蠕・｡鬪・====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 譏ｯ蠢・｡ｫ蜿よ焚"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}縲りｯｷ譽譟･霍ｯ蠕・弍蜷ｦ豁｣遑ｮ・・}

            style = kwargs.get('style', self.config.get('default_style', 'anime'))
            if style not in COLOR_STYLES:
                return {"status": "error", "error": f"譛ｪ遏･鬟取ｼ: {style}・悟庄逕ｨ: {list(COLOR_STYLES.keys())}"}

            style_config = COLOR_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.85))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{style}_{timestamp}.png")

            logger.info(f"荳願牡鬟取ｼ: {style}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",      # 蠑ｺ蛻ｶ謠仙叙蟷ｲ蜃郤ｿ遞ｿ
                controlnet_model="lineart",   # 菴ｿ逕ｨ譛ｬ蝨ｰ Lineart 讓｡蝙具ｼ悟ｮ檎ｾ朱煤郤ｿ
                strength=strength,            # 鬮伜ｼｺ蠎ｦ驥咲ｻ假ｼ碁㈱謾ｾ濶ｲ蠖ｩ
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "style": style,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "lineart"
                }
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ColorizeSketch(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="郤ｿ遞ｿ荳願牡蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・郤ｿ遞ｿ蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--style", "-s", default="anime",
                        choices=list(COLOR_STYLES.keys()), help="荳願牡鬟取ｼ")
    parser.add_argument("--strength", type=float, default=0.85, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ColorizeSketch(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))