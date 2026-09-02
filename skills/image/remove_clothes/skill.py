# skills/image/remove_clothes/skill.py
"""
移除衣服 Skill - 使用 SD Inpaint 移除图片中的衣服
支持 YOLO 自动检测或手动绘制遮罩
"""

import os
import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)

try:
    import torch
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"依赖库未安装: {e}")

try:
    from skills.image.controlnet_img2img.skill import ControlnetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"ControlNet 引擎不可用: {e}")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 未安装")


class ClothesRemover:
    """移除衣服技能"""

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
    SEGMENTATION_METHODS = ['yolo', 'manual']

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "remove_clothes"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.auto_resize = self.config.get('auto_resize', True)
        self.min_size = self.config.get('min_size', 512)
        self.max_size = self.config.get('max_size', 1024)
        self.default_seg_method = self.config.get('default_seg_method', 'yolo')

        self.pipeline = None
        self.current_model = None
        self._yolo_model = None
        self.controlnet_engine = None

        if self.config.get('use_controlnet', True) and CONTROLNET_ENGINE_AVAILABLE:
            try:
                from skills.image.controlnet_img2img.skill import ControlnetImg2Img
                self.controlnet_engine = ControlnetImg2Img(config={'device': self.device})
                logger.info("  ✅ ControlNet 引擎初始化成功")
            except Exception as e:
                logger.warning(f"  引擎初始化失败: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ClothesRemover v{self.version} 初始化完成")
        logger.info(f"  模型目录: {self.models_dir}")
        logger.info(f"  设备: {self.device}")
        logger.info(f"  ControlNet: {'可用' if self.controlnet_engine else '不可用'}")
        logger.info(f"  YOLO: {'可用' if YOLO_AVAILABLE else '不可用'}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 25,
            'default_strength': 0.5,
            'use_controlnet': True,
            'default_controlnet_type': 'canny',
            'default_seg_method': 'yolo',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config.get('output_dir', str(self.skill_dir / 'output'))).mkdir(parents=True, exist_ok=True)

    def _find_model(self, model_name: str) -> Optional[Path]:
        if not model_name:
            model_name = self.config.get('default_model', 'zenityXmix.inpainting.safetensors')
        direct_path = self.models_dir / model_name
        if direct_path.exists():
            return direct_path

        filename = os.path.basename(model_name)
        for subdir in ['sd-v1-5', 'sdxl']:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                return sub_path

        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    return file_path
        logger.error(f"找不到模型: {model_name}")
        return None

    def _load_pipeline(self, model_path: Path) -> bool:
        try:
            self.pipeline = StableDiffusionInpaintPipeline.from_single_file(
                str(model_path),
                torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32,
                safety_checker=None,
                requires_safety_checker=False,
            )
            self.pipeline.to(self.device)
            self.pipeline.enable_attention_slicing()
            self.current_model = model_path.name
            logger.info(f"  ✅ Inpaint 模型加载成功: {self.current_model}")
            return True
        except Exception as e:
            logger.error(f"  ❌ Inpaint 模型加载失败: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 未安装")
            return False
        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"找不到模型: {model_name}")
            return False
        return self._load_pipeline(model_path)

    def _get_yolo_model(self):
        if not YOLO_AVAILABLE:
            return None
        if self._yolo_model is None:
            try:
                self._yolo_model = YOLO("yolov8n-seg.pt")
            except Exception as e:
                logger.warning(f"  YOLO 初始化失败: {e}")
                self._yolo_model = False
        return self._yolo_model

    def _generate_mask_auto(self, image: Image.Image) -> Optional[Image.Image]:
        if not YOLO_AVAILABLE:
            return None
        h, w = image.size[1], image.size[0]
        yolo = self._get_yolo_model()
        if not yolo:
            return None
        try:
            results = yolo(image, verbose=False)
            if len(results) == 0 or results[0].masks is None:
                return None
            masks = results[0].masks.data.cpu().numpy()
            combined = np.zeros((h, w), dtype=np.uint8)
            for m in masks:
                m_resized = cv2.resize(m, (w, h))
                combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)
            coords = np.where(combined > 0)
            if len(coords[0]) == 0:
                return None
            y_min, y_max = coords[0].min(), coords[0].max()
            body_h = y_max - y_min
            neck = y_min + int(body_h * 0.18)
            hip = y_min + int(body_h * 0.70)
            x_min, x_max = coords[1].min(), coords[1].max()
            body_w = x_max - x_min
            left = x_min + int(body_w * 0.08)
            right = x_max - int(body_w * 0.08)
            clothes = np.zeros_like(combined)
            clothes[neck:hip, left:right] = combined[neck:hip, left:right]
            kernel = np.ones((5, 5), np.uint8)
            clothes = cv2.dilate(clothes, kernel, iterations=1)
            clothes = cv2.GaussianBlur(clothes, (9, 9), 0)
            if np.sum(clothes > 0) < 100:
                return None
            return Image.fromarray(clothes, mode="L")
        except Exception as e:
            logger.warning(f"  YOLO 生成遮罩失败: {e}")
            return None

    def _generate_mask_manual(self, image: Image.Image) -> Image.Image:
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w), dtype=np.uint8)
        drawing = False
        brush_size = 30

        print("\n" + "=" * 50)
        print("手动绘制遮罩模式")
        print("=" * 50)
        print("  左键拖动绘制遮罩（绿色区域）")
        print("  滚轮调整画笔大小")
        print("  R 键清除重画")
        print("  Q 键完成")
        print("=" * 50 + "\n")

        def draw_callback(event, x, y, flags, param):
            nonlocal drawing, brush_size
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
                cv2.circle(mask, (x, y), brush_size, 255, -1)
                cv2.circle(overlay, (x, y), brush_size, (0, 255, 0), -1)
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing:
                    cv2.circle(mask, (x, y), brush_size, 255, -1)
                    cv2.circle(overlay, (x, y), brush_size, (0, 255, 0), -1)
            elif event == cv2.EVENT_LBUTTONUP:
                drawing = False
            elif event == cv2.EVENT_MOUSEWHEEL:
                delta = flags
                brush_size = min(100, max(5, brush_size + (5 if delta > 0 else -5)))
                print(f"   画笔大小: {brush_size}")

        cv2.namedWindow('Draw Mask - Remove Clothes')
        cv2.setMouseCallback('Draw Mask - Remove Clothes', draw_callback)

        while True:
            display = img_cv.copy()
            mask_overlay = cv2.addWeighted(display, 0.5, overlay, 0.5, 0)
            cv2.putText(mask_overlay, f"Brush: {brush_size}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(mask_overlay, "Draw clothes, press Q to finish", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.imshow('Draw Mask - Remove Clothes', mask_overlay)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 32:
                break
            elif key == ord('r'):
                mask = np.zeros((h, w), dtype=np.uint8)
                overlay = np.zeros((h, w, 3), dtype=np.uint8)

        cv2.destroyAllWindows()

        if np.sum(mask > 0) < 100:
            print("  遮罩区域太小，使用默认中心区域")
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = w // 2, h // 2
            cv2.ellipse(mask, (cx, cy), (w // 4, h // 3), 0, 0, 360, 255, -1)

        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        return Image.fromarray(mask, mode="L")

    def _generate_mask(self, image: Image.Image, method: str = None, **kwargs) -> Image.Image:
        method = method or self.default_seg_method
        logger.info(f"  遮罩生成方法: {method}")

        if method == 'yolo':
            mask = self._generate_mask_auto(image)
            if mask is not None:
                return mask
            logger.info("  YOLO 失败，切换到手动模式")
            return self._generate_mask_manual(image)
        elif method == 'manual':
            return self._generate_mask_manual(image)
        else:
            logger.warning(f"  未知方法: {method}，使用 YOLO")
            mask = self._generate_mask_auto(image)
            if mask is not None:
                return mask
            return self._generate_mask_manual(image)

    def _resize_image(self, image: Image.Image) -> tuple:
        if not self.auto_resize:
            return image, image.size

        original_size = image.size
        need_resize = False
        new_size = original_size

        if min(original_size) < self.min_size:
            ratio = self.min_size / min(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            need_resize = True
        elif max(original_size) > self.max_size:
            ratio = self.max_size / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            need_resize = True

        if need_resize:
            logger.info(f"  调整尺寸: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            original_size = new_size

        width = (original_size[0] // 8) * 8
        height = (original_size[1] // 8) * 8
        if width != original_size[0] or height != original_size[1]:
            new_image = Image.new("RGB", (width, height), (0, 0, 0))
            x_offset = (width - original_size[0]) // 2
            y_offset = (height - original_size[1]) // 2
            new_image.paste(image, (x_offset, y_offset))
            image = new_image

        return image, image.size

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")

        try:
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 是必填参数"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"输入图片不存在: {abs_image_path}"}

            output_path = kwargs.get('output_path')
            model_name = kwargs.get('model_name')
            seg_method = kwargs.get('seg_method', self.default_seg_method)
            controlnet_type = kwargs.get('controlnet_type', self.config.get('default_controlnet_type', 'canny'))
            use_controlnet = kwargs.get('use_controlnet', self.config.get('use_controlnet', True))

            prompt = kwargs.get('prompt') or 'nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic'
            negative_prompt = kwargs.get('negative_prompt') or 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime'
            strength = kwargs.get('strength', self.config.get('default_strength', 0.5))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)
            save_mask = kwargs.get('save_mask', False)

            image = Image.open(abs_image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info("生成遮罩...")
            mask = self._generate_mask(image, method=seg_method)

            if save_mask:
                mask_path = str(abs_image_path).replace('.png', '_mask.png').replace('.jpg', '_mask.png')
                mask.save(mask_path)

            # 尝试使用 ControlNet
            if use_controlnet and self.controlnet_engine is not None:
                logger.info("  尝试使用 ControlNet 引擎...")

                if output_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_remove_{timestamp}.png")

                result = self.controlnet_engine.execute(
                    input_image_path=str(abs_image_path),
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    preprocessor_type=controlnet_type.upper(),
                    controlnet_model=controlnet_type,
                    strength=strength,
                    output_path=output_path
                )

                if result['status'] == 'success':
                    return {
                        "status": "success",
                        "output_path": result.get('image_path', output_path),
                        "parameters": {
                            "image_path": str(abs_image_path),
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "strength": strength,
                            "steps": steps,
                            "seed": seed,
                            "device": self.device,
                            "seg_method": seg_method,
                            "controlnet": True,
                            "controlnet_type": controlnet_type
                        },
                        "generation_time": f"{time.time() - start_time:.2f}s"
                    }
                else:
                    logger.warning(f"  ControlNet 失败，回退到 Inpaint")

            # 回退到 Inpaint
            if not self.pipeline:
                model_name = model_name or self.config.get('default_model')
                if not self._load_model(model_name):
                    return {"status": "error", "error": f"加载模型失败: {model_name}"}

            if seed == -1:
                seed = random.randint(0, 2 ** 32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_remove_{timestamp}.png")

            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=image,
                mask_image=mask,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=7.5,
                generator=generator,
            ).images[0]
            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "parameters": {"seg_method": seg_method, "controlnet": False},
                "generation_time": f"{time.time() - start_time:.2f}s"
            }

        except Exception as e:
            logger.error(f"执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ClothesRemover(name={self.name}, version={self.version})>"