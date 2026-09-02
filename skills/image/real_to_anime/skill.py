# skills/real_to_anime/skill.py
"""
逵滉ｺｺ霓ｬ蜉ｨ貍ｫ Skill - 蟆・悄螳樒・迚・ｽｬ謐｢荳ｺ蜉ｨ貍ｫ鬟取ｼ
螟咲畑騾夂畑 ControlNet 蠑墓梼・・penPose菫晄戟蟋ｿ諤・ｼ碁ｫ伜ｹ・ｺｦ驥咲ｻ倩ｽｬ鬟取ｼ・・
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

# 蜉ｨ貍ｫ鬟取ｼ鬚・ｮｾ
ANIME_STYLES = {
    "gibli": {
        "prompt": "studio ghibli style, anime, beautiful, soft colors, masterpiece, best quality, 2d animation, hayao miyazaki style",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "shinkai": {
        "prompt": "makoto shinkai style, anime, vibrant colors, beautiful lighting, masterpiece, best quality, your name style, 2d animation",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "jojo": {
        "prompt": "jojo's bizarre adventure style, anime, bold colors, dynamic, masterpiece, best quality, 2d animation, dramatic",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "classic": {
        "prompt": "classic anime style, 90s anime, vibrant colors, beautiful, masterpiece, best quality, 2d illustration",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "modern": {
        "prompt": "modern anime style, beautiful, vibrant colors, detailed, masterpiece, best quality, 2d illustration, high quality",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "manga": {
        "prompt": "manga style, black and white, manga art, masterpiece, best quality, 2d illustration, comic style",
        "negative": "photorealistic, 3d render, realistic, color, ugly, deformed"
    }
}


class RealToAnime:
    """逵滉ｺｺ霓ｬ蜉ｨ貍ｫ謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "real_to_anime"
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

        logger.info(f"RealToAnime v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  蜉ｨ貍ｫ鬟取ｼ: {len(ANIME_STYLES)} 遘・)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 35,
            'default_strength': 0.8, # 霓ｬ蜉ｨ貍ｫ髴隕∬ｾ・ｫ倡噪驥咲ｻ伜ｹ・ｺｦ譚･謾ｹ蜿倡判鬟・
            'default_style': 'modern',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(ANIME_STYLES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """謇ｧ陦檎悄莠ｺ霓ｬ蜉ｨ貍ｫ"""
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

            style = kwargs.get('style', self.config.get('default_style', 'modern'))
            if style not in ANIME_STYLES:
                return {"status": "error", "error": f"譛ｪ遏･鬟取ｼ: {style}・悟庄逕ｨ: {list(ANIME_STYLES.keys())}"}

            style_config = ANIME_STYLES[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.8))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_anime_{style}_{timestamp}.png")

            logger.info(f"蜉ｨ貍ｫ鬟取ｼ: {style}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",   # 謠仙叙莠ｺ菴馴ｪｨ譫ｶ
                controlnet_model="openpose",    # 蠑ｺ蛻ｶ髞∵ｭｻ莠ｺ菴灘ｧｿ諤・ｼ碁亟豁｢蜿伜ｽ｢
                strength=strength,              # 霎・ｫ倡噪驥咲ｻ伜ｹ・ｺｦ・悟ｮ梧・逕ｻ鬟手ｽｬ蛹・
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "style": style,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "openpose"
                }
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<RealToAnime(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="逵滉ｺｺ霓ｬ蜉ｨ貍ｫ蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--style", "-s", default="modern",
                        choices=list(ANIME_STYLES.keys()), help="蜉ｨ貍ｫ鬟取ｼ")
    parser.add_argument("--prompt", "-p", help="閾ｪ螳壻ｹ画署遉ｺ隸・)
    parser.add_argument("--strength", type=float, default=0.8, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=35, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = RealToAnime(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        style=args.style, prompt=args.prompt,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))