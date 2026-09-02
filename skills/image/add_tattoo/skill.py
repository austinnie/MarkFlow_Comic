# skills/add_tattoo/skill.py
"""
豺ｻ蜉郤ｹ霄ｫ Skill - 蝨ｨ莠ｺ迚ｩ霄ｫ菴謎ｸ頑ｷｻ蜉郤ｹ霄ｫ・檎ｻ昜ｸ肴隼蜿倅ｽ灘梛蜥瑚う濶ｲ
螟咲畑騾夂畑 ControlNet 蠑墓梼・・ED + Lineart 譫∽ｽ主ｼｺ蠎ｦ・檎ｲｾ蜃・匠蜉郤ｹ霄ｫ郤ｹ逅・ｼ・
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

TATTOO_PROMPTS = {
    "dragon": {
        "prompt": "dragon tattoo on skin, intricate dragon design, detailed tattoo, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    },
    "flower": {
        "prompt": "flower tattoo, beautiful floral tattoo on skin, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    },
    "tribal": {
        "prompt": "tribal tattoo, traditional tribal design, bold lines, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    },
    "mandala": {
        "prompt": "mandala tattoo, intricate geometric pattern, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    },
    "rose": {
        "prompt": "rose tattoo, realistic rose on skin, detailed, beautiful, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    },
    "skull": {
        "prompt": "skull tattoo, detailed skull design, dark, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    },
    "butterfly": {
        "prompt": "butterfly tattoo, beautiful butterfly on skin, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    },
    "script": {
        "prompt": "script tattoo, beautiful calligraphy tattoo on skin, meaningful text, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality"
    }
}


class AddTattoo:
    """豺ｻ蜉郤ｹ霄ｫ謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "add_tattoo"
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

        logger.info(f"AddTattoo v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  郤ｹ霄ｫ邀ｻ蝙・ {list(TATTOO_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.40,  # 豺ｻ蜉郤ｹ霄ｫ蠑ｺ蠎ｦ荳崎・螟ｪ鬮假ｼ碁∩蜈肴隼蜿倅ｺｺ菴鍋ｻ捺桷
            'default_tattoo': 'dragon',
            'default_negative': 'ugly, deformed, bad anatomy, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_tattoos(self) -> Dict[str, Any]:
        return {"status": "success", "tattoos": list(TATTOO_PROMPTS.keys())}

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

            tattoo = kwargs.get('tattoo', self.config.get('default_tattoo', 'dragon'))
            if tattoo not in TATTOO_PROMPTS:
                return {"status": "error", "error": f"譛ｪ遏･郤ｹ霄ｫ邀ｻ蝙・ {tattoo}・悟庄逕ｨ: {list(TATTOO_PROMPTS.keys())}"}

            tattoo_config = TATTOO_PROMPTS[tattoo]
            prompt = kwargs.get('prompt') or tattoo_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or tattoo_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.40))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_tattoo_{tattoo}_{timestamp}.png")

            logger.info(f"郤ｹ霄ｫ邀ｻ蝙・ {tattoo}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            # 菴ｿ逕ｨ HED + Lineart 髞∵ｭｻ莠ｺ菴楢ｽｮ蟒灘柱閧､濶ｲ・悟宵蜿蜉郤ｹ霄ｫ
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
                "tattoo": tattoo,
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
        return f"<AddTattoo(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="豺ｻ蜉郤ｹ霄ｫ蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--tattoo", "-t", default="dragon",
                        choices=list(TATTOO_PROMPTS.keys()), help="郤ｹ霄ｫ邀ｻ蝙・)
    parser.add_argument("--strength", type=float, default=0.40, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = AddTattoo(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        tattoo=args.tattoo,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))