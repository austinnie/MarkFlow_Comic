# skills/style_transfer/skill.py
"""
鬟取ｼ霓ｬ謐｢ Skill - 蟆・崟迚・ｽｬ謐｢荳ｺ謖・ｮ夐｣取ｼ・域ｲｹ逕ｻ/豌ｴ蠖ｩ/蜉ｨ貍ｫ/邏謠冗ｭ会ｼ・
螟咲畑騾夂畑 ControlNet 蠑墓梼・・ED + Lineart 髞∵ｭｻ譫・崟・碁ｫ伜ｹ・ｺｦ驥肴桷逕ｻ髱｢雍ｨ諢滂ｼ・
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

# 鬟取ｼ鬚・ｮｾ
STYLE_PRESETS = {
    "oil_painting": {
        "prompt": "oil painting, thick brushstrokes, canvas texture, masterpiece, van gogh style, rich colors, artistic, high quality",
        "negative": "photorealistic, 3d render, digital art, smooth, cartoon, anime"
    },
    "watercolor": {
        "prompt": "watercolor painting, soft wash, paper texture, flowing colors, transparent, artistic, masterpiece, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges, oil painting"
    },
    "anime": {
        "prompt": "anime style, cel shading, vibrant colors, anime art, masterpiece, best quality, 2d illustration, manga style",
        "negative": "photorealistic, 3d render, realistic, ugly, deformed"
    },
    "sketch": {
        "prompt": "pencil sketch, graphite drawing, fine lines, cross-hatching, monochrome, black and white, masterpiece, high quality",
        "negative": "photorealistic, color, 3d render, smooth, oil painting"
    },
    "impressionist": {
        "prompt": "impressionist painting, soft brushstrokes, vibrant colors, light effects, masterpiece, claude monet style, high quality",
        "negative": "photorealistic, 3d render, digital art, hard edges"
    },
    "pixel_art": {
        "prompt": "pixel art, retro game style, 8-bit, blocky, colorful, masterpiece, high quality",
        "negative": "photorealistic, 3d render, smooth, blurry, oil painting"
    },
    "cyberpunk": {
        "prompt": "cyberpunk style, neon colors, futuristic, glowing lights, dark atmosphere, sci-fi, masterpiece, high quality",
        "negative": "photorealistic, 3d render, ugly, deformed, blurry"
    },
    "vintage": {
        "prompt": "vintage photo style, retro, film grain, warm tones, nostalgic, old photo, masterpiece, high quality",
        "negative": "digital art, 3d render, photorealistic, ugly, deformed"
    }
}


class StyleTransfer:
    """鬟取ｼ霓ｬ謐｢謚閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "style_transfer"
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

        logger.info(f"StyleTransfer v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  鬚・ｮｾ鬟取ｼ: {len(STYLE_PRESETS)} 遘・)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.75,  # 鬟取ｼ霓ｬ謐｢髴隕・ｫ伜ｼｺ蠎ｦ驥咲ｻ俶擂驥頑叛雍ｨ諢・
            'default_style': 'oil_painting',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_styles(self) -> Dict[str, Any]:
        return {"status": "success", "styles": list(STYLE_PRESETS.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """謇ｧ陦碁｣取ｼ霓ｬ謐｢"""
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

            style = kwargs.get('style', self.config.get('default_style', 'oil_painting'))
            if style not in STYLE_PRESETS:
                return {"status": "error", "error": f"譛ｪ遏･鬟取ｼ: {style}・悟庄逕ｨ: {list(STYLE_PRESETS.keys())}"}

            style_config = STYLE_PRESETS[style]
            prompt = kwargs.get('prompt') or style_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or style_config['negative']

            strength = kwargs.get('strength', self.config.get('default_strength', 0.75))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{style}_{timestamp}.png")

            logger.info(f"鬟取ｼ: {style}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            # 菴ｿ逕ｨ HED 謠仙叙霓ｯ霎ｹ郛假ｼ碁・蜷・Lineart 讓｡蝙矩煤豁ｻ譫・崟
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
                "style": style,
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
        return f"<StyleTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="鬟取ｼ霓ｬ謐｢蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--style", "-s", default="oil_painting",
                        choices=list(STYLE_PRESETS.keys()), help="鬟取ｼ")
    parser.add_argument("--strength", type=float, default=0.75, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = StyleTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output, style=args.style,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))