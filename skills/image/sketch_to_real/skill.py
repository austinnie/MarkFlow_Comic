# skills/sketch_to_real/skill.py
"""
ç´ æè½¬çäºº Skill - å°E´ æEçº¿ç¨¿è½¬æ¢ä¸ºçäººç§çE
ä½¿ç¨ Lineart ControlNet ä¿æçº¿æ¡ç»æ
"""

import os
import sys
import json
import time
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

# ==================== å¼åEçæ­£çEºå±å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# ==================== é£æ ¼éç½® ====================
REALISM_STYLES = {
    "realistic": {
        "prompt": "photorealistic, real person, realistic skin texture, natural lighting, detailed, masterpiece, high quality, 8k",
        "negative": "anime, cartoon, 2d, illustration, drawing, painting, sketch"
    },
    "cinematic": {
        "prompt": "cinematic photography, real person, movie still, dramatic lighting, detailed, masterpiece, high quality, 8k",
        "negative": "anime, cartoon, 2d, illustration, drawing, sketch"
    },
    "portrait": {
        "prompt": "professional portrait photography, real person, studio lighting, beautiful, detailed, masterpiece, high quality",
        "negative": "anime, cartoon, 2d, illustration, drawing, sketch"
    },
    "artistic": {
        "prompt": "artistic photography, real person, creative lighting, beautiful, masterpiece, high quality",
        "negative": "anime, cartoon, 2d, illustration, drawing, sketch"
    }
}

# ==================== å¯ç¨æ¨¡ååEè¡¨ ====================
AVAILABLE_MODELS = {
    "anytimeRealistic_v10.safetensors": {
        "name": "Anytime Realistic",
        "size": "2.13 GB",
        "type": "åå®E,
        "description": "éç¨åå®é£æ ¼Eæ¨èE
    },
    "asianrealisticSdlife_v40.safetensors": {
        "name": "Asian Realistic SDLife",
        "size": "3.29 GB",
        "type": "äºæ´²åå®E,
        "description": "äºæ´²äººååEå®E
    },
    "DreamShaper_8_pruned.safetensors": {
        "name": "DreamShaper 8",
        "size": "2.13 GB",
        "type": "èºæ¯",
        "description": "æ¢¦å¹»/èºæ¯é£æ ¼"
    },
    "nextphoto_v30.safetensors": {
        "name": "Next Photo v3.0",
        "size": "2.13 GB",
        "type": "æE½±",
        "description": "çå®æå½±é£æ ¼"
    }
}


class SketchToReal:
    """ç´ æè½¬çäººæè½Eçº¯ ControlNetEæ é InpaintEE""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "sketch_to_real"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cpu')

        # é»è®¤åæ°
        self.default_model = self.config.get('default_model', 'anytimeRealistic_v10.safetensors')
        self.default_steps = self.config.get('default_steps', 35)
        self.default_strength = self.config.get('default_strength', 0.85)
        self.default_style = self.config.get('default_style', 'realistic')
        self.default_negative = self.config.get('default_negative', 'ugly, deformed, blurry, low quality, sketch, drawing, lineart, 2d')

        # ç¼å­E
        self.controlnet_engine = None

        # ==================== åå§ååºå±å¼æ ====================
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"SketchToReal v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  é»è®¤æ¨¡åE {self.default_model}")
        logger.info(f"  é£æ ¼: {list(REALISM_STYLES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'default_model': 'anytimeRealistic_v10.safetensors',
            'default_steps': 35,
            'default_strength': 0.85,
            'default_style': 'realistic',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        Path(self.config.get('output_dir', str(self.output_dir))).mkdir(parents=True, exist_ok=True)

    def _find_model(self, model_name: str) -> Optional[Path]:
        """æ¥æ¾æ¨¡åæä»¶"""
        if not model_name:
            model_name = self.default_model

        direct_path = self.models_dir / model_name
        if direct_path.exists():
            return direct_path

        filename = os.path.basename(model_name)
        for subdir in ['sd-v1-5', 'sdxl']:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                return sub_path

        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    return file_path

        logger.error(f"æªæ¾å°æ¨¡åE {model_name}")
        return None

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(REALISM_STYLES.keys())}

    def list_models(self) -> Dict[str, Any]:
        """ååEææå¯ç¨æ¨¡åE""
        models = {}
        for key, info in AVAILABLE_MODELS.items():
            models[key] = {
                "name": info["name"],
                "size": info["size"],
                "type": info["type"],
                "description": info["description"],
            }
        return {
            "status": "success",
            "models": models,
            "count": len(models),
            "default": self.default_model,
            "timestamp": datetime.now().isoformat()
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"æ§è¡æè½: {self.name} v{self.version}")

        try:
            # ==================== 1. ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path') or kwargs.get('input')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            output_path = kwargs.get('output_path') or kwargs.get('output')

            # æç¤ºè¯ä¸é£æ ¼éç½®
            style = kwargs.get('style', self.default_style)
            if style not in REALISM_STYLES:
                return {"status": "error", "error": f"æªç¥é£æ ¼: {style}Eå¯ç¨: {list(REALISM_STYLES.keys())}"}

            s_config = REALISM_STYLES[style]
            prompt = kwargs.get('prompt') or s_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or s_config.get('negative', self.default_negative)

            # ==================== 2. ç´æ¥è°E¨åºå±EControlNet å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            logger.info(f"é£æ ¼: {style}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            # å¦ææ²¡ä¼  output_pathEé»è®¤å­å°æ¬æè½çEoutput ç®å½E
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_sketch2real_{style}_{timestamp}.png")

            # æ ¸å¿E»è¾ï¼ä¼ å¥ HED (æåçº¿ç¨¿) + Lineart åºå±æ¨¡åE
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),  # ç»å¯¹è·¯å¾E
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",               # æåçº¿ç¨¿
                controlnet_model="lineart",            # å¼ºå¶ä½¿ç¨æ¬å° lineart æ¨¡åï¼ä½ æ¬å°çEmodels--lllyasviel--control_v11p_sd15_lineartEE
                strength=0.85,                         # é«å¼ºåº¦éç»ï¼è®©çº¿ç¨¿åçäºº
                output_path=output_path                # å¼ºå¶æE®è¾åE
            )

            # æ£æ¥å¼æè¿åç»æ
            if result['status'] == 'success':
                return {
                    "status": "success",
                    "output_path": result.get('image_path', output_path),
                    "style": style,
                    "generation_time": f"{time.time() - start_time:.2f}s",
                    "parameters": {
                        "steps": kwargs.get('steps', self.default_steps),
                        "seed": kwargs.get('seed', -1),
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "controlnet": "lineart"
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # å¼ææ¥éï¼ç´æ¥æå¼æçEè¯¯åæ ·æåE
                return {"status": "error", "error": result.get('error', 'åºå±å¼æè°E¨å¤±è´¥')}

        except Exception as e:
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<SketchToReal(name={self.name}, version={self.version})>"


# ==================== å½ä»¤è¡åEå£ ====================
if __name__ == "__main__":
    import argparse

    MODEL_CHOICES = list(AVAILABLE_MODELS.keys())

    parser = argparse.ArgumentParser(description="ç´ æè½¬çäººå·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEç´ æEçº¿ç¨¿å¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--model", "-m", default="anytimeRealistic_v10.safetensors",
                        choices=MODEL_CHOICES, help="SD æ¨¡ååç§°")
    parser.add_argument("--style", "-s", default="realistic",
                        choices=list(REALISM_STYLES.keys()), help="çäººé£æ ¼")
    parser.add_argument("--prompt", "-p", help="èªå®ä¹æç¤ºè¯ï¼è¦Eé£æ ¼é»è®¤EE)
    parser.add_argument("--negative", "-n", help="èªå®ä¹è´é¢æç¤ºè¯ï¼è¦Eé£æ ¼é»è®¤EE)
    parser.add_argument("--steps", type=int, default=35, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="è®¾å¤E)
    parser.add_argument("--list-models", action="store_true", help="ååEææå¯ç¨æ¨¡åE)
    parser.add_argument("--list-styles", action="store_true", help="ååEææå¯ç¨é£æ ¼")

    args = parser.parse_args()

    # å¦æåªæ¯ååEæ¨¡åE
    if args.list_models:
        skill = SketchToReal()
        result = skill.list_models()
        print("\n" + "=" * 60)
        print("  å¯ç¨æ¨¡ååEè¡¨")
        print("=" * 60)
        for key, info in result['models'].items():
            default_mark = " â­E(é»è®¤)" if key == result['default'] else ""
            print(f"  {key}")
            print(f"    åç§°: {info['name']}{default_mark}")
            print(f"    å¤§å°E {info['size']}")
            print(f"    ç±»åE {info['type']}")
            print(f"    è¯´æE {info['description']}")
            print()
        print(f"  å± {result['count']} ä¸ªæ¨¡åE)
        print("=" * 60)
        sys.exit(0)

    # å¦æåªæ¯ååEé£æ ¼
    if args.list_styles:
        print("\n" + "=" * 60)
        print("  å¯ç¨é£æ ¼åè¡¨")
        print("=" * 60)
        for key, info in REALISM_STYLES.items():
            print(f"  {key}")
            print(f"    æç¤ºè¯E {info['prompt'][:60]}...")
            print(f"    è´é¢: {info['negative'][:60]}...")
            print()
        print(f"  å± {len(REALISM_STYLES)} ç§é£æ ¼")
        print("=" * 60)
        sys.exit(0)

    skill = SketchToReal(config={
        'device': args.device,
        'default_model': args.model,
        'default_steps': args.steps,
        'default_style': args.style,
    })

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        model_name=args.model,
        style=args.style,
        prompt=args.prompt,
        negative_prompt=args.negative,
        steps=args.steps,
        seed=args.seed,
    )

    if result['status'] == 'success':
        print(f"\nâEæå!")
        print(f"  ð è¾åE: {result['output_path']}")
        print(f"  ð¨ é£æ ¼: {result['style']}")
        print(f"  â±EE èæ¶: {result['generation_time']}")
        print(f"  ð åæ°:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\nâEå¤±è´¥: {result.get('error', 'æªç¥éè¯¯')}")