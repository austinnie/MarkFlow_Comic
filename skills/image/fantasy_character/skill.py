# skills/fantasy_character/skill.py
"""
螂・ｹｻ隗定牡 Skill - 蟆・ｺｺ迚ｩ蜿俶・螂・ｹｻ隗定牡・育ｲｾ轣ｵ/螟ｩ菴ｿ/諱ｶ鬲・鬲疲ｳ募ｸ育ｭ会ｼ・
螟咲畑騾夂畑 ControlNet 蠑墓梼・・penPose髞∝ｧｿ諤・ｼ碁ｫ伜ｹ・ｺｦ驥咲ｻ倩ｽｬ螂・ｹｻ鬟趣ｼ・
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
    logger.warning(f"torch 謌・PIL 譛ｪ螳芽｣・ {e}")

# ==================== 蠑募・騾夂畑蠑墓梼・域婿譯・・・====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"騾夂畑 ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")

# 螂・ｹｻ隗定牡謠千､ｺ隸埼・鄂ｮ
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
    """螂・ｹｻ隗定牡謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "fantasy_character"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 蠑ｺ蛻ｶ譛ｬ謚閭ｽ霎灘・逶ｮ蠖・====================
        self.output_dir = Path(self.config.get('output_dir', self.skill_dir / 'output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # ==================== 蛻晏ｧ句喧蠎募ｱょｼ墓梼 ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  笨・蠎募ｱ・ControlNet 蠑墓梼蛻晏ｧ句喧謌仙粥")
            except Exception as e:
                logger.warning(f"  蠎募ｱょｼ墓梼蛻晏ｧ句喧螟ｱ雍･: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"FantasyCharacter v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  螂・ｹｻ邀ｻ蝙・ {list(FANTASY_PROMPTS.keys())}")

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
        """謇ｧ陦悟･・ｹｻ隗定牡霓ｬ謐｢"""
        start_time = time.time()
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name} v{self.version}")

        try:
            # ==================== 荳･譬ｼ霍ｯ蠕・｡鬪・====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "郛ｺ蟆・image_path 蜿よ焚"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}縲りｯｷ譽譟･霍ｯ蠕・弍蜷ｦ豁｣遑ｮ・・}

            # 2. 闔ｷ蜿門盾謨ｰ
            fantasy_type = kwargs.get('fantasy_type', self.config.get('default_type', 'elf'))
            if fantasy_type not in FANTASY_PROMPTS:
                return {
                    "status": "error",
                    "error": f"譛ｪ遏･螂・ｹｻ邀ｻ蝙・ {fantasy_type}・悟庄逕ｨ: {list(FANTASY_PROMPTS.keys())}"
                }

            f_config = FANTASY_PROMPTS[fantasy_type]
            prompt = kwargs.get('prompt') or f_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or f_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = kwargs.get('output_path') or str(self.output_dir / f"{fantasy_type}_{timestamp}.png")

            logger.info(f"螂・ｹｻ邀ｻ蝙・ {fantasy_type}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",   # 謠仙叙莠ｺ菴馴ｪｨ譫ｶ
                controlnet_model="openpose",    # 髞∵ｭｻ莠ｺ菴灘ｧｿ諤・ｼ碁亟豁｢螂・ｹｻ蛹門ｯｼ閾ｴ蟠ｩ蝮・
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            # 菫晏ｭ伜・謨ｰ謐ｮ
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
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }

    def batch_process(self, image_paths: List[str], fantasy_type: str = 'elf', **kwargs) -> List[Dict[str, Any]]:
        """謇ｹ驥丞､・炊螟壼ｼ蝗ｾ迚・""
        results = []
        total = len(image_paths)
        for idx, img_path in enumerate(image_paths):
            logger.info(f"螟・炊 {idx+1}/{total}: {img_path}")
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
        description='螂・ｹｻ隗定牡逕滓・蝎ｨ v2.0 - 蟆・ｺｺ迚ｩ辣ｧ迚・ｽｬ謐｢荳ｺ螂・ｹｻ隗定牡',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''蜿ｯ逕ｨ逧・･・ｹｻ邀ｻ蝙・ {', '.join(FANTASY_PROMPTS.keys())}'''
    )
    
    parser.add_argument('image', help='霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument('-t', '--type', default='elf', choices=list(FANTASY_PROMPTS.keys()), help='螂・ｹｻ邀ｻ蝙・(鮟倩ｮ､: elf)')
    parser.add_argument('-o', '--output', help='霎灘・逶ｮ蠖・)
    parser.add_argument('-s', '--steps', type=int, default=35, help='謗ｨ逅・ｭ･謨ｰ')
    parser.add_argument('-r', '--strength', type=float, default=0.8, help='蜿俶困蠑ｺ蠎ｦ 0.0-1.0')
    parser.add_argument('--seed', type=int, default=-1, help='髫乗惻遘榊ｭ・)
    parser.add_argument('--prompt', help='閾ｪ螳壻ｹ画署遉ｺ隸・)
    parser.add_argument('--negative', help='閾ｪ螳壻ｹ芽ｴ滄擇謠千､ｺ隸・)
    parser.add_argument('--list-types', action='store_true', help='蛻怜・謇譛牙･・ｹｻ邀ｻ蝙・)
    
    args = parser.parse_args()
    
    if args.list_types:
        print("蜿ｯ逕ｨ逧・･・ｹｻ邀ｻ蝙・")
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
        print(f"\n笨・逕滓・謌仙粥!")
        print(f"  霎灘・: {result['output_path']}")
        print(f"  邀ｻ蝙・ {result['fantasy_type']}")
        print(f"  遘榊ｭ・ {result['seed']}")
        print(f"  閠玲慮: {result['elapsed_time']:.2f}s")
    else:
        print(f"\n笶・螟ｱ雍･: {result.get('error', '譛ｪ遏･髞呵ｯｯ')}")
        sys.exit(1)