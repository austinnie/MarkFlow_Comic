# skills/day_night_transfer/skill.py
"""
æ¼å¤è½¬æ¢ Skill - å°E¾çEç½å¤©è½¬ä¸ºå¤ææåä¹E
å¤ç¨éç¨ ControlNet å¼æEELSD + Depth éç©ºé´å ä½ï¼å®æEåæ¯è½¬æ¢EE
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

TIME_MODES = {
    "day": {
        "prompt": "bright sunny day, natural sunlight, clear sky, vibrant, masterpiece, high quality",
        "negative": "night, dark, moonlight, stars, dim"
    },
    "night": {
        "prompt": "night scene, moonlight, stars, dark sky, soft lighting, mysterious, masterpiece, high quality",
        "negative": "day, sunlight, bright, sunny, daylight"
    },
    "sunset": {
        "prompt": "sunset, golden hour, warm orange sky, beautiful sunset, masterpiece, high quality",
        "negative": "night, dark, harsh sunlight"
    },
    "dawn": {
        "prompt": "dawn, early morning, soft light, sunrise, misty, peaceful, masterpiece, high quality",
        "negative": "night, harsh light, sunset"
    }
}


class DayNightTransfer:
    """æ¼å¤è½¬æ¢æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "day_night_transfer"
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

        logger.info(f"DayNightTransfer v{self.version} åååå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  æ¨¡å¼E {list(TIME_MODES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_mode': 'night',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_modes(self) -> Dict[str, Any]:
        return {"status": "success", "modes": list(TIME_MODES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
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

            mode = kwargs.get('mode', self.config.get('default_mode', 'night'))
            if mode not in TIME_MODES:
                return {"status": "error", "error": f"æªç¥æ¨¡å¼E {mode}Eå¯ç¨: {list(TIME_MODES.keys())}"}

            mode_config = TIME_MODES[mode]
            prompt = kwargs.get('prompt') or mode_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or mode_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # éè®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{mode}_{timestamp}.png")

            logger.info(f"æ¨¡å¼E {mode}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            # ä½¿ç¨ MLSD æåå ä½çº¿æ¡ + åºå±EDepth æ¨¡åï¼å®ç¾ä¿æåºæ¯ç©ºé´çæ
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="MLSD",      # æååºç­Eæ¯ç©ç´çº¿
                controlnet_model="depth",      # ä½¿ç¨æ·±åº¦æ¨¡åéæ­ç©ºé´å³ç³
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "mode": mode,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "depth"
                }
            }

        except Exception as e:
            logger.error(f"æè¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<DayNightTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="æ¼å¤è½¬æ¢å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--mode", "-m", default="night",
                        choices=list(TIME_MODES.keys()), help="æ¨¡å¼E)
    parser.add_argument("--strength", type=float, default=0.7, help="éçå¼ºåº¦")
    parser.add_argument("--steps", type=int, default=30, help="è¿­ä£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºçå­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = DayNightTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        mode=args.mode,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))