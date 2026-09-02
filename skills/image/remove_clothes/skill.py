# markflow/skills/remove_clothes/skill.py
"""
è¡£æç§»é¤ Skill - ä½¿ç¨æ¬å° SD Inpaint æ¨¡åE
æ¯æEYOLO / Manual åE²Eå¤ç¨éç¨ ControlNet å¼æ
ControlNet åEInpaint åE¦»æ§è¡E
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

# ==================== ä¾èµå¯¼å¥ ====================
try:
    import torch
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"ä¾èµæªå®è£E {e}")

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
    logger.info("éç¨ ControlNet å¼æå è½½æå")
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# ==================== åE²æ¨¡åï¼é²å¾¡æ§å¯¼å¥EE====================
try:
    from .segmentation import (
        segment_with_yolo,
        segment_manual,
        segment_with_clipseg,
        segment_with_sam,
        segment_with_grounding_dino,
    )
    SEGMENTATION_AVAILABLE = True
except ImportError:
    SEGMENTATION_AVAILABLE = False
    logger.warning("æ¬å° segmentation æ¨¡åæªæ¾å°Eå°E½¿ç¨åE½®ç®åç YOLO ææå¨")

# YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO æªå®è£E¼å°E½¿ç¨æå¨é®ç½©")

class ClothesRemover:
    """è¡£æç§»é¤æè½"""

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
    SEGMENTATION_METHODS = ['yolo', 'manual', 'clipseg', 'sam', 'grounding_dino']

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "remove_clothes"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
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

        # ==================== å¼åEéç¨å¼æ ====================
        self.controlnet_engine = None
        if self.config.get('use_controlnet', True) and CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEéç¨ä¿å½¢å¼æ (controlnet_img2img) åå§åæå")
            except Exception as e:
                logger.warning(f"  âEéç¨ä¿å½¢å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ClothesRemover v{self.version} åå§åå®æE")
        logger.info(f"  æ¨¡åç®å½E {self.models_dir}")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  ControlNet å¼æ: {'âEå¯ç¨' if self.controlnet_engine else 'âEä¸å¯ç¨'}")
        logger.info(f"  YOLO: {'âEå¯ç¨' if YOLO_AVAILABLE else 'âEä¸å¯ç¨'}")

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

    # ==================== æ¨¡åç®¡çE====================
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
        logger.error(f"æªæ¾å°æ¨¡åE {model_name}")
        return None

    def _load_pipeline(self, model_path: Path) -> bool:
        """å è½½çº¯ SD Inpaint PipelineEå¤E¨è·¯çº¿EE""
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
            logger.info(f"  âEInpaint æ¨¡åå è½½æå: {self.current_model}")
            return True
        except Exception as e:
            logger.error(f"  âEInpaint æ¨¡åå è½½å¤±è´¥: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers æªå®è£E)
            return False
        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"æ¨¡åæä»¶ä¸å­å¨: {model_name}")
            return False
        return self._load_pipeline(model_path)

    def _load_model_from_path(self, model_path: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers æªå®è£E)
            return False
        if not os.path.exists(model_path):
            logger.error(f"æ¨¡åä¸å­å¨: {model_path}")
            return False
        return self._load_pipeline(Path(model_path))

    # ==================== é®ç½©çæE ====================
    def _get_yolo_model(self):
        if not YOLO_AVAILABLE:
            return None
        if self._yolo_model is None:
            try:
                self._yolo_model = YOLO("yolov8n-seg.pt")
            except Exception as e:
                logger.warning(f"  YOLO å è½½å¤±è´¥: {e}")
                self._yolo_model = False
        return self._yolo_model

    def _generate_mask_auto(self, image: Image.Image) -> Optional[Image.Image]:
        if not YOLO_AVAILABLE: return None
        h, w = image.size[1], image.size[0]
        yolo = self._get_yolo_model()
        if not yolo: return None
        try:
            results = yolo(image, verbose=False)
            if len(results) == 0 or results[0].masks is None: return None
            masks = results[0].masks.data.cpu().numpy()
            combined = np.zeros((h, w), dtype=np.uint8)
            for m in masks:
                m_resized = cv2.resize(m, (w, h))
                combined = np.maximum(combined, (m_resized > 0.5).astype(np.uint8) * 255)
            coords = np.where(combined > 0)
            if len(coords[0]) == 0: return None
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
            if np.sum(clothes > 0) < 100: return None
            return Image.fromarray(clothes, mode="L")
        except Exception as e:
            logger.warning(f"  YOLO åE²å¤±è´¥: {e}")
            return None

    def _generate_mask_manual(self, image: Image.Image) -> Image.Image:
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w), dtype=np.uint8)
        drawing = False
        brush_size = 30
        print("\n" + "=" * 50)
        print("æå¨ç»å¶é®ç½©æ¨¡å¼E)
        print("=" * 50)
        print("  æä½é¼ æ E·¦é®ç»å¶é®ç½©Eç½è²åºåï¼E)
        print("  æ»è½®è°Eç»ç¬å¤§å°E)
        print("  æER é®éç½®é®ç½©")
        print("  æEQ æEç©ºæ ¼é® å®æEç»å¶")
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
                print(f"   ç»ç¬å¤§å°E {brush_size}")
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
            print("  é®ç½©åºåå¤ªå°ï¼ä½¿ç¨æ¤­åE»è®¤é®ç½©")
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = w // 2, h // 2
            cv2.ellipse(mask, (cx, cy), (w // 4, h // 3), 0, 0, 360, 255, -1)
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        return Image.fromarray(mask, mode="L")

    def _generate_mask(self, image: Image.Image, method: str = None, **kwargs) -> Image.Image:
        method = method or self.default_seg_method
        logger.info(f"  ä½¿ç¨åE²æ¹æ³E {method}")
        if method == 'yolo':
            mask = self._generate_mask_auto(image)
            if mask is not None:
                return mask
            logger.info("  YOLO å¤±è´¥Eéçº§å°æå¨ç»å¶")
            return self._generate_mask_manual(image)
        elif method == 'manual':
            return self._generate_mask_manual(image)
        else:
            # ç®åéçº§
            logger.warning(f"  æä¸æ¯æE«çº§åE²æ¹æ³E {method}Eä½¿ç¨ YOLO ææå¨")
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
            logger.info(f"  ç­æ¯ä¾ç¼©æ¾: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
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
        logger.info(f"æ§è¡æè½: {self.name} (v{self.version})")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            output_path = kwargs.get('output_path')
            model_path = kwargs.get('model_path')
            model_name = kwargs.get('model_name')
            seg_method = kwargs.get('seg_method', self.default_seg_method)
            controlnet_type = kwargs.get('controlnet_type', self.config.get('default_controlnet_type', 'canny'))
            use_controlnet = kwargs.get('use_controlnet', self.config.get('use_controlnet', True))

            # è·ååæ°
            prompt = kwargs.get('prompt') or 'nude body, beautiful skin, realistic skin texture, natural light, soft shadows, masterpiece, best quality, photorealistic'
            negative_prompt = kwargs.get('negative_prompt') or 'clothes, fabric, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime'
            strength = kwargs.get('strength', self.config.get('default_strength', 0.5))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)
            save_mask = kwargs.get('save_mask', False)

            # å è½½å¾çE
            image = Image.open(abs_image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            # çæEé®ç½©
            logger.info("çæEé®ç½©...")
            mask = self._generate_mask(image, method=seg_method)

            if save_mask:
                mask_path = str(abs_image_path).replace('.png', '_mask.png').replace('.jpg', '_mask.png')
                mask.save(mask_path)

            # ==================== æ ¸å¿E¼å¼æè°E¨ ====================
            # å¦æå¯ç¨äºEControlNet å¼æEå¹¶ä¸å¼æå¯ç¨
            if use_controlnet and self.controlnet_engine is not None:
                logger.info("  ð¥ ä½¿ç¨éç¨ ControlNet å¼æè¿è¡çæE..")
                
                # é»è®¤è¾åEå°æ¬æè½ç®å½E
                if output_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_remove_{timestamp}.png")

                result = self.controlnet_engine.execute(
                    input_image_path=str(abs_image_path),
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    preprocessor_type=controlnet_type.upper(), # èªå¨æåå¯¹åºçå§¿æEçº¿ç¨¿
                    controlnet_model=controlnet_type,
                    strength=strength,  # ä¼ ç»å¼æ
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
                    # å¼æå¤±è´¥Eåé
                    logger.warning(f"  å¼æè°E¨å¤±è´¥: {result.get('error')}Eåéå°åEInpaint")
            
            # ==================== å¤E¨Eçº¯ Inpaint è·¯çº¿ ====================
            # å è½½ Inpaint æ¨¡åE
            if model_path:
                if not self._load_model_from_path(model_path):
                    return {"status": "error", "error": f"æ æ³å è½½æ¨¡åE {model_path}"}
            else:
                model_name = model_name or self.config.get('default_model')
                if self.pipeline is None or self.current_model != model_name:
                    if not self._load_model(model_name):
                        return {"status": "error", "error": f"æ æ³å è½½æ¨¡åE {model_name}"}

            if seed == -1:
                seed = random.randint(0, 2 ** 32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            # ç¡®ä¿è¾åEè·¯å¾E­å¨
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
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ClothesRemover(name={self.name}, version={self.version})>"