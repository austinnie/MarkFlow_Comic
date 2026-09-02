# skills/change_lighting/skill.py
"""
謾ｹ蜿伜・辣ｧ Skill - 菫晄戟蝨ｺ譎ｯ扈捺桷荳榊序・梧隼蜿伜・辣ｧ豌帛峩
螟咲畑騾夂畑 ControlNet 蠑墓梼・・epth + Lineart 髞∫ｩｺ髣ｴ扈捺桷・悟ｮ梧・蜈牙ｽｱ霓ｬ謐｢・・
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

# 蜈臥・鬚・ｮｾ
LIGHTING_PRESETS = {
    "golden_hour": {
        "prompt": "golden hour lighting, warm sunset light, soft warm glow, beautiful lighting, masterpiece",
        "negative": "harsh lighting, dark, cold, blue"
    },
    "sunny": {
        "prompt": "bright sunny day, natural sunlight, clear lighting, vibrant, masterpiece",
        "negative": "dark, gloomy, night, harsh shadows"
    },
    "night": {
        "prompt": "night scene, moonlight, dark atmosphere, soft lighting, starry, masterpiece",
        "negative": "bright, sunny, daylight, harsh lighting"
    },
    "studio": {
        "prompt": "studio lighting, professional photography, soft light, elegant, masterpiece",
        "negative": "harsh, natural light, outdoor"
    },
    "dramatic": {
        "prompt": "dramatic lighting, chiaroscuro, strong contrast, moody, cinematic, masterpiece",
        "negative": "flat lighting, soft, bright, daylight"
    },
    "soft": {
        "prompt": "soft lighting, diffused light, gentle, warm, cozy, masterpiece",
        "negative": "harsh, dramatic, strong contrast"
    },
    "cyberpunk": {
        "prompt": "cyberpunk lighting, neon lights, colorful, futuristic, glowing, masterpiece",
        "negative": "natural, daylight, soft, warm"
    },
    "moody": {
        "prompt": "moody lighting, dark atmosphere, mysterious, soft shadows, cinematic, masterpiece",
        "negative": "bright, sunny, happy, flat"
    }
}


class ChangeLighting:
    """謾ｹ蜿伜・辣ｧ謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_lighting"
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

        logger.info(f"ChangeLighting v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  蜈臥・鬚・ｮｾ: {len(LIGHTING_PRESETS)} 遘・)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.65,  # 蜈臥・謾ｹ蜿伜ｼｺ蠎ｦ荳榊ｮ懆ｿ・､ｧ・碁∩蜈咲ｻ捺桷蟠ｩ蝮・
            'default_lighting': 'golden_hour',
            'default_negative': 'ugly, deformed, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_lightings(self) -> Dict[str, Any]:
        return {"status": "success", "lightings": list(LIGHTING_PRESETS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """謇ｧ陦梧隼蜿伜・辣ｧ"""
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

            lighting = kwargs.get('lighting', self.config.get('default_lighting', 'golden_hour'))
            if lighting not in LIGHTING_PRESETS:
                return {"status": "error", "error": f"譛ｪ遏･蜈臥・: {lighting}・悟庄逕ｨ: {list(LIGHTING_PRESETS.keys())}"}

            lighting_config = LIGHTING_PRESETS[lighting]
            prompt = kwargs.get('prompt') or lighting_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or lighting_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.65))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_light_{lighting}_{timestamp}.png")

            logger.info(f"蜈臥・: {lighting}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="MLSD",      # 謠仙叙蟒ｺ遲・譎ｯ迚ｩ蜃菴・
                controlnet_model="depth",       # 豺ｱ蠎ｦ讓｡蝙矩煤豁ｻ遨ｺ髣ｴ扈捺桷
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "lighting": lighting,
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
        return f"<ChangeLighting(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="謾ｹ蜿伜・辣ｧ蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--lighting", "-l", default="golden_hour",
                        choices=list(LIGHTING_PRESETS.keys()), help="蜈臥・鬚・ｮｾ")
    parser.add_argument("--prompt", "-p", help="閾ｪ螳壻ｹ画署遉ｺ隸・)
    parser.add_argument("--strength", type=float, default=0.65, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeLighting(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        lighting=args.lighting, prompt=args.prompt,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))