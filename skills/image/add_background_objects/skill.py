# skills/add_background_objects/skill.py
"""
豺ｻ蜉閭梧勹迚ｩ菴・Skill - 蝨ｨ蝗ｾ迚・レ譎ｯ荳ｭ豺ｻ蜉謖・ｮ夂黄菴難ｼ檎ｻ昜ｸ咲ｴ蝮丞燕譎ｯ莠ｺ迚ｩ
螟咲畑騾夂畑 ControlNet 蠑墓梼・・LSD + Depth 髞∫ｩｺ髣ｴ扈捺桷・御ｽ主ｼｺ蠎ｦ邊ｾ蜃・刈迚ｩ菴難ｼ・
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

OBJECT_PROMPTS = {
    "flowers": "adding flowers, beautiful bouquet, colorful flowers, garden, masterpiece, high quality",
    "trees": "adding trees, beautiful trees, nature, greenery, masterpiece, high quality",
    "vase": "adding a vase, beautiful ceramic vase, decorative, masterpiece, high quality",
    "lamp": "adding a lamp, warm light, beautiful lamp, interior, masterpiece, high quality",
    "painting": "adding a painting, beautiful painting on wall, art, masterpiece, high quality",
    "books": "adding books, stack of books, library, cozy, masterpiece, high quality",
    "candle": "adding candles, warm glow, candlelight, cozy, masterpiece, high quality",
    "clock": "adding a clock, beautiful clock, decorative, masterpiece, high quality",
    "sculpture": "adding a sculpture, beautiful art piece, statue, masterpiece, high quality",
    "mirror": "adding a mirror, elegant mirror, decorative, masterpiece, high quality"
}


class AddBackgroundObjects:
    """豺ｻ蜉閭梧勹迚ｩ菴捺橿閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "add_background_objects"
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

        logger.info(f"AddBackgroundObjects v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  迚ｩ菴鍋ｱｻ蝙・ {list(OBJECT_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.50,  # 豺ｻ蜉閭梧勹迚ｩ菴灘ｼｺ蠎ｦ荳崎・螟ｪ鬮假ｼ碁∩蜈咲ｴ蝮丞燕譎ｯ
            'default_object': 'flowers',
            'default_negative': 'ugly, deformed, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_objects(self) -> Dict[str, Any]:
        return {"status": "success", "objects": list(OBJECT_PROMPTS.keys())}

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

            obj = kwargs.get('object', self.config.get('default_object', 'flowers'))
            if obj not in OBJECT_PROMPTS:
                return {"status": "error", "error": f"譛ｪ遏･迚ｩ菴・ {obj}・悟庄逕ｨ: {list(OBJECT_PROMPTS.keys())}"}

            obj_prompt = OBJECT_PROMPTS[obj]
            prompt = kwargs.get('prompt') or obj_prompt
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.50))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_add_{obj}_{timestamp}.png")

            logger.info(f"豺ｻ蜉迚ｩ菴・ {obj}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            # 菴ｿ逕ｨ MLSD・郁レ譎ｯ逶ｴ郤ｿ・・ Depth・域ｷｱ蠎ｦ遨ｺ髣ｴ・会ｼ悟惠荳咲ｴ蝮丞燕譎ｯ逧・ュ蜀ｵ荳区ｷｻ蜉迚ｩ菴・
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
                "object": obj,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "depth"
                }
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<AddBackgroundObjects(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="豺ｻ蜉閭梧勹迚ｩ菴灘ｷ･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--object", "-obj", default="flowers",
                        choices=list(OBJECT_PROMPTS.keys()), help="迚ｩ菴鍋ｱｻ蝙・)
    parser.add_argument("--strength", type=float, default=0.50, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = AddBackgroundObjects(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        object=args.object,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))