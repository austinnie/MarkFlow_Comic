# skills/intimate_closeup/skill.py
"""
遘∝､・音蜀・- 荳髞ｮ逕滓・蜚ｯ鄒守ｧ∝､・音蜀・
"""

import time
import os
import sys
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
except ImportError:
    torch = None

try:
    from skills.image.controlnet_img2img.skill import ControlnetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")

STYLE_MAP = {
    "artistic": "artistic nude photography, fine art, soft focus, elegant composition, tasteful, masterpiece",
    "natural": "natural lighting, soft shadows, intimate atmosphere, warm tones, beautiful skin texture, masterpiece",
    "romantic": "romantic mood, soft glow, gentle lighting, intimate, sensual, beautiful, masterpiece",
    "vintage": "vintage style, soft grain, warm sepia tones, classic nude photography, timeless, masterpiece",
    "ethereal": "ethereal glow, dreamy atmosphere, soft light, delicate, beautiful, masterpiece",
}

BACKGROUND_MAP = {
    "soft": "soft blurred background, gentle bokeh, intimate setting, cozy atmosphere",
    "dark": "dark background, dramatic contrast, moody, sensual, artistic",
    "warm": "warm ambient light, cozy bedroom, golden tones, romantic atmosphere",
    "nature": "nature setting, soft greenery, dappled light, organic, peaceful",
    "studio": "clean studio background, professional lighting, elegant, refined",
}


class IntimateCloseup:
    """遘∝､・音蜀呎橿閭ｽ"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "intimate_closeup"
        self.version = "1.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.device = self.config.get('device', 'cuda' if torch and torch.cuda.is_available() else 'cpu')

        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlnetImg2Img(config={'device': self.device})
                logger.info("  笨・ControlNet 蠑墓梼蛻晏ｧ句喧謌仙粥")
            except Exception as e:
                logger.warning(f"  蠑墓梼蛻晏ｧ句喧螟ｱ雍･: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"IntimateCloseup v{self.version} 蛻晏ｧ句喧螳梧・")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.6,
            'default_style': 'artistic',
            'default_background': 'soft',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, explicit, pornographic, vulgar, extreme closeup, gore, blood, injury, medical, surgery, disease, infection, shaved, completely bald',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name}")

        try:
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 譏ｯ蠢・｡ｫ蜿よ焚"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}"}

            style = kwargs.get('style', self.config.get('default_style', 'artistic'))
            background = kwargs.get('background', self.config.get('default_background', 'soft'))

            if style not in STYLE_MAP:
                return {"status": "error", "error": f"譛ｪ遏･鬟取ｼ: {style}・悟庄逕ｨ: {list(STYLE_MAP.keys())}"}
            if background not in BACKGROUND_MAP:
                return {"status": "error", "error": f"譛ｪ遏･閭梧勹: {background}・悟庄逕ｨ: {list(BACKGROUND_MAP.keys())}"}

            prompt = f"close-up of a woman's intimate area, lower body, delicate skin, feminine beauty, {STYLE_MAP[style]}, {BACKGROUND_MAP[background]}, high quality, 8k, fine art photography"

            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.6))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 蠑墓梼荳榊庄逕ｨ"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_intimate_{style}_{background}_{timestamp}.png")

            logger.info(f"鬟取ｼ: {style}, 閭梧勹: {background}")
            logger.info(f"謠千､ｺ隸・ {prompt[:100]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                controlnet_type="openpose",
                controlnet_strength=0.8,
                strength=strength,
                steps=steps,
                seed=seed,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('output_path', output_path),
                "style": style,
                "background": background,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                }
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<IntimateCloseup(name={self.name}, version={self.version})>"