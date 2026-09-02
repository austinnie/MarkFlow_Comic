# skills/real_to_anime/skill.py
"""
çäººè½¬å¨æ¼« Skill - å°Eå®çEçE½¬æ¢ä¸ºå¨æ¼«é£æ ¼
å¤ç¨éç¨ ControlNet å¼æEEpenPoseä¿æå§¿æE¼é«å¹Eº¦éç»è½¬é£æ ¼EE
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

# å¨æ¼«é£æ ¼é¢E®¾
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
    """çäººè½¬å¨æ¼«æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "real_to_anime"
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

        logger.info(f"RealToAnime v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  å¨æ¼«é£æ ¼: {len(ANIME_STYLES)} ç§E)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 35,
            'default_strength': 0.8, # è½¬å¨æ¼«éè¦è¾E«çéç»å¹Eº¦æ¥æ¹åç»é£E
            'default_style': 'modern',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(ANIME_STYLES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æ§è¡çäººè½¬å¨æ¼«"""
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

            style = kwargs.get('style', self.config.get('default_style', 'modern'))
            if style not in ANIME_STYLES:
                return {"status": "error", "error": f"æªç¥é£æ ¼: {style}Eå¯ç¨: {list(ANIME_STYLES.keys())}"}

            style_config = ANIME_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # é»è®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_anime_{style}_{timestamp}.png")

            logger.info(f"å¨æ¼«é£æ ¼: {style}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",   # æåäººä½éª¨æ¶
                controlnet_model="openpose",    # å¼ºå¶éæ­»äººä½å§¿æE¼é²æ­¢åå½¢
                strength=strength,              # è¾E«çéç»å¹Eº¦Eå®æEç»é£è½¬åE
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
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<RealToAnime(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="çäººè½¬å¨æ¼«å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--style", "-s", default="modern",
                        choices=list(ANIME_STYLES.keys()), help="å¨æ¼«é£æ ¼")
    parser.add_argument("--prompt", "-p", help="èªå®ä¹æç¤ºè¯E)
    parser.add_argument("--strength", type=float, default=0.8, help="éç»å¼ºåº¦")
    parser.add_argument("--steps", type=int, default=35, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = RealToAnime(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        style=args.style, prompt=args.prompt,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))