# skills/image/photo_restorer/skill.py
"""
老照片修复工具 Skill - 使用AI技术修复、上色、增强老照片
基于 ControlNet 进行图像修复和增强
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
    from PIL import Image, ImageEnhance, ImageFilter
    import numpy as np
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

# ==================== 修复模式配置 ====================
RESTORE_MODES = {
    "repair": {
        "prompt": "restored photo, repaired, clear, sharp, high quality, detailed, masterpiece",
        "negative": "ugly, deformed, blurry, low quality, damaged, scratched, faded, torn"
    },
    "colorize": {
        "prompt": "colorized photo, vibrant colors, natural, clear, high quality, detailed, masterpiece",
        "negative": "ugly, deformed, blurry, low quality, black and white, faded"
    },
    "enhance": {
        "prompt": "enhanced photo, sharp, vivid, clear, high quality, detailed, masterpiece",
        "negative": "ugly, deformed, blurry, low quality, faded, damaged"
    }
}


class PhotoRestorer:
    """老照片修复工具 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_restorer"
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

        logger.info(f"PhotoRestorer v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  修复模式: {list(RESTORE_MODES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 35,
            'default_strength': 0.5,
            'default_mode': 'repair',
            'default_negative': 'ugly, deformed, blurry, low quality, damaged, scratched, faded, torn',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_modes(self) -> Dict[str, Any]:
        """列出所有可用修复模式"""
        return {"status": "success", "modes": list(RESTORE_MODES.keys())}

    def _enhance_image(self, image_path: str, output_path: str) -> str:
        """增强图像质量"""
        try:
            img = Image.open(image_path)

            # 锐化
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.15)

            # 对比度增强
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)

            # 色彩增强
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.05)

            img.save(output_path, quality=95)
            return output_path
        except Exception as e:
            logger.warning(f"  图像增强失败: {e}")
            return image_path

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

            # ==================== 获取修复模式 ====================
            mode = kwargs.get('mode', self.config.get('default_mode', 'repair'))
            if mode not in RESTORE_MODES:
                return {"status": "error", "error": f"未知模式: {mode}，可用: {list(RESTORE_MODES.keys())}"}

            mode_config = RESTORE_MODES[mode]
            prompt = kwargs.get('prompt') or mode_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or mode_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.5))
            steps = kwargs.get('steps', self.config.get('default_steps', 35))
            seed = kwargs.get('seed', -1)

            # ==================== 默认输出路径 ====================
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_restored_{mode}_{timestamp}.png")

            # ==================== 调用底层 ControlNet 引擎 ====================
            if self._controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            logger.info(f"修复模式: {mode}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用 Canny 保持边缘结构
            result = self._controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",          # 提取边缘轮廓
                controlnet_model="canny",         # 保持边缘结构
                strength=strength,
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            final_path = result.get('image_path', output_path)

            # ==================== 增强图像 ====================
            if kwargs.get('enhance', True):
                final_path = self._enhance_image(final_path, final_path)
                logger.info("  ✅ 图像增强已应用")

            return {
                "status": "success",
                "output_path": final_path,
                "mode": mode,
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
        return f"<PhotoRestorer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="老照片修复工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入老照片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--mode", "-m", default="repair",
                        choices=list(RESTORE_MODES.keys()), help="修复模式")
    parser.add_argument("--strength", type=float, default=0.5, help="重绘强度 (0-1)")
    parser.add_argument("--steps", type=int, default=35, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--no-enhance", action="store_true", help="不增强图像")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = PhotoRestorer(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        mode=args.mode,
        strength=args.strength, steps=args.steps, seed=args.seed,
        enhance=not args.no_enhance
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))