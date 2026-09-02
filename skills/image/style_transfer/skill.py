# skills/style_transfer/skill.py
"""
é£æ ¼è½¬æ¢ Skill - å°E¾çE½¬æ¢ä¸ºæE®é£æ ¼Eæ²¹ç»/æ°´å½©/å¨æ¼«/ç´ æç­ï¼E
å¤ç¨éç¨ ControlNet å¼æEEED + Lineart éæ­»æE¾Eé«å¹Eº¦éæç»é¢è´¨æï¼E
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

# é£æ ¼é¢E®¾
STYLE_PRESETS = {
    "oil_painting": {
        "prompt": "oil painting, thick brushstrokes, canvas texture, masterpiece, van gogh style, rich colors, artistic, high quality",
        "negative": "photorealistic, 3d render, digital art, smooth, cartoon, anime"
    },
    "watercolor": {
        "prompt": "watercolor painting, soft wash, paper texture, flowing colors, transparent, artistic, masterpiece, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges, oil painting"
    },
    "anime": {
        "prompt": "anime style, cel shading, vibrant colors, anime art, masterpiece, best quality, 2d illustration, manga style",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "sketch": {
        "prompt": "pencil sketch, graphite drawing, fine lines, cross-hatching, monochrome, black and white, masterpiece, high quality",
        "negative": "photorealistic, color, 3d render, smooth, oil painting"
    },
    "impressionist": {
        "prompt": "impressionist painting, soft brushstrokes, vibrant colors, light effects, masterpiece, claude monet style, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges"
    },
    "pixel_art": {
        "prompt": "pixel art, retro game style, 8-bit, blocky, colorful, masterpiece, high quality",
        "negative": "photorealistic, 3d render, smooth, blurry, oil painting"
    },
    "cyberpunk": {
        "prompt": "cyberpunk style, neon colors, futuristic, glowing lights, dark atmosphere, sci-fi, masterpiece, high quality",
        "negative": "photorealistic, 3d render, ugly, deformed, blurry"
    },
    "vintage": {
        "prompt": "vintage photo style, retro, film grain, warm tones, nostalgic, old photo, masterpiece, high quality",
        "negative": "digital art, 3d render, photorealistic, ugly, deformed"
    }
}


class StyleTransfer:
    """é£æ ¼è½¬æ¢æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "style_transfer"
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

        logger.info(f"StyleTransfer v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  é¢E®¾é£æ ¼: {len(STYLE_PRESETS)} ç§E)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.75,  # é£æ ¼è½¬æ¢éè¦E«å¼ºåº¦éç»æ¥éæ¾è´¨æE
            'default_style': 'oil_painting',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(STYLE_PRESETS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æ§è¡é£æ ¼è½¬æ¢"""
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

            style = kwargs.get('style', self.config.get('default_style', 'oil_painting'))
            if style not in STYLE_PRESETS:
                return {"status": "error", "error": f"æªç¥é£æ ¼: {style}Eå¯ç¨: {list(STYLE_PRESETS.keys())}"}

            style_config = STYLE_PRESETS[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.75))
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

            logger.info(f"é£æ ¼: {style}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            # ä½¿ç¨ HED æåè½¯è¾¹ç¼ï¼éEåELineart æ¨¡åéæ­»æE¾
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",
                controlnet_model="lineart",
                strength=strength,
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
        return f"<StyleTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="é£æ ¼è½¬æ¢å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--style", "-s", default="oil_painting",
                        choices=list(STYLE_PRESETS.keys()), help="é£æ ¼")
    parser.add_argument("--strength", type=float, default=0.75, help="éç»å¼ºåº¦")
    parser.add_argument("--steps", type=int, default=30, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = StyleTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))