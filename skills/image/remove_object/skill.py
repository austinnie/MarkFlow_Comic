# skills/image/remove_object/skill.py
"""
移除物体 Skill - 从图片中移除不需要的物体，自动填充背景
使用 ControlNet Inpaint 进行物体移除
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
    from PIL import Image, ImageDraw
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

# ==================== 默认配置 ====================
DEFAULT_PROMPT = "background, natural, seamless, clean, empty, masterpiece, high quality"
DEFAULT_NEGATIVE = "ugly, deformed, blurry, low quality, object, person, animal, extra limbs"


class RemoveObject:
    """移除物体技能 v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "remove_object"
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

        logger.info(f"RemoveObject v{self.version} 初始化完成")
        logger.info(f"  设备: {self.device}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.7,
            'default_negative': DEFAULT_NEGATIVE,
            'auto_detect': False,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _create_manual_mask(self, image_path: str, object_prompt: str) -> Optional[str]:
        """
        创建手动遮罩（占位实现，实际使用时需要用户交互）
        这里返回 None 表示需要用户提供遮罩
        """
        logger.warning("  手动遮罩模式需要用户交互，请使用 --skip_manual 或提供 mask_path")
        return None

    def _auto_detect_mask(self, image_path: str) -> Optional[str]:
        """自动检测物体并生成遮罩（占位实现）"""
        logger.warning("  自动检测功能需要 YOLO 或 SAM 支持")
        return None

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

            # ==================== 获取参数 ====================
            skip_manual = kwargs.get('skip_manual', self.config.get('auto_detect', False))
            mask_path = kwargs.get('mask_path')
            object_prompt = kwargs.get('object_prompt', 'object to remove')

            prompt = kwargs.get('prompt') or DEFAULT_PROMPT
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # ==================== 处理遮罩 ====================
            final_mask_path = mask_path

            if final_mask_path is None and not skip_manual:
                # 需要手动遮罩
                return {
                    "status": "error",
                    "error": "需要手动创建遮罩，请使用 mask_path 参数提供遮罩，或设置 skip_manual=True 启用自动检测",
                    "hint": "mask_path: 遮罩图片路径（白色区域为要移除的物体）"
                }

            if final_mask_path is None and skip_manual:
                # 自动检测
                final_mask_path = self._auto_detect_mask(str(abs_image_path))
                if final_mask_path is None:
                    return {
                        "status": "error",
                        "error": "自动检测失败，请手动提供 mask_path 遮罩"
                    }
                logger.info(f"  ✅ 自动检测遮罩已生成: {final_mask_path}")

            # ==================== 默认输出路径 ====================
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_removed_{timestamp}.png")

            # ==================== 调用底层 ControlNet 引擎 ====================
            if self._controlnet_engine is None:
                return {"status": "error", "error": "ControlNet 引擎不可用"}

            logger.info(f"提示词: {prompt[:80]}...")
            logger.info(f"使用遮罩: {final_mask_path is not None}")

            # 使用 Inpaint 进行物体移除
            result = self._controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",          # 提取边缘轮廓
                controlnet_model="canny",         # 保持边缘结构
                strength=strength,
                steps=steps,
                output_path=output_path,
                mask_path=final_mask_path         # 传入遮罩
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "controlnet": "canny"
                },
                "mask_used": final_mask_path is not None
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<RemoveObject(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="移除物体工具 v2.0")
    parser.add_argument("--input", "-i", required=True, help="输入图片路径")
    parser.add_argument("--output", "-o", help="输出路径")
    parser.add_argument("--mask", "-m", help="遮罩图片路径（白色区域为要移除的物体）")
    parser.add_argument("--skip_manual", action="store_true", help="跳过手动遮罩，使用自动检测")
    parser.add_argument("--object", help="要移除的物体描述（用于自动检测）")
    parser.add_argument("--strength", type=float, default=0.7, help="重绘强度 (0-1)")
    parser.add_argument("--steps", type=int, default=30, help="迭代步数")
    parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = RemoveObject(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        mask_path=args.mask, skip_manual=args.skip_manual,
        object_prompt=args.object,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))