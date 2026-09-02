# skills/colorize_sketch/skill.py
"""
çº¿ç¨¿ä¸è² Skill - ç»é»ç½çº¿ç¨¿/ç´ æä¸è²
å¤ç¨éç¨ ControlNet å¼æEEED + Lineart å¼ºå¶éçº¿Eé«å¹Eº¦éç»ä¸è²EE
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
    logger.warning("torch æEPIL æªå®è£E)

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# ä¸è²é£æ ¼é¢E®¾
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
    """çº¿ç¨¿ä¸è²æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "colorize_sketch"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # ==================== åå§ååºå±å¼æ ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±EControlNet å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ColorizeSketch v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  ä¸è²é£æ ¼: {len(COLOR_STYLES)} ç§E)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.85,  # ä¸è²å¿E¡»é«å¼ºåº¦éç»E
            'default_style': 'anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(COLOR_STYLES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æ§è¡çº¿ç¨¿ä¸è²"""
        start_time = time.time()
        logger.info(f"æ§è¡æè½: {self.name}")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            style = kwargs.get('style', self.config.get('default_style', 'anime'))
            if style not in COLOR_STYLES:
                return {"status": "error", "error": f"æªç¥é£æ ¼: {style}Eå¯ç¨: {list(COLOR_STYLES.keys())}"}

            style_config = COLOR_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.85))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # é»è®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{style}_{timestamp}.png")

            logger.info(f"ä¸è²é£æ ¼: {style}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",      # å¼ºå¶æåå¹²åçº¿ç¨¿
                controlnet_model="lineart",   # ä½¿ç¨æ¬å° Lineart æ¨¡åï¼å®ç¾éçº¿
                strength=strength,            # é«å¼ºåº¦éç»ï¼éæ¾è²å½©
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
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ColorizeSketch(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="çº¿ç¨¿ä¸è²å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEçº¿ç¨¿å¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--style", "-s", default="anime",
                        choices=list(COLOR_STYLES.keys()), help="ä¸è²é£æ ¼")
    parser.add_argument("--strength", type=float, default=0.85, help="éç»å¼ºåº¦")
    parser.add_argument("--steps", type=int, default=30, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ColorizeSketch(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))