# skills/weather_transfer/skill.py
"""
å¤©æ°è½¬æ¢ Skill - å°E¾çE½¬æ¢ä¸ºä¸åå¤©æ°E(æ´/é¨/éª/é¾)
å¤ç¨éç¨ ControlNet å¼æEELSD + Depth éç©ºé´ç»æEè½¬æ¢å¤©æ°æ°å´EE
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

WEATHERS = {
    "sunny": {
        "prompt": "bright sunny day, clear sky, warm sunlight, beautiful weather, masterpiece, high quality",
        "negative": "rain, snow, fog, dark, cloudy"
    },
    "rainy": {
        "prompt": "rainy day, rain drops, wet ground, cloudy sky, peaceful, atmosphere, masterpiece, high quality",
        "negative": "sunny, snow, clear sky, dry"
    },
    "snowy": {
        "prompt": "snowy day, snow falling, white landscape, cold, beautiful winter, masterpiece, high quality",
        "negative": "rain, sunny, green, warm"
    },
    "foggy": {
        "prompt": "foggy day, mist, soft atmosphere, mysterious, ethereal, masterpiece, high quality",
        "negative": "sunny, clear sky, bright"
    },
    "stormy": {
        "prompt": "stormy weather, dark clouds, lightning, dramatic, atmospheric, masterpiece, high quality",
        "negative": "sunny, clear sky, calm"
    },
    "cloudy": {
        "prompt": "cloudy day, overcast sky, soft light, peaceful, atmosphere, masterpiece, high quality",
        "negative": "sunny, clear sky, rain"
    }
}


class WeatherTransfer:
    """å¤©æ°è½¬æ¢æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "weather_transfer"
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

        logger.info(f"WeatherTransfer v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  å¤©æ°E {list(WEATHERS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_weather': 'sunny',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_weathers(self) -> Dict[str, Any]:
        return {"status": "success", "weathers": list(WEATHERS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
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

            weather = kwargs.get('weather', self.config.get('default_weather', 'sunny'))
            if weather not in WEATHERS:
                return {"status": "error", "error": f"æªç¥å¤©æ°E {weather}Eå¯ç¨: {list(WEATHERS.keys())}"}

            weather_config = WEATHERS[weather]
            prompt = kwargs.get('prompt') or weather_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or weather_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # é»è®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{weather}_{timestamp}.png")

            logger.info(f"å¤©æ°E {weather}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            # ä½¿ç¨ MLSDEæååºæ¯ç´çº¿EE DepthEéç©ºé´æ·±åº¦Eï¼è½¬æ¢å¤©æ°E
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="MLSD",
                controlnet_model="depth",
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "weather": weather,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "depth"
                }
            }

        except Exception as e:
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<WeatherTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="å¤©æ°è½¬æ¢å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--weather", "-w", default="sunny",
                        choices=list(WEATHERS.keys()), help="å¤©æ°E)
    parser.add_argument("--strength", type=float, default=0.7, help="éç»å¼ºåº¦")
    parser.add_argument("--steps", type=int, default=30, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = WeatherTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        weather=args.weather,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))