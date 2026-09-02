# skills/sketch_to_real/skill.py
"""
ç´ æè½¬çäºº Skill - å°E´ æEçº¿ç¨¿è½¬æ¢ä¸ºçäººç§çE
ä½¿ç¨ Lineart ControlNet ä¿æçº¿æ¡ç»æ
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
    logger.warning("torch æEPIL æªå®è£E)

# ==================== å¼åEçæ­£çEºå±å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# ==================== é£æ ¼éç½® ====================
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

# ==================== å¯ç¨æ¨¡ååEè¡¨ ====================
AVAILABLE_MODELS = {
    "anytimeRealistic_v10.safetensors": {
        "name": "Anytime Realistic",
        "size": "2.13 GB",
        "type": "åå®E,
        "description": "éç¨åå®é£æ ¼Eæ¨èE
    },
    "asianrealisticSdlife_v40.safetensors": {
        "name": "Asian Realistic SDLife",
        "size": "3.29 GB",
        "type": "äºæ´²åå®E,
        "description": "äºæ´²äººååEå®E
    },
    "DreamShaper_8_pruned.safetensors": {
        "name": "DreamShaper 8",
        "size": "2.13 GB",
        "type": "èºæ¯",
        "description": "æ¢¦å¹»/èºæ¯é£æ ¼"
    },
    "nextphoto_v30.safetensors": {
        "name": "Next Photo v3.0",
        "size": "2.13 GB",
        "type": "æE½±",
        "description": "çå®æå½±é£æ ¼"
    }
}


class SketchToReal:
    """ç´ æè½¬çäººæè½Eçº¯ ControlNetEæ é InpaintEE""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "sketch_to_real"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cpu')

        # é»è®¤åæ°
        self.default_model = self.config.get('default_model', 'anytimeRealistic_v10.safetensors')
        self.default_steps = self.config.get('default_steps', 35)
        self.default_strength = self.config.get('default_strength', 0.85)
        self.default_style = self.config.get('default_style', 'realistic')
        self.default_negative = self.config.get('default_negative', 'ugly, deformed, blurry, low quality, sketch, drawing, lineart, 2d')

        # ç¼å­E
        self.controlnet_engine = None

        # ==================== åå§ååºå±å¼æ ====================
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"SketchToReal v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  é»è®¤æ¨¡åE {self.default_model}")
        logger.info(f"  é£æ ¼: {list(REALISM_STYLES.keys())}")

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
        """æ¥æ¾æ¨¡åæä»¶"""
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

        logger.error(f"æªæ¾å°æ¨¡åE {model_name}")
        return None

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(REALISM_STYLES.keys())}

    def list_models(self) -> Dict[str, Any]:
        """ååEææå¯ç¨æ¨¡åE""
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
        logger.info(f"æ§è¡æè½: {self.name} v{self.version}")

        try:
            # ==================== 1. ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path') or kwargs.get('input')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            output_path = kwargs.get('output_path') or kwargs.get('output')

            # æç¤ºè¯ä¸é£æ ¼éç½®
            style = kwargs.get('style', self.default_style)
            if style not in REALISM_STYLES:
                return {"status": "error", "error": f"æªç¥é£æ ¼: {style}Eå¯ç¨: {list(REALISM_STYLES.keys())}"}

            s_config = REALISM_STYLES[style]
            prompt = kwargs.get('prompt') or s_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or s_config.get('negative', self.default_negative)

            # ==================== 2. ç´æ¥è°E¨åºå±EControlNet å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            logger.info(f"é£æ ¼: {style}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            # å¦ææ²¡ä¼  output_pathEé»è®¤å­å°æ¬æè½çEoutput ç®å½E
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_sketch2real_{style}_{timestamp}.png")

            # æ ¸å¿E»è¾ï¼ä¼ å¥ HED (æåçº¿ç¨¿) + Lineart åºå±æ¨¡åE
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),  # ç»å¯¹è·¯å¾E
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",               # æåçº¿ç¨¿
                controlnet_model="lineart",            # å¼ºå¶ä½¿ç¨æ¬å° lineart æ¨¡åï¼ä½ æ¬å°çEmodels--lllyasviel--control_v11p_sd15_lineartEE
                strength=0.85,                         # é«å¼ºåº¦éç»ï¼è®©çº¿ç¨¿åçäºº
                output_path=output_path                # å¼ºå¶æE®è¾åE
            )

            # æ£æ¥å¼æè¿åç»æ
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
                # å¼ææ¥éï¼ç´æ¥æå¼æçEè¯¯åæ ·æåE
                return {"status": "error", "error": result.get('error', 'åºå±å¼æè°E¨å¤±è´¥')}

        except Exception as e:
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<SketchToReal(name={self.name}, version={self.version})>"


# ==================== å½ä»¤è¡åEå£ ====================
if __name__ == "__main__":
    import argparse

    MODEL_CHOICES = list(AVAILABLE_MODELS.keys())

    parser = argparse.ArgumentParser(description="ç´ æè½¬çäººå·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEç´ æEçº¿ç¨¿å¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--model", "-m", default="anytimeRealistic_v10.safetensors",
                        choices=MODEL_CHOICES, help="SD æ¨¡ååç§°")
    parser.add_argument("--style", "-s", default="realistic",
                        choices=list(REALISM_STYLES.keys()), help="çäººé£æ ¼")
    parser.add_argument("--prompt", "-p", help="èªå®ä¹æç¤ºè¯ï¼è¦Eé£æ ¼é»è®¤EE)
    parser.add_argument("--negative", "-n", help="èªå®ä¹è´é¢æç¤ºè¯ï¼è¦Eé£æ ¼é»è®¤EE)
    parser.add_argument("--steps", type=int, default=35, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="è®¾å¤E)
    parser.add_argument("--list-models", action="store_true", help="ååEææå¯ç¨æ¨¡åE)
    parser.add_argument("--list-styles", action="store_true", help="ååEææå¯ç¨é£æ ¼")

    args = parser.parse_args()

    # å¦æåªæ¯ååEæ¨¡åE
    if args.list_models:
        skill = SketchToReal()
        result = skill.list_models()
        print("\n" + "=" * 60)
        print("  å¯ç¨æ¨¡ååEè¡¨")
        print("=" * 60)
        for key, info in result['models'].items():
            default_mark = " â­E(é»è®¤)" if key == result['default'] else ""
            print(f"  {key}")
            print(f"    åç§°: {info['name']}{default_mark}")
            print(f"    å¤§å°E {info['size']}")
            print(f"    ç±»åE {info['type']}")
            print(f"    è¯´æE {info['description']}")
            print()
        print(f"  å± {result['count']} ä¸ªæ¨¡åE)
        print("=" * 60)
        sys.exit(0)

    # å¦æåªæ¯ååEé£æ ¼
    if args.list_styles:
        print("\n" + "=" * 60)
        print("  å¯ç¨é£æ ¼åè¡¨")
        print("=" * 60)
        for key, info in REALISM_STYLES.items():
            print(f"  {key}")
            print(f"    æç¤ºè¯E {info['prompt'][:60]}...")
            print(f"    è´é¢: {info['negative'][:60]}...")
            print()
        print(f"  å± {len(REALISM_STYLES)} ç§é£æ ¼")
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
        print(f"\nâEæå!")
        print(f"  ð è¾åE: {result['output_path']}")
        print(f"  ð¨ é£æ ¼: {result['style']}")
        print(f"  â±EE èæ¶: {result['generation_time']}")
        print(f"  ð åæ°:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\nâEå¤±è´¥: {result.get('error', 'æªç¥éè¯¯')}")