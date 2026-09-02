# skills/colorize_sketch/skill.py
"""
çº¿ç¨¿ä¸è² Skill - ç»é»ç½çº¿ç¨¿/ç´ æä¸è²
å¤ç¨éç¨ ControlNet å¼æEEED + Lineart å¼ºå¶éçº¿Eé«å¹Eº¦éç»ä¸è²EE
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
    logger.warning("torch æEPIL æªå®è£E)

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# ä¸è²é£æ ¼é¢E®¾
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
    """çº¿ç¨¿ä¸è²æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "colorize_sketch"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # ==================== åå§ååºå±å¼æ ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±EControlNet å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ColorizeSketch v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  ä¸è²é£æ ¼: {len(COLOR_STYLES)} ç§E)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.85,  # ä¸è²å¿E¡»é«å¼ºåº¦éç»E
            'default_style': 'anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(COLOR_STYLES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æ§è¡çº¿ç¨¿ä¸è²"""
        start_time = time.time()
        logger.info(f"æ§è¡æè½: {self.name}")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            style = kwargs.get('style', self.config.get('default_style', 'anime'))
            if style not in COLOR_STYLES:
                return {"status": "error", "error": f"æªç¥é£æ ¼: {style}Eå¯ç¨: {list(COLOR_STYLES.keys())}"}

            style_config = COLOR_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.85))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # é»è®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{style}_{timestamp}.png")

            logger.info(f"ä¸è²é£æ ¼: {style}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",      # å¼ºå¶æåå¹²åçº¿ç¨¿
                controlnet_model="lineart",   # ä½¿ç¨æ¬å° Lineart æ¨¡åï¼å®ç¾éçº¿
                strength=strength,            # é«å¼ºåº¦éç»ï¼éæ¾è²å½©
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
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ColorizeSketch(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="çº¿ç¨¿ä¸è²å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEçº¿ç¨¿å¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--style", "-s", default="anime",
                        choices=list(COLOR_STYLES.keys()), help="ä¸è²é£æ ¼")
    parser.add_argument("--strength", type=float, default=0.85, help="éç»å¼ºåº¦")
    parser.add_argument("--steps", type=int, default=30, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ColorizeSketch(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))