# skills/fantasy_character/skill.py
"""
å¥E¹»è§è² Skill - å°Eººç©åæEå¥E¹»è§è²Eç²¾çµ/å¤©ä½¿/æ¶é­Eé­æ³å¸ç­ï¼E
å¤ç¨éç¨ ControlNet å¼æEEpenPoseéå§¿æE¼é«å¹Eº¦éç»è½¬å¥E¹»é£ï¼E
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
    logger.warning(f"torch æEPIL æªå®è£E {e}")

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# å¥E¹»è§è²æç¤ºè¯éEç½®
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
    """å¥E¹»è§è²æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "fantasy_character"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = Path(self.config.get('output_dir', self.skill_dir / 'output'))
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

        logger.info(f"FantasyCharacter v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  å¥E¹»ç±»åE {list(FANTASY_PROMPTS.keys())}")

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
        """æ§è¡å¥E¹»è§è²è½¬æ¢"""
        start_time = time.time()
        logger.info(f"æ§è¡æè½: {self.name} v{self.version}")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "ç¼ºå°Eimage_path åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            # 2. è·ååæ°
            fantasy_type = kwargs.get('fantasy_type', self.config.get('default_type', 'elf'))
            if fantasy_type not in FANTASY_PROMPTS:
                return {
                    "status": "error",
                    "error": f"æªç¥å¥E¹»ç±»åE {fantasy_type}Eå¯ç¨: {list(FANTASY_PROMPTS.keys())}"
                }

            f_config = FANTASY_PROMPTS[fantasy_type]
            prompt = kwargs.get('prompt') or f_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or f_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # é»è®¤è¾åEå°æ¬æè½ç®å½E
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = kwargs.get('output_path') or str(self.output_dir / f"{fantasy_type}_{timestamp}.png")

            logger.info(f"å¥E¹»ç±»åE {fantasy_type}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",   # æåäººä½éª¨æ¶
                controlnet_model="openpose",    # éæ­»äººä½å§¿æE¼é²æ­¢å¥E¹»åå¯¼è´å´©åE
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            # ä¿å­åEæ°æ®
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
            logger.error(f"æ§è¡å¤±è´¥: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }

    def batch_process(self, image_paths: List[str], fantasy_type: str = 'elf', **kwargs) -> List[Dict[str, Any]]:
        """æ¹éå¤Eå¤å¼ å¾çE""
        results = []
        total = len(image_paths)
        for idx, img_path in enumerate(image_paths):
            logger.info(f"å¤E {idx+1}/{total}: {img_path}")
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
        description='å¥E¹»è§è²çæEå¨ v2.0 - å°Eººç©ç§çE½¬æ¢ä¸ºå¥E¹»è§è²',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''å¯ç¨çE¥E¹»ç±»åE {', '.join(FANTASY_PROMPTS.keys())}'''
    )
    
    parser.add_argument('image', help='è¾åEå¾çE·¯å¾E)
    parser.add_argument('-t', '--type', default='elf', choices=list(FANTASY_PROMPTS.keys()), help='å¥E¹»ç±»åE(é»è®¤: elf)')
    parser.add_argument('-o', '--output', help='è¾åEç®å½E)
    parser.add_argument('-s', '--steps', type=int, default=35, help='æ¨çE­¥æ°')
    parser.add_argument('-r', '--strength', type=float, default=0.8, help='åæ¢å¼ºåº¦ 0.0-1.0')
    parser.add_argument('--seed', type=int, default=-1, help='éæºç§å­E)
    parser.add_argument('--prompt', help='èªå®ä¹æç¤ºè¯E)
    parser.add_argument('--negative', help='èªå®ä¹è´é¢æç¤ºè¯E)
    parser.add_argument('--list-types', action='store_true', help='ååEææå¥E¹»ç±»åE)
    
    args = parser.parse_args()
    
    if args.list_types:
        print("å¯ç¨çE¥E¹»ç±»åE")
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
        print(f"\nâEçæEæå!")
        print(f"  è¾åE: {result['output_path']}")
        print(f"  ç±»åE {result['fantasy_type']}")
        print(f"  ç§å­E {result['seed']}")
        print(f"  èæ¶: {result['elapsed_time']:.2f}s")
    else:
        print(f"\nâEå¤±è´¥: {result.get('error', 'æªç¥éè¯¯')}")
        sys.exit(1)