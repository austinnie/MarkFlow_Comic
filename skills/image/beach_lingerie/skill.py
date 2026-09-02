# skills/beach_lingerie/skill.py
"""
豬ｷ貊ｩ蜚ｯ鄒主・陦｣ - 荳髞ｮ逕滓・
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

OUTFIT_MAP = {
    "white_lace": "white lace lingerie, delicate lace, elegant, beautiful, masterpiece",
    "black_silk": "black silk lingerie, glossy silk, sophisticated, seductive, masterpiece",
    "pink_satin": "pink satin lingerie, soft satin, romantic, cute, masterpiece",
    "red_velvet": "red velvet lingerie, luxurious velvet, passionate, bold, masterpiece",
    "blue_lace": "blue lace lingerie, delicate lace, elegant, beautiful, masterpiece",
}

POSE_MAP = {
    "standing": "standing on sandy beach, full body, confident pose, hands on hips, masterpiece",
    "walking": "walking on beach, dynamic motion, one foot raised, elegant stride, masterpiece",
    "sitting": "sitting on beach towel, relaxed posture, looking at viewer, masterpiece",
}


class BeachLingerie:
    """豬ｷ貊ｩ蜚ｯ鄒主・陦｣謚閭ｽ"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "beach_lingerie"
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

        logger.info(f"BeachLingerie v{self.version} 蛻晏ｧ句喧螳梧・")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_outfit': 'white_lace',
            'default_pose': 'standing',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality',
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

            outfit = kwargs.get('outfit', self.config.get('default_outfit', 'white_lace'))
            pose = kwargs.get('pose', self.config.get('default_pose', 'standing'))

            if outfit not in OUTFIT_MAP:
                return {"status": "error", "error": f"譛ｪ遏･蜀・｡｣鬟取ｼ: {outfit}・悟庄逕ｨ: {list(OUTFIT_MAP.keys())}"}
            if pose not in POSE_MAP:
                return {"status": "error", "error": f"譛ｪ遏･蟋ｿ諤・ {pose}・悟庄逕ｨ: {list(POSE_MAP.keys())}"}

            base_prompt = "1girl, full body, facing viewer, beautiful face, perfect body, large bust, hourglass figure, "

            if pose == "standing":
                base_prompt += "standing on a beautiful sandy beach, ocean waves in background, confident posture, hands on hips, "
            elif pose == "walking":
                base_prompt += "walking along the beach, dynamic motion, ocean in background, elegant stride, "
            elif pose == "sitting":
                base_prompt += "sitting on a beach towel on the sand, relaxed posture, ocean view, "

            prompt = base_prompt + OUTFIT_MAP[outfit] + ", beach background, sunny day, golden sunlight, high quality, masterpiece, 8k, photorealistic"

            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 蠑墓梼荳榊庄逕ｨ"}

            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_beach_{outfit}_{pose}_{timestamp}.png")

            logger.info(f"蜀・｡｣鬟取ｼ: {outfit}, 蟋ｿ諤・ {pose}")
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
                "outfit": outfit,
                "pose": pose,
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
        return f"<BeachLingerie(name={self.name}, version={self.version})>"