# skills/change_background/skill.py
"""
謐｢閭梧勹 Skill - 菫晄戟莠ｺ迚ｩ荳榊序・梧崛謐｢閭梧勹
螟咲畑騾夂畑 ControlNet 蠑墓梼・・LSD + Depth 髞∫ｩｺ髣ｴ扈捺桷・御ｽ主ｼｺ蠎ｦ邊ｾ蜃・困閭梧勹・・
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

# 豺ｻ蜉鬘ｹ逶ｮ霍ｯ蠕・
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"diffusers 譛ｪ螳芽｣・ {e}")

# ==================== 蠑募・騾夂畑蠑墓梼・域婿譯・・・====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"騾夂畑 ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")


class ChangeBackground:
    """謐｢閭梧勹謚閭ｽ v2.0"""

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

    # 鬚・ｮｾ閭梧勹謠千､ｺ隸・
    PRESET_BACKGROUNDS = {
        "beach": "beach, ocean waves, golden sand, sunset, palm trees, tropical paradise",
        "forest": "deep forest, sunlight through trees, green moss, peaceful nature, woodland",
        "mountain": "snowy mountain peaks, alpine meadow, clear blue sky, majestic landscape",
        "city": "modern city skyline, skyscrapers, night lights, urban atmosphere, bustling street",
        "space": "outer space, stars, nebula, galaxy, cosmic, sci-fi background",
        "underwater": "underwater world, coral reef, colorful fish, sun rays through water",
        "sakura": "cherry blossom trees, pink petals, spring, Japanese garden, soft pink",
        "autumn": "autumn forest, golden and red leaves, warm colors, fall season",
        "snow": "snowy landscape, winter wonderland, white snow, pine trees, cozy cabin",
        "desert": "desert dunes, golden sand, warm sunset, vast landscape, arid",
        "library": "old library, bookshelves, warm lighting, academic atmosphere, quiet",
        "cafe": "cozy cafe, warm lighting, coffee, comfortable chairs, urban life",
        "temple": "ancient temple, traditional architecture, serene, spiritual, cultural",
        "sunset": "sunset over the sea, vibrant orange and pink sky, romantic, beautiful",
        "aurora": "northern lights, aurora borealis, starry night, magical, arctic",
        "waterfall": "majestic waterfall, mist, lush green, tropical, powerful nature",
        "castle": "medieval castle, stone walls, historical, fantasy, majestic",
        "cyberpunk": "cyberpunk city, neon lights, rainy street, futuristic, dark",
        "studio": "white studio background, professional photography, clean, minimal",
        "gradient": "smooth gradient background, soft colors, modern, clean aesthetic",
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_background"
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

        logger.info(f"ChangeBackground v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  鬚・ｮｾ閭梧勹: {len(self.PRESET_BACKGROUNDS)} 遘・)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.55,  # 謐｢閭梧勹荳崎・隶ｩ蜑肴勹莠ｺ迚ｩ蜿伜ｽ｢
            'default_prompt': 'beautiful natural background, masterpiece, high quality',
            'default_negative': 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config.get('output_dir', str(self.skill_dir / 'output'))).mkdir(parents=True, exist_ok=True)

    def list_presets(self) -> Dict[str, Any]:
        return {"status": "success", "presets": self.PRESET_BACKGROUNDS, "count": len(self.PRESET_BACKGROUNDS)}

    # ==================== 荳ｻ謇ｧ陦梧婿豕・====================
    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name} (v{self.version})")

        try:
            # ==================== 荳･譬ｼ霍ｯ蠕・｡鬪・====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 譏ｯ蠢・｡ｫ蜿よ焚"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}縲りｯｷ譽譟･霍ｯ蠕・弍蜷ｦ豁｣遑ｮ・・}

            output_path = kwargs.get('output_path')
            background_prompt = kwargs.get('background_prompt')
            preset = kwargs.get('preset')

            if preset and preset in self.PRESET_BACKGROUNDS:
                background_prompt = self.PRESET_BACKGROUNDS[preset]
                logger.info(f"  菴ｿ逕ｨ鬚・ｮｾ閭梧勹: {preset}")

            if not background_prompt:
                background_prompt = self.config.get('default_prompt', 'beautiful natural background, masterpiece, high quality')

            prompt = background_prompt
            negative_prompt = kwargs.get('negative_prompt', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.55))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                preset_suffix = f"_{preset}" if preset else ""
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{timestamp}_bg{preset_suffix}.png")

            logger.info(f"螟・炊: {os.path.basename(abs_image_path)} ({Image.open(abs_image_path).size})")
            logger.info(f"閭梧勹謠剰ｿｰ: {background_prompt[:80]}...")

            # 菴ｿ逕ｨ MLSD (謠仙叙蝨ｺ譎ｯ逶ｴ郤ｿ) + Depth (髞∫ｩｺ髣ｴ豺ｱ蠎ｦ)・碁・蜷井ｽ主ｼｺ蠎ｦ謐｢閭梧勹
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",  # 笨・莉・"MLSD" 謾ｹ荳ｺ "HED"
                controlnet_model="depth",  # 謌・"canny"
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "parameters": {
                    "image_path": str(abs_image_path),
                    "background_prompt": background_prompt,
                    "preset": preset,
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "device": self.device,
                    "controlnet": True,
                    "controlnet_type": "depth"
                },
                "generation_time": f"{time.time() - start_time:.2f}s",
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e), "skill": self.name}

    def __repr__(self):
        return f"<ChangeBackground(name={self.name}, version={self.version})>"


# ==================== 蜻ｽ莉､陦悟・蜿｣ ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="謐｢閭梧勹蟾･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--preset", "-p", choices=list(ChangeBackground.PRESET_BACKGROUNDS.keys()),
                        help="鬚・ｮｾ閭梧勹蜷咲ｧｰ")
    parser.add_argument("--prompt", help="閾ｪ螳壻ｹ芽レ譎ｯ謠剰ｿｰ謠千､ｺ隸・)
    parser.add_argument("--strength", "-s", type=float, default=0.55, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="隶ｾ螟・)

    args = parser.parse_args()

    skill = ChangeBackground(config={'device': args.device})

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        preset=args.preset,
        background_prompt=args.prompt,
        strength=args.strength,
        steps=args.steps,
        seed=args.seed
    )

    if result['status'] == 'success':
        print(f"\n笨・謌仙粥!")
        print(f"  刀 霎灘・: {result['output_path']}")
        print(f"  竢ｱ・・ 閠玲慮: {result['generation_time']}")
        print(f"  搭 蜿よ焚:")
        for key, value in result['parameters'].items():
            print(f"    {key}: {value}")
    else:
        print(f"\n笶・螟ｱ雍･: {result.get('error', '譛ｪ遏･髞呵ｯｯ')}")