# skills/real_to_anime/skill.py
"""
çäººè½¬å¨æ¼« Skill - å°Eå®çEçE½¬æ¢ä¸ºå¨æ¼«é£æ ¼
å¤ç¨éç¨ ControlNet å¼æEEpenPoseä¿æå¿æE¼é«å¹Eº¦éçè½¬é£æ ¼EE
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

# å¨æ¼«é£æ ¼é¢E®¾
ANIME_STYLES = {
    "gibli": {
        "prompt": "studio ghibli style, anime, beautiful, soft colors, masterpiece, best quality, 2d animation, hayao miyazaki style",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "shinkai": {
        "prompt": "makoto shinkai style, anime, vibrant colors, beautiful lighting, masterpiece, best quality, your name style, 2d animation",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "jojo": {
        "prompt": "jojo's bizarre adventure style, anime, bold colors, dynamic, masterpiece, best quality, 2d animation, dramatic",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "classic": {
        "prompt": "classic anime style, 90s anime, vibrant colors, beautiful, masterpiece, best quality, 2d illustration",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "modern": {
        "prompt": "modern anime style, beautiful, vibrant colors, detailed, masterpiece, best quality, 2d illustration, high quality",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "manga": {
        "prompt": "manga style, black and white, manga art, masterpiece, best quality, 2d illustration, comic style",
        "negative": "photorealistic, 3d render, realistic, color, ugly, deformed"
    }
}


class RealToAnime:
    """çäººè½¬å¨æ¼«æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "real_to_anime"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # ==================== ååååºå±å¼æ ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±EControlNet å¼æåååæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåååå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"RealToAnime v{self.version} åååå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  å¨æ¼«é£æ ¼: {len(ANIME_STYLES)} çE)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 35,
            'default_strength': 0.8, # è½¬å¨æ¼«éè¦è¾E«çéçå¹Eº¦æ¥æ¹åçé£E
            'default_style': 'modern',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(ANIME_STYLES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æè¡çäººè½¬å¨æ¼«"""
        start_time = time.time()
        logger.info(f"æè¡æè½: {self.name}")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            style = kwargs.get('style', self.config.get('default_style', 'modern'))
            if style not in ANIME_STYLES:
                return {"status": "error", "error": f"æªç¥é£æ ¼: {style}Eå¯ç¨: {list(ANIME_STYLES.keys())}"}

            style_config = ANIME_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # éè®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_anime_{style}_{timestamp}.png")

            logger.info(f"å¨æ¼«é£æ ¼: {style}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",   # æåäººä½éª¨æ¶
                controlnet_model="openpose",    # å¼ºå¶éæ­äººä½å¿æE¼é²æ­¢åå½¢
                strength=strength,              # è¾E«çéçå¹Eº¦Eå®æEçé£è½¬åE
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
                    "controlnet": "openpose"
                }
            }

        except Exception as e:
            logger.error(f"æè¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<RealToAnime(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="çäººè½¬å¨æ¼«å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--style", "-s", default="modern",
                        choices=list(ANIME_STYLES.keys()), help="å¨æ¼«é£æ ¼")
    parser.add_argument("--prompt", "-p", help="èªå®ä¹æç¤ºè¯E)
    parser.add_argument("--strength", type=float, default=0.8, help="éçå¼ºåº¦")
    parser.add_argument("--steps", type=int, default=35, help="è¿­ä£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºçå­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = RealToAnime(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        style=args.style, prompt=args.prompt,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))