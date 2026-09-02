# skills/image/season_transfer/skill.py
"""
季节转换 Skill - 将图片转换为不同季节风格（春、夏、秋、冬）
使用 ControlNet 保持原图结构
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

# ==================== 季节配置 ====================
SEASON_MAP = {
    "spring": {
        "prompt": "spring season, cherry blossoms, blooming flowers, green grass, fresh, vibrant, masterpiece, high quality",
        "negative": "winter, snow, cold, autumn leaves, summer heat, dry"
    },
    "summer": {
        "prompt": "summer season, bright sunlight, green trees, blue sky, warm, vibrant, masterpiece, high quality",
        "negative": "winter, snow, cold, autumn leaves, spring flowers"
    },
    "autumn": {
        "prompt": "autumn season, golden leaves, orange and red foliage, warm tones, cozy, masterpiece, high quality",
        "negative": "winter, snow, cold, spring flowers, summer green"
    },
    "winter": {
        "prompt": "winter season, snow, white landscape, cold, serene, peaceful, masterpiece, high quality",
        "negative": "summer, spring, autumn, green, warm"
    }
}


class SeasonTransfer:
    """季节转换技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "season_transfer"
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

        logger.info(f"SeasonTransfer v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  季节: {list(SEASON_MAP.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.55,
            'default_season': 'spring',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_seasons(self) -> Dict[str, Any]:
        """列出所有可用季节"""
        return {"status": "success", "seasons": list(SEASON_MAP.keys())}

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

            # ==================== 获取季节 ====================
            season = kwargs.get('season', self.config.get('default_season', 'spring'))
            if season not in SEASON_MAP:
                return {"status": "error", "error": f"未知季节: {season}，可用: {list(SEASON_MAP.keys())}"}

            season_config = SEASON_MAP[season]
            prompt = kwargs.get('prompt') or season_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or season_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.55))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 默认输出路径 ====================
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_{season}_{timestamp}.png")

            # ==================== 调用底层 ControlNet 引擎 ====================
            if self._controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            logger.info(f"目标季节: {season}")
            logger.info(f"提示词: {prompt[:80]}...")

            result = self._controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",          # 提取边缘轮廓
                controlnet_model="canny",         # 保持结构
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "season": season,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "controlnet": "canny"
                }
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<SeasonTransfer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="季节转换工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--season", "-s", default="spring",
                        choices=list(SEASON_MAP.keys()), help="目标季节")
    parser.add_argument("--strength", type=float, default=0.55, help="重绘强度 (0-1)")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = SeasonTransfer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        season=args.season,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))