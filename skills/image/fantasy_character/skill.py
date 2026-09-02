# skills/fantasy_character/skill.py
"""
å¥E¹èè² Skill - å°Eººç©åæEå¥E¹èè²Eç²¾çµ/å¤©ä½¿/æ¶é­Eé­æ³å¸ç­ï¼E
å¤ç¨éç¨ ControlNet å¼æEEpenPoseéå¿æE¼é«å¹Eº¦éçè½¬å¥E¹é£ï¼E
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"torch æEPIL æªå®è£E {e}")

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# å¥E¹èè²æç¤ºè¯éEç½®
FANTASY_PROMPTS = {
    "elf": {
        "prompt": "beautiful elf, long pointed ears, fantasy elf, elegant, magical, nature, fantasy character, masterpiece, high quality, detailed",
        "negative": "ugly, deformed, human, modern, realistic, bad anatomy"
    },
    "angel": {
        "prompt": "beautiful angel, white feathered wings, golden halo, divine, ethereal, heavenly, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, demon, devil, dark, evil"
    },
    "demon": {
        "prompt": "beautiful demon, curved horns, dark bat wings, seductive, dark fantasy, hellfire, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, angel, holy, light, pure"
    },
    "mage": {
        "prompt": "powerful mage, wizard, magical robes, staff, spellcasting, arcane energy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, modern, realistic, casual"
    },
    "knight": {
        "prompt": "majestic knight, full plate armor, fantasy knight, sword, shield, heroic, noble, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, modern, casual, civilian"
    },
    "fairy": {
        "prompt": "beautiful fairy, translucent wings, glowing, magical, ethereal, nature spirit, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic"
    },
    "vampire": {
        "prompt": "elegant vampire, pale skin, sharp fangs, gothic, aristocratic, dark fantasy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, cheerful"
    },
    "merfolk": {
        "prompt": "beautiful mermaid, fish tail, underwater, coral, seashells, aquatic fantasy, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, legs"
    },
    "dragonborn": {
        "prompt": "dragonborn character, dragon scales, reptilian features, fantasy, powerful, elemental, fantasy character, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic"
    },
    "phoenix": {
        "prompt": "phoenix themed character, fiery, reborn, majestic, golden flames, fantasy, masterpiece, high quality",
        "negative": "ugly, deformed, human, modern, realistic, cold"
    }
}


class FantasyCharacter:
    """å¥E¹èè²æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "fantasy_character"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = Path(self.config.get('output_dir', self.skill_dir / 'output'))
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

        logger.info(f"FantasyCharacter v{self.version} åååå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  å¥E¹ç±åE {list(FANTASY_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_steps': 35,
            'default_strength': 0.8,
            'default_type': 'elf',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality, modern, realistic, human',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def get_available_types(self) -> Dict[str, str]:
        return {k: v['prompt'][:50] + '...' for k, v in FANTASY_PROMPTS.items()}

    def get_type_info(self, fantasy_type: str) -> Optional[Dict[str, str]]:
        return FANTASY_PROMPTS.get(fantasy_type)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æè¡å¥E¹èè²è½¬æ¢"""
        start_time = time.time()
        logger.info(f"æè¡æè½: {self.name} v{self.version}")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "ç¼ºå°Eimage_path åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            # 2. è·ååæ°
            fantasy_type = kwargs.get('fantasy_type', self.config.get('default_type', 'elf'))
            if fantasy_type not in FANTASY_PROMPTS:
                return {
                    "status": "error",
                    "error": f"æªç¥å¥E¹ç±åE {fantasy_type}Eå¯ç¨: {list(FANTASY_PROMPTS.keys())}"
                }

            f_config = FANTASY_PROMPTS[fantasy_type]
            prompt = kwargs.get('prompt') or f_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or f_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # éè®¤è¾åEå°æ¬æè½ç®å½E
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = kwargs.get('output_path') or str(self.output_dir / f"{fantasy_type}_{timestamp}.png")

            logger.info(f"å¥E¹ç±åE {fantasy_type}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",   # æåäººä½éª¨æ¶
                controlnet_model="openpose",    # éæ­äººä½å¿æE¼é²æ­¢å¥E¹åå¯¼è´å´©åE
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            # ä¿å­åEæ°æ®
            metadata = {
                'skill': self.name,
                'version': self.version,
                'fantasy_type': fantasy_type,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'steps': steps,
                'strength': strength,
                'seed': seed,
                'output_path': output_path,
                'timestamp': timestamp,
                'use_controlnet': True,
            }

            metadata_path = Path(output_path).with_suffix('.meta.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "metadata_path": str(metadata_path),
                "fantasy_type": fantasy_type,
                "seed": seed,
                "elapsed_time": time.time() - start_time,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"æè¡å¤±è´¥: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }

    def batch_process(self, image_paths: List[str], fantasy_type: str = 'elf', **kwargs) -> List[Dict[str, Any]]:
        """æ¹éå¤Eå¤å¼ å¾çE""
        results = []
        total = len(image_paths)
        for idx, img_path in enumerate(image_paths):
            logger.info(f"å¤E {idx+1}/{total}: {img_path}")
            result = self.execute(
                image_path=img_path,
                fantasy_type=fantasy_type,
                **kwargs
            )
            results.append({'image': img_path, 'result': result})
            if idx < total - 1:
                time.sleep(0.5)
        return results

    def __repr__(self) -> str:
        return f"<FantasyCharacter skill v{self.version} on {self.device}>"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='å¥E¹èè²çæEå¨ v2.0 - å°Eººç©ççE½¬æ¢ä¸ºå¥E¹èè²',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''å¯ç¨çE¥E¹ç±åE {', '.join(FANTASY_PROMPTS.keys())}'''
    )
    
    parser.add_argument('image', help='è¾åEå¾çE·¯å¾E)
    parser.add_argument('-t', '--type', default='elf', choices=list(FANTASY_PROMPTS.keys()), help='å¥E¹ç±åE(éè®¤: elf)')
    parser.add_argument('-o', '--output', help='è¾åEç®å½E)
    parser.add_argument('-s', '--steps', type=int, default=35, help='æ¨çE­¥æ°')
    parser.add_argument('-r', '--strength', type=float, default=0.8, help='åæ¢å¼ºåº¦ 0.0-1.0')
    parser.add_argument('--seed', type=int, default=-1, help='éæºçå­E)
    parser.add_argument('--prompt', help='èªå®ä¹æç¤ºè¯E)
    parser.add_argument('--negative', help='èªå®ä¹è´é¢æç¤ºè¯E)
    parser.add_argument('--list-types', action='store_true', help='ååEææå¥E¹ç±åE)
    
    args = parser.parse_args()
    
    if args.list_types:
        print("å¯ç¨çE¥E¹ç±åE")
        for t in FANTASY_PROMPTS.keys():
            print(f"  - {t}")
        sys.exit(0)
    
    skill = FantasyCharacter()
    result = skill.execute(
        image_path=args.image,
        fantasy_type=args.type,
        output_dir=args.output,
        steps=args.steps,
        strength=args.strength,
        seed=args.seed,
        prompt=args.prompt,
        negative_prompt=args.negative,
    )
    
    if result['status'] == 'success':
        print(f"\nâEçæEæå!")
        print(f"  è¾åE: {result['output_path']}")
        print(f"  ç±åE {result['fantasy_type']}")
        print(f"  çå­E {result['seed']}")
        print(f"  èæ¶: {result['elapsed_time']:.2f}s")
    else:
        print(f"\nâEå¤±è´¥: {result.get('error', 'æªç¥éè¯¯')}")
        sys.exit(1)
"""