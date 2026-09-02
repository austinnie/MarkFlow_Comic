# skills/change_expression/skill.py
"""
謾ｹ蜿倩｡ｨ諠・Skill - 謾ｹ蜿倅ｺｺ迚ｩ陦ｨ諠・ｼ亥ｾｮ隨・逕滓ｰ・諠願ｮｶ/謔ｲ莨､遲会ｼ会ｼ御ｿ晄戟莠ｺ迚ｩ髟ｿ逶ｸ扈晏ｯｹ荳榊序
螟咲畑騾夂畑 ControlNet 蠑墓梼・・ED + Lineart 髞∵ｭｻ莠泌ｮ假ｼ檎ｲｾ蜃・ｰ・｡ｨ諠・ｼ・
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

EXPRESSION_PROMPTS = {
    "smile": {
        "prompt": "smiling face, happy expression, cheerful, beautiful smile, teeth showing, masterpiece, high quality",
        "negative": "frowning, angry, sad, serious, neutral"
    },
    "angry": {
        "prompt": "angry face, fierce expression, furious, intense, angry eyes, masterpiece, high quality",
        "negative": "smiling, happy, sad, neutral, calm"
    },
    "sad": {
        "prompt": "sad face, melancholic expression, teary eyes, sorrowful, masterpiece, high quality",
        "negative": "smiling, happy, angry, neutral, cheerful"
    },
    "surprised": {
        "prompt": "surprised face, shocked expression, wide eyes, mouth open, amazed, masterpiece, high quality",
        "negative": "smiling, angry, sad, neutral, calm"
    },
    "serious": {
        "prompt": "serious face, neutral expression, focused, professional, calm, masterpiece, high quality",
        "negative": "smiling, angry, sad, surprised, laughing"
    },
    "laughing": {
        "prompt": "laughing face, joyful expression, laughing happily, cheerful, masterpiece, high quality",
        "negative": "angry, sad, serious, neutral, frowning"
    },
    "crying": {
        "prompt": "crying face, tears, emotional, sad expression, weeping, masterpiece, high quality",
        "negative": "smiling, happy, angry, neutral, cheerful"
    },
    "flirty": {
        "prompt": "flirty expression, playful smile, winking, charming, confident, masterpiece, high quality",
        "negative": "angry, sad, serious, neutral, frowning"
    }
}


class ChangeExpression:
    """謾ｹ蜿倩｡ｨ諠・橿閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_expression"
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

        logger.info(f"ChangeExpression v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  陦ｨ諠・ｱｻ蝙・ {list(EXPRESSION_PROMPTS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.45,  # 謾ｹ蜿倩｡ｨ諠・ｼｺ蠎ｦ荳崎・螟ｪ鬮假ｼ悟凄蛻吩ｼ壼序謌仙嘗荳荳ｪ莠ｺ
            'default_expression': 'smile',
            'default_negative': 'ugly, deformed, bad anatomy, blurry, low quality, extra limbs',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_expressions(self) -> Dict[str, Any]:
        return {"status": "success", "expressions": list(EXPRESSION_PROMPTS.keys())}

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

            expression = kwargs.get('expression', self.config.get('default_expression', 'smile'))
            if expression not in EXPRESSION_PROMPTS:
                return {"status": "error", "error": f"譛ｪ遏･陦ｨ諠・ {expression}・悟庄逕ｨ: {list(EXPRESSION_PROMPTS.keys())}"}

            expr_config = EXPRESSION_PROMPTS[expression]
            prompt = kwargs.get('prompt') or expr_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or expr_config.get('negative', self.config.get('default_negative'))

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
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_expr_{expression}_{timestamp}.png")

            logger.info(f"陦ｨ諠・ {expression}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            # 菴ｿ逕ｨ HED + Lineart 螳檎ｾ朱煤豁ｻ莠泌ｮ・
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
                "expression": expression,
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
        return f"<ChangeExpression(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="謾ｹ蜿倩｡ｨ諠・ｷ･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--expression", "-e", default="smile",
                        choices=list(EXPRESSION_PROMPTS.keys()), help="陦ｨ諠・ｱｻ蝙・)
    parser.add_argument("--strength", type=float, default=0.45, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeExpression(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        expression=args.expression,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))