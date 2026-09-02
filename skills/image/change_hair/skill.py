# skills/change_hair/skill.py
"""
謐｢蜿大梛/蜿題牡 Skill - 菫晄戟蟋ｿ諤∝柱閼ｸ驛ｨ荳榊序・梧隼蜿伜書蝙・
螟咲畑騾夂畑 ControlNet 蠑墓梼・・ED + Lineart 髞∬┷髞∝書髯・ｺｿ・檎ｲｾ蜃・困蜿題牡/蜿大梛・・
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

# 蜿大梛鬚・ｮｾ
HAIR_STYLES = {
    "long_flowing": "long flowing hair, beautiful hair, silky smooth, masterpiece",
    "curly": "curly hair, beautiful curls, voluminous hair, masterpiece",
    "short_bob": "short bob haircut, stylish hair, chic, masterpiece",
    "ponytail": "high ponytail hairstyle, sleek hair, masterpiece",
    "braid": "braided hair, beautiful braid, masterpiece",
    "bun": "hair bun, elegant hairstyle, updo, masterpiece",
    "wave": "wavy hair, beautiful waves, soft hair, masterpiece",
    "straight": "straight hair, sleek, smooth, masterpiece"
}

HAIR_COLORS = {
    "black": "black hair",
    "blonde": "blonde hair, golden hair",
    "brown": "brown hair, chestnut hair",
    "red": "red hair, auburn hair",
    "pink": "pink hair, pastel pink",
    "blue": "blue hair, vibrant blue",
    "silver": "silver hair, white hair",
    "purple": "purple hair, violet"
}


class ChangeHair:
    """謐｢蜿大梛謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_hair"
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

        logger.info(f"ChangeHair v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.45,  # 謐｢蜿題牡蠑ｺ蠎ｦ荳崎・螟ｪ鬮假ｼ悟凄蛻呵┷驛ｨ莨壼ｴｩ
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(HAIR_STYLES.keys()), "colors": list(HAIR_COLORS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """謇ｧ陦梧困蜿大梛"""
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

            hair_style = kwargs.get('hair_style')
            hair_color = kwargs.get('hair_color')

            # 譫・ｻｺ謠千､ｺ隸・
            prompt_parts = []
            if hair_style and hair_style in HAIR_STYLES:
                prompt_parts.append(HAIR_STYLES[hair_style])
            if hair_color and hair_color in HAIR_COLORS:
                prompt_parts.append(HAIR_COLORS[hair_color])
            if not prompt_parts:
                prompt_parts = ["beautiful hair", "masterpiece"]

            prompt = kwargs.get('prompt') or (", ".join(prompt_parts) + ", masterpiece, high quality")
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.45))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                style_suffix = hair_style or "custom"
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_hair_{style_suffix}_{timestamp}.png")

            logger.info(f"蜿大梛: {hair_style or '閾ｪ螳壻ｹ・}, 蜿題牡: {hair_color or '閾ｪ螳壻ｹ・}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            # 菴ｿ逕ｨ HED 謠仙叙霓ｯ霎ｹ郛假ｼ碁煤螳夊┷驛ｨ霓ｮ蟒灘柱蜿鷹刔郤ｿ
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
                "hair_style": hair_style,
                "hair_color": hair_color,
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
        return f"<ChangeHair(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="謐｢蜿大梛蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--style", "-s", choices=list(HAIR_STYLES.keys()), help="蜿大梛")
    parser.add_argument("--color", "-c", choices=list(HAIR_COLORS.keys()), help="蜿題牡")
    parser.add_argument("--prompt", "-p", help="閾ｪ螳壻ｹ画署遉ｺ隸・)
    parser.add_argument("--strength", type=float, default=0.45, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeHair(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        hair_style=args.style, hair_color=args.color, prompt=args.prompt,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))