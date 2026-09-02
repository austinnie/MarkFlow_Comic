# skills/add_animal_ears/skill.py
"""
豺ｻ蜉蜈ｽ閠ｳ Skill - 荳ｺ莠ｺ迚ｩ豺ｻ蜉蜉ｨ迚ｩ閠ｳ譛ｵ・育賢閠ｳ/迢苓ｳ/迢占ｳ遲会ｼ会ｼ檎ｻ晏ｯｹ荳肴隼蜿倅ｺｺ迚ｩ髱｢驛ｨ
螟咲畑騾夂畑 ControlNet 蠑墓梼・・ED + Lineart 髞∵ｭｻ髱｢驛ｨ・御ｸｭ蠑ｺ蠎ｦ邊ｾ蜃・函髟ｿ蜈ｽ閠ｳ・・
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
    logger.warning("torch 謌・PIL 譛ｪ螳芽｣・)

# ==================== 蠑募・騾夂畑蠑墓梼・域婿譯・・・====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"騾夂畑 ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")

ANIMAL_EARS = {
    "cat": {
        "prompt": "cat ears, cute cat ears, neko, furry ears, adorable, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs"
    },
    "dog": {
        "prompt": "dog ears, floppy dog ears, cute, adorable, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs"
    },
    "fox": {
        "prompt": "fox ears, pointed ears, cute fox ears, adorable, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs"
    },
    "wolf": {
        "prompt": "wolf ears, large pointed ears, wild, majestic, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs"
    },
    "bunny": {
        "prompt": "bunny ears, long rabbit ears, cute, adorable, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs"
    },
    "bear": {
        "prompt": "bear ears, round fluffy ears, cute, adorable, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs"
    }
}


class AddAnimalEars:
    """豺ｻ蜉蜈ｽ閠ｳ謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "add_animal_ears"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 蠑ｺ蛻ｶ譛ｬ謚閭ｽ霎灘・逶ｮ蠖・====================
        self.output_dir = self.skill_dir / "output"
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

        logger.info(f"AddAnimalEars v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  蜉ｨ迚ｩ邀ｻ蝙・ {list(ANIMAL_EARS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.55,  # 豺ｻ蜉閠ｳ譛ｵ蠑ｺ蠎ｦ荳崎・螟ｪ鬮假ｼ碁∩蜈咲ｴ蝮城擇驛ｨ
            'default_animal': 'cat',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_animals(self) -> Dict[str, Any]:
        return {"status": "success", "animals": list(ANIMAL_EARS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name}")

        try:
            # ==================== 荳･譬ｼ霍ｯ蠕・｡鬪・====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 譏ｯ蠢・｡ｫ蜿よ焚"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}縲りｯｷ譽譟･霍ｯ蠕・弍蜷ｦ豁｣遑ｮ・・}

            animal = kwargs.get('animal', self.config.get('default_animal', 'cat'))
            if animal not in ANIMAL_EARS:
                return {"status": "error", "error": f"譛ｪ遏･蜉ｨ迚ｩ: {animal}・悟庄逕ｨ: {list(ANIMAL_EARS.keys())}"}

            animal_config = ANIMAL_EARS[animal]
            prompt = kwargs.get('prompt') or animal_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or animal_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.55))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_ears_{animal}_{timestamp}.png")

            logger.info(f"蜉ｨ迚ｩ邀ｻ蝙・ {animal}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            # 菴ｿ逕ｨ HED + Lineart・碁煤豁ｻ莠ｺ迚ｩ髱｢驛ｨ霓ｮ蟒難ｼ悟宵蜈∬ｮｸ閠ｳ譛ｵ逕滄柄蜃ｺ譚･
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",
                controlnet_model="lineart",
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "animal": animal,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "lineart"
                }
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<AddAnimalEars(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="豺ｻ蜉蜈ｽ閠ｳ蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--animal", "-a", default="cat",
                        choices=list(ANIMAL_EARS.keys()), help="蜉ｨ迚ｩ邀ｻ蝙・)
    parser.add_argument("--strength", type=float, default=0.55, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = AddAnimalEars(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        animal=args.animal,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))