# skills/nude_oil_painting/skill.py
"""
陬ｸ菴捺ｲｹ逕ｻ - 荳髞ｮ逕滓・蜿､蜈ｸ/蜀吝ｮ樊ｲｹ逕ｻ鬟取ｼ陬ｸ菴謎ｺｺ蜒・
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
    "classical": "classical oil painting, Renaissance style, soft chiaroscuro, warm earth tones, masterpiece, high quality",
    "baroque": "Baroque oil painting, dramatic lighting, rich colors, tenebrism, masterpiece, high quality",
    "impressionist": "Impressionist oil painting, visible brushstrokes, soft colors, light and atmosphere, masterpiece, high quality",
    "realistic": "photorealistic oil painting, ultra detailed, smooth blending, lifelike skin texture, masterpiece, high quality",
    "romantic": "Romantic oil painting, emotional, dramatic, soft glow, poetic atmosphere, masterpiece, high quality",
    "modern": "modern oil painting, abstract expressionism, bold colors, contemporary style, masterpiece, high quality",
}

POSE_MAP = {
    "standing": "standing upright, classical contrapposto, arms relaxed, masterpiece",
    "reclining": "reclining on couch, elegant pose, one arm supporting head, masterpiece",
    "sitting": "sitting on chair, graceful posture, hands on lap, masterpiece",
    "kneeling": "kneeling on floor, looking up, devotional pose, masterpiece",
    "lying": "lying down, relaxed, peaceful expression, masterpiece",
}

LIGHTING_MAP = {
    "studio": "studio lighting, soft shadows, even illumination, high quality",
    "dramatic": "dramatic chiaroscuro, strong contrasts, deep shadows, cinematic",
    "warm": "warm golden lighting, sunset glow, intimate atmosphere, beautiful",
    "cool": "cool blue lighting, moonlight, ethereal atmosphere, mystical",
}


class NudeOilPainting:
    """陬ｸ菴捺ｲｹ逕ｻ謚閭ｽ"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "nude_oil_painting"
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

        logger.info(f"NudeOilPainting v{self.version} 蛻晏ｧ句喧螳梧・")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.65,
            'default_style': 'classical',
            'default_pose': 'standing',
            'default_lighting': 'studio',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime, digital art, 3d render, plastic',
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

            style = kwargs.get('style', self.config.get('default_style', 'classical'))
            pose = kwargs.get('pose', self.config.get('default_pose', 'standing'))
            lighting = kwargs.get('lighting', self.config.get('default_lighting', 'studio'))

            if style not in STYLE_MAP:
                return {"status": "error", "error": f"譛ｪ遏･鬟取ｼ: {style}・悟庄逕ｨ: {list(STYLE_MAP.keys())}"}
            if pose not in POSE_MAP:
                return {"status": "error", "error": f"譛ｪ遏･蟋ｿ諤・ {pose}・悟庄逕ｨ: {list(POSE_MAP.keys())}"}
            if lighting not in LIGHTING_MAP:
                return {"status": "error", "error": f"譛ｪ遏･轣ｯ蜈・ {lighting}・悟庄逕ｨ: {list(LIGHTING_MAP.keys())}"}

            prompt = f"1girl, full body, beautiful face, perfect body, large bust, hourglass figure, nude, naked, oil painting, canvas texture, {STYLE_MAP[style]}, {POSE_MAP[pose]}, {LIGHTING_MAP[lighting]}, artistic, fine art, high quality, masterpiece"

            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.65))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 蠑墓梼荳榊庄逕ｨ"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_oil_{style}_{pose}_{timestamp}.png")

            logger.info(f"鬟取ｼ: {style}, 蟋ｿ諤・ {pose}, 轣ｯ蜈・ {lighting}")
            logger.info(f"謠千､ｺ隸・ {prompt[:100]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                controlnet_type="openpose",
                controlnet_strength=1.0,
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
                "pose": pose,
                "lighting": lighting,
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
        return f"<NudeOilPainting(name={self.name}, version={self.version})>"