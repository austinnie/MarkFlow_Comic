# skills/image/fantasy_character/skill.py
"""
幻想角色生成 Skill - 将人物转换为幻想角色（精灵、矮人、兽人等）
使用 ControlNet OpenPose 保持人物姿态一致
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
    logger.warning("torch 或 PIL 未安装")

try:
    from skills.image.controlnet_img2img.skill import ControlnetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"ControlNet 引擎不可用: {e}")

# ==================== 幻想角色类型配置 ====================
FANTASY_TYPES = {
    "elf": {
        "prompt": "elf, pointed ears, elegant, mystical, beautiful, fantasy, magical aura, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    },
    "dwarf": {
        "prompt": "dwarf, short, sturdy, beard, warrior, fantasy, rugged, strong, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    },
    "orc": {
        "prompt": "orc, green skin, muscular, fierce, fantasy, warrior, tusks, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    },
    "fairy": {
        "prompt": "fairy, wings, magical, delicate, glowing, fantasy, ethereal, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    },
    "dragonborn": {
        "prompt": "dragonborn, scales, dragon features, reptilian, fantasy, warrior, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    },
    "angel": {
        "prompt": "angel, wings, halo, divine, ethereal, beautiful, fantasy, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    },
    "demon": {
        "prompt": "demon, horns, dark, fiery, fantasy, powerful, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    },
    "dark_elf": {
        "prompt": "dark elf, drow, dark skin, white hair, elegant, mysterious, fantasy, masterpiece, high quality",
        "negative": "ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality"
    }
}


class FantasyCharacter:
    """幻想角色生成技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "fantasy_character"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 强制本技能输出目录 ====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        # ==================== 初始化 ControlNet 引擎 ====================
        self._controlnet_engine = None

        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                from skills.image.controlnet_img2img.skill import ControlnetImg2Img
                self._controlnet_engine = ControlnetImg2Img(config={'device': self.device})
                logger.info("  ✅ ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"FantasyCharacter v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  角色类型: {list(FANTASY_TYPES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.6,
            'default_type': 'elf',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_types(self) -> Dict[str, Any]:
        """列出所有可用幻想角色类型"""
        return {"status": "success", "types": list(FANTASY_TYPES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name}")

        try:
            # ==================== 严格路径校验 ====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}。请检查路径是否正确！"}

            # ==================== 获取幻想角色类型 ====================
            fantasy_type = kwargs.get('fantasy_type', self.config.get('default_type', 'elf'))
            if fantasy_type not in FANTASY_TYPES:
                return {"status": "error", "error": f"未知角色类型: {fantasy_type}，可用: {list(FANTASY_TYPES.keys())}"}

            type_config = FANTASY_TYPES[fantasy_type]
            prompt = kwargs.get('prompt') or type_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or type_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.6))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 默认输出路径 ====================
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{fantasy_type}_{timestamp}.png")

            # ==================== 调用底层 ControlNet 引擎 ====================
            if self._controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            logger.info(f"幻想角色类型: {fantasy_type}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用 OpenPose 保持人物姿态
            result = self._controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",          # 提取边缘轮廓
                controlnet_model="openpose",      # 使用 OpenPose 保持姿态
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "fantasy_type": fantasy_type,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "controlnet": "openpose"
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<FantasyCharacter(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="幻想角色生成工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--type", "-t", default="elf",
                        choices=list(FANTASY_TYPES.keys()), help="幻想角色类型")
    parser.add_argument("--strength", type=float, default=0.6, help="重绘强度 (0-1)")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = FantasyCharacter(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        fantasy_type=args.type,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))