# skills/image/photo_realistic/skill.py
"""
照片写实化 Skill - 让 AI 图片看起来像真实相机照片
应用相机 EXIF 数据、色彩校正、噪点添加等效果
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

# ==================== 相机配置 ====================
CAMERA_PRESETS = {
    "canon": {
        "prompt": "canon camera photo, realistic, natural colors, sharp, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality, painting, cartoon, anime, digital art"
    },
    "nikon": {
        "prompt": "nikon camera photo, realistic, vibrant colors, sharp, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality, painting, cartoon, anime, digital art"
    },
    "sony": {
        "prompt": "sony camera photo, realistic, accurate colors, sharp, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality, painting, cartoon, anime, digital art"
    },
    "fujifilm": {
        "prompt": "fujifilm camera photo, film-like, warm colors, artistic, sharp, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality, painting, cartoon, anime, digital art"
    },
    "leica": {
        "prompt": "leica camera photo, cinematic, rich colors, sharp, detailed, masterpiece, high quality",
        "negative": "ugly, deformed, blurry, low quality, painting, cartoon, anime, digital art"
    }
}


class PhotoRealistic:
    """照片写实化技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_realistic"
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

        logger.info(f"PhotoRealistic v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  相机预设: {list(CAMERA_PRESETS.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 25,
            'default_strength': 0.35,
            'default_camera': 'canon',
            'default_negative': 'ugly, deformed, blurry, low quality, painting, cartoon, anime, digital art',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def list_cameras(self) -> Dict[str, Any]:
        """列出所有可用相机预设"""
        return {"status": "success", "cameras": list(CAMERA_PRESETS.keys())}

    def _add_photo_effects(self, image_path: str, output_path: str) -> str:
        """添加照片真实感效果（噪点、色彩校正等）"""
        try:
            img = Image.open(image_path)

            # 轻微锐化
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)

            # 轻微色彩增强
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.05)

            # 添加微弱的颗粒感
            if img.mode == 'RGB':
                arr = np.array(img)
                noise = np.random.normal(0, 2, arr.shape).astype(np.int16)
                arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
                img = Image.fromarray(arr)

            img.save(output_path, quality=95)
            return output_path
        except Exception as e:
            logger.warning(f"  照片效果添加失败: {e}")
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

            # ==================== 获取相机预设 ====================
            camera = kwargs.get('camera', self.config.get('default_camera', 'canon'))
            if camera not in CAMERA_PRESETS:
                return {"status": "error", "error": f"未知相机: {camera}，可用: {list(CAMERA_PRESETS.keys())}"}

            camera_config = CAMERA_PRESETS[camera]
            prompt = kwargs.get('prompt') or camera_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or camera_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.35))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)

            # ==================== 默认输出路径 ====================
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_realistic_{camera}_{timestamp}.png")

            # ==================== 调用底层 ControlNet 引擎 ====================
            if self._controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            logger.info(f"相机预设: {camera}")
            logger.info(f"提示词: {prompt[:80]}...")

            # 使用低强度保持原图，仅增强真实感
            result = self._controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",          # 提取边缘轮廓
                controlnet_model="canny",         # 保持边缘结构
                strength=strength,                # 低强度保持原图
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            final_path = result.get('image_path', output_path)

            # ==================== 添加照片效果 ====================
            if kwargs.get('apply_effects', True):
                final_path = self._add_photo_effects(final_path, final_path)
                logger.info("  ✅ 照片效果已应用")

            return {
                "status": "success",
                "output_path": final_path,
                "camera": camera,
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
        return f"<PhotoRealistic(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="照片写实化工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--camera", "-c", default="canon",
                        choices=list(CAMERA_PRESETS.keys()), help="相机预设")
    parser.add_argument("--strength", type=float, default=0.35, help="重绘强度 (0-1)")
    parser.add_argument("--steps", type=int, default=25, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--no-effects", action="store_true", help="不添加照片效果")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = PhotoRealistic(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        camera=args.camera,
        strength=args.strength, steps=args.steps, seed=args.seed,
        apply_effects=not args.no_effects
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))