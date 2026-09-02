# markflow/skills/change_clothes/skill.py
"""
謐｢陦｣譛・Skill - 蟆・ｺｺ迚ｩ陦｣譛肴崛謐｢荳ｺ謖・ｮ壽ｬｾ蠑・
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    
import os
import time
import json
import random
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
import logging

logger = logging.getLogger(__name__)

# ==================== 萓晁ｵ門ｯｼ蜈･ ====================
try:
    import torch
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError as e:
    DIFFUSERS_AVAILABLE = False
    logger.warning(f"萓晁ｵ匁悴螳芽｣・ {e}")

# 蠑募・ controlnet_img2img 蠎募ｱよ橿閭ｽ菴應ｸｺ菫晏ｽ｢蠑墓梼
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
    logger.info("騾夂畑 ControlNet 蠑墓梼蜉霓ｽ謌仙粥")
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"騾夂畑 ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")

# YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO 譛ｪ螳芽｣・ｼ悟ｰ・ｽｿ逕ｨ謇句勘驕ｮ鄂ｩ")


# ==================== 謚閭ｽ邀ｻ ====================
class ChangeClothes:
    """謐｢陦｣譛肴橿閭ｽ - 蟆・ｺｺ迚ｩ陦｣譛肴崛謐｢荳ｺ謖・ｮ壽ｬｾ蠑・""

    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_clothes"
        self.version = "2.0.0"

        # 蠑ｺ蛻ｶ隶ｾ鄂ｮ譛ｬ謚閭ｽ霎灘・逶ｮ蠖・
        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        
        self.default_output_dir = self.skill_dir / "output"
        self.default_output_dir.mkdir(parents=True, exist_ok=True)

        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.auto_resize = self.config.get('auto_resize', True)
        self.min_size = self.config.get('min_size', 512)
        self.max_size = self.config.get('max_size', 1024)

        self.pipeline = None
        self.current_model = None
        self._yolo_model = None
        
        # ControlNet 蠎募ｱょｼ墓梼・域婿譯・・・
        self.controlnet_engine = None
        if self.config.get('use_controlnet', True) and CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  笨・騾夂畑菫晏ｽ｢蠑墓梼 (controlnet_img2img) 蛻晏ｧ句喧謌仙粥")
            except Exception as e:
                logger.warning(f"  笶・騾夂畑菫晏ｽ｢蠑墓梼蛻晏ｧ句喧螟ｱ雍･: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangeClothes 蛻晏ｧ句喧螳梧・")
        logger.info(f"  讓｡蝙狗岼蠖・ {self.models_dir}")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  ControlNet: {'笨・蜿ｯ逕ｨ' if self.controlnet_engine else '笶・荳榊庄逕ｨ'}")
        logger.info(f"  YOLO: {'笨・蜿ｯ逕ｨ' if YOLO_AVAILABLE else '笶・荳榊庄逕ｨ'}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.default_output_dir),
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 25,
            'default_strength': 0.6,
            'use_controlnet': True,
            'default_controlnet_type': 'openpose',
            'default_prompt': 'wearing a beautiful dress, elegant, fashionable, high quality, detailed, masterpiece',
            'default_negative': 'nude, naked, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

        Path(self.config.get('output_dir', str(self.skill_dir / 'output'))).mkdir(parents=True, exist_ok=True)

    # ==================== 讓｡蝙狗ｮ｡逅・====================
    def _find_model(self, model_name: str) -> Optional[Path]:
        if not model_name:
            model_name = self.config.get('default_model', 'zenityXmix.inpainting.safetensors')

        direct_path = self.models_dir / model_name
        if direct_path.exists():
            return direct_path

        filename = os.path.basename(model_name)
        subdirs = ['sd-v1-5', 'sdxl']
        for subdir in subdirs:
            sub_path = self.models_dir / subdir / filename
            if sub_path.exists():
                return sub_path

        for subdir in self.models_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    return file_path

        logger.error(f"譛ｪ謇ｾ蛻ｰ讓｡蝙・ '{model_name}'")
        return None

    def _load_pipeline(self, model_path: Path) -> bool:
        """蜉霓ｽ SD Inpaint Pipeline・亥､・畑霍ｯ郤ｿ・・""
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
            logger.info(f"  笨・Inpaint 讓｡蝙句刈霓ｽ謌仙粥: {self.current_model}")
            return True

        except Exception as e:
            logger.error(f"  笶・Inpaint 讓｡蝙句刈霓ｽ螟ｱ雍･: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 譛ｪ螳芽｣・)
            return False

        model_path = self._find_model(model_name)
        if not model_path:
            logger.error(f"讓｡蝙区枚莉ｶ荳榊ｭ伜惠: {model_name}")
            return False

        return self._load_pipeline(model_path)

    def _load_model_from_path(self, model_path: str) -> bool:
        if not DIFFUSERS_AVAILABLE:
            logger.error("diffusers 譛ｪ螳芽｣・)
            return False

        if not os.path.exists(model_path):
            logger.error(f"讓｡蝙倶ｸ榊ｭ伜惠: {model_path}")
            return False

        return self._load_pipeline(Path(model_path))

    # ==================== 驕ｮ鄂ｩ逕滓・ ====================
    def _get_yolo_model(self):
        if not YOLO_AVAILABLE:
            return None
        if self._yolo_model is None:
            try:
                self._yolo_model = YOLO("yolov8n-seg.pt")
            except Exception as e:
                logger.warning(f"  YOLO 蜉霓ｽ螟ｱ雍･: {e}")
                self._yolo_model = False
        return self._yolo_model

    def _generate_mask_auto(self, image: Image.Image) -> Optional[Image.Image]:
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
            logger.warning(f"  YOLO 蛻・牡螟ｱ雍･: {e}")
            return None

    def _generate_mask_manual(self, image: Image.Image) -> Image.Image:
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w), dtype=np.uint8)
        drawing = False
        brush_size = 30

        print("\n" + "=" * 50)
        print("謇句勘扈伜宛驕ｮ鄂ｩ讓｡蠑・)
        print("=" * 50)
        print("  謖我ｽ城ｼ譬・ｷｦ髞ｮ扈伜宛驕ｮ鄂ｩ・育區濶ｲ蛹ｺ蝓滂ｼ・)
        print("  貊夊ｽｮ隹・鰍逕ｻ隨泌､ｧ蟆・)
        print("  謖・R 髞ｮ驥咲ｽｮ驕ｮ鄂ｩ")
        print("  謖・Q 謌・遨ｺ譬ｼ髞ｮ 螳梧・扈伜宛")
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
                print(f"   逕ｻ隨泌､ｧ蟆・ {brush_size}")

        cv2.namedWindow('Draw Mask - Change Clothes')
        cv2.setMouseCallback('Draw Mask - Change Clothes', draw_callback)

        while True:
            display = img_cv.copy()
            mask_overlay = cv2.addWeighted(display, 0.5, overlay, 0.5, 0)
            cv2.putText(mask_overlay, f"Brush: {brush_size}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(mask_overlay, "Draw clothes, press Q to finish", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.imshow('Draw Mask - Change Clothes', mask_overlay)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 32:
                break
            elif key == ord('r'):
                mask = np.zeros((h, w), dtype=np.uint8)
                overlay = np.zeros((h, w, 3), dtype=np.uint8)
                print("  驕ｮ鄂ｩ蟾ｲ驥咲ｽｮ")

        cv2.destroyAllWindows()

        if np.sum(mask > 0) < 100:
            print("  驕ｮ鄂ｩ蛹ｺ蝓溷､ｪ蟆擾ｼ御ｽｿ逕ｨ讀ｭ蝨・ｻ倩ｮ､驕ｮ鄂ｩ")
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = w // 2, h // 2
            cv2.ellipse(mask, (cx, cy), (w // 4, h // 3), 0, 0, 360, 255, -1)

        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        print(f"  驕ｮ鄂ｩ螳梧・・瑚ｦ・尠 {np.sum(mask > 0)} 蜒冗ｴ")
        return Image.fromarray(mask, mode="L")

    def _generate_mask(self, image: Image.Image, use_manual: bool = False) -> Image.Image:
        if use_manual:
            return self._generate_mask_manual(image)

        mask = self._generate_mask_auto(image)
        if mask is not None:
            logger.info("  笨・菴ｿ逕ｨ YOLO 閾ｪ蜉ｨ驕ｮ鄂ｩ")
            return mask

        logger.info("  笞・・閾ｪ蜉ｨ驕ｮ鄂ｩ螟ｱ雍･・悟・謐｢蛻ｰ謇句勘扈伜宛")
        return self._generate_mask_manual(image)

    # ==================== ControlNet 蠑墓梼髮・・ ====================
    def _generate_pose_image(self, image: Image.Image, controlnet_type: str = "openpose") -> Optional[Image.Image]:
        """菴ｿ逕ｨ controlnet_img2img 蠎募ｱょｼ墓梼鬚・､・炊・域署蜿夜ｪｨ鬪ｼ/郤ｿ遞ｿ・会ｼ御ｸ肴ｶ牙所讓｡蝙句刈霓ｽ"""
        if self.controlnet_engine is None:
            return None

        try:
            logger.info(f"  笨・謠仙叙謗ｧ蛻ｶ迚ｹ蠕・({controlnet_type})...")
            control_image = self.controlnet_engine._preprocess(image, preprocessor_type=controlnet_type.upper())
            
            if control_image is not None:
                logger.info("  笨・謗ｧ蛻ｶ迚ｹ蠕∵署蜿門ｮ梧・")
                return control_image
            else:
                logger.warning("  笞・・謗ｧ蛻ｶ迚ｹ蠕∵署蜿門､ｱ雍･・檎ｻｧ扈ｭ菴ｿ逕ｨ譎ｮ騾・Inpaint")
                return None

        except Exception as e:
            logger.warning(f"  笞・・謗ｧ蛻ｶ迚ｹ蠕∵署蜿門ｼょｸｸ: {e}")
            return None

    # ==================== 蝗ｾ迚・｢・､・炊 ====================
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
            logger.info(f"  遲画ｯ比ｾ狗ｼｩ謾ｾ: {original_size[0]}x{original_size[1]} -> {new_size[0]}x{new_size[1]}")
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
            logger.info(f"  蝪ｫ蜈・ｯｹ鮨・ {original_size[0]}x{original_size[1]} -> {width}x{height}")
            original_size = (width, height)

        return image, original_size

    # ==================== 謇ｹ驥丞､・炊 ====================
    def batch_process(self, input_dir: str, output_dir: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        input_path = Path(input_dir)
        if not input_path.exists():
            return {"status": "error", "error": f"逶ｮ蠖穂ｸ榊ｭ伜惠: {input_dir}"}

        if output_dir is None:
            output_dir = input_path / "changed_output"
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        images = []
        for ext in self.SUPPORTED_EXTENSIONS:
            images.extend(input_path.glob(f"*{ext}"))
            images.extend(input_path.glob(f"*{ext.upper()}"))

        if not images:
            return {"status": "error", "error": f"譛ｪ謇ｾ蛻ｰ蝗ｾ迚・ {input_dir}"}

        logger.info(f"刀 謇ｾ蛻ｰ {len(images)} 荳ｪ蝗ｾ迚・)
        logger.info(f"唐 霎灘・逶ｮ蠖・ {output_dir}")

        results = []
        success_count = 0
        failed_count = 0

        for i, img_path in enumerate(images, 1):
            logger.info(f"\n[{i}/{len(images)}] {img_path.name}")
            output_file = output_path / img_path.name

            try:
                result = self.execute(image_path=str(img_path), output_path=str(output_file), **kwargs)
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
                results.append(result)
            except Exception as e:
                failed_count += 1
                results.append({"status": "error", "error": str(e), "image": str(img_path)})

        return {
            "status": "success" if success_count > 0 else "error",
            "total": len(images),
            "success": success_count,
            "failed": failed_count,
            "results": results,
            "output_dir": str(output_path)
        }

    # ==================== 荳ｻ謇ｧ陦梧婿豕・====================
    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name} (v{self.version})")

        try:
            # 1. 闔ｷ蜿門盾謨ｰ
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 譏ｯ蠢・｡ｫ蜿よ焚"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}縲りｯｷ譽譟･霍ｯ蠕・弍蜷ｦ豁｣遑ｮ・・}

            output_path = kwargs.get('output_path')
            model_path = kwargs.get('model_path')
            model_name = kwargs.get('model_name')
            manual_mask = kwargs.get('manual_mask', False)
            controlnet_type = kwargs.get('controlnet_type', self.config.get('default_controlnet_type', 'openpose'))
            use_controlnet = kwargs.get('use_controlnet', self.config.get('use_controlnet', True))

            # 2. 蜉霓ｽ Inpaint 讓｡蝙具ｼ亥､・畑霍ｯ郤ｿ・・
            if model_path:
                if not self._load_model_from_path(model_path):
                    return {"status": "error", "error": f"譌豕募刈霓ｽ讓｡蝙・ {model_path}"}
            else:
                model_name = model_name or self.config.get('default_model', 'zenityXmix.inpainting.safetensors')
                if self.pipeline is None or self.current_model != model_name:
                    if not self._load_model(model_name):
                        return {"status": "error", "error": f"譌豕募刈霓ｽ讓｡蝙・ {model_name}"}

            # 3. 闔ｷ蜿也函謌仙盾謨ｰ
            prompt = kwargs.get('prompt') if kwargs.get('prompt') is not None else self.config.get('default_prompt')
            negative_prompt = kwargs.get('negative_prompt') if kwargs.get('negative_prompt') is not None else self.config.get('default_negative')
            strength = kwargs.get('strength', self.config.get('default_strength', 0.6))
            steps = kwargs.get('steps', self.config.get('default_steps', 25))
            seed = kwargs.get('seed', -1)
            output_dir = kwargs.get('output_dir', self.config.get('output_dir'))
            save_mask = kwargs.get('save_mask', False)

            # 4. 蜉霓ｽ蟷ｶ郛ｩ謾ｾ蝗ｾ迚・
            image = Image.open(abs_image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"螟・炊: {os.path.basename(abs_image_path)} ({image.size[0]}x{image.size[1]})")
            logger.info(f"譛崎｣・緒霑ｰ: {prompt[:80]}...")

            # 5. 逕滓・驕ｮ鄂ｩ
            logger.info("逕滓・驕ｮ鄂ｩ...")
            mask = self._generate_mask(image, use_manual=manual_mask)

            if save_mask:
                mask_path = str(abs_image_path).replace('.png', '_mask.png').replace('.jpg', '_mask.png')
                mask.save(mask_path)
                logger.info(f"  驕ｮ鄂ｩ: {os.path.basename(mask_path)}")

            # 6. 逕滓・蟋ｿ諤∝崟・・ontrolNet・・
            control_image = None
            if use_controlnet and self.controlnet_engine is not None:
                logger.info(f"逕滓・蟋ｿ諤∝崟 (controlnet_type={controlnet_type})...")
                control_image = self._generate_pose_image(image, controlnet_type)
                if control_image is not None:
                    logger.info("  蟋ｿ諤∝崟逕滓・螳梧・")
                else:
                    logger.info("  蟋ｿ諤∝崟逕滓・螟ｱ雍･・檎ｻｧ扈ｭ菴ｿ逕ｨ譎ｮ騾・Inpaint")

            # 7. 隶ｾ鄂ｮ髫乗惻遘榊ｭ・
            if seed == -1:
                seed = random.randint(0, 2 ** 32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            logger.info("SD 逕滓・荳ｭ...")
            logger.info(f"  謠千､ｺ隸・ {prompt[:50]}...")
            logger.info(f"  豁･謨ｰ: {steps}")
            logger.info(f"  蠑ｺ蠎ｦ: {strength}")
            logger.info(f"  遘榊ｭ・ {seed}")
            if control_image is not None:
                logger.info("  ControlNet: 蟾ｲ蜷ｯ逕ｨ")

            # 8. 謇ｧ陦檎函謌・
            if control_image is not None:
                # 襍ｰ譁ｹ譯・・夊ｰ・畑騾夂畑逧・ControlNet 蝗ｾ逕溷崟蠑墓梼・育卆蛻・卆菫晏ｽ｢・・
                logger.info("  櫨 菴ｿ逕ｨ ControlNet 蝗ｾ逕溷崟蠑墓梼霑幄｡御ｿ晏ｽ｢驥咲ｻ・..")
                
                # 蛻帛ｻｺ荳荳ｪ荳ｴ譌ｶ菫晏ｭ倩ｷｯ蠕・ｼ亥・蜈･譛ｬ謚閭ｽ逶ｮ蠖包ｼ・
                tmp_output = str(self.default_output_dir / f"_tmp_{int(time.time())}.png")
                
                result = self.controlnet_engine.execute(
                    input_image_path=str(abs_image_path),  # 蠢・｡ｻ莨扈晏ｯｹ霍ｯ蠕・
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    preprocessor_type=controlnet_type.upper(),
                    controlnet_model="openpose",          # 逶ｴ謗･髞∝ｮ・openpose 蠎募ｱよｨ｡蝙・
                    strength=0.65,                        # 菫晏ｽ｢驥咲ｻ伜ｹ・ｺｦ
                    output_path=tmp_output
                )
                
                if result['status'] == 'success':
                    result = Image.open(result.get('image_path', tmp_output))
                else:
                    logger.warning(f"  蠑墓梼隹・畑螟ｱ雍･: {result.get('error')}・悟屓騾蛻ｰ蜴・Inpaint")
                    pipeline_kwargs = {
                        'prompt': prompt,
                        'negative_prompt': negative_prompt,
                        'image': image,
                        'mask_image': mask,
                        'strength': strength,
                        'num_inference_steps': steps,
                        'guidance_scale': 7.5,
                        'generator': generator,
                    }
                    result = self.pipeline(**pipeline_kwargs).images[0]
            else:
                # 螯よ棡豐｡譛牙庄逕ｨ逧・而蛻ｶ迚ｹ蠕・ｼ瑚ｵｰ蜴滓怏逧・ｱ驛ｨ驥咲ｻ倬ｻ霎・
                logger.info("  菴ｿ逕ｨ螻驛ｨ驥咲ｻ假ｼ・npaint・芽ｿ幄｡碁㍾扈・..")
                pipeline_kwargs = {
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'image': image,
                    'mask_image': mask,
                    'strength': strength,
                    'num_inference_steps': steps,
                    'guidance_scale': 7.5,
                    'generator': generator,
                }
                result = self.pipeline(**pipeline_kwargs).images[0]

            # 9. 菫晏ｭ倡ｻ捺棡
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{Path(abs_image_path).stem}_{timestamp}_changed.png"
                output_path = str(self.default_output_dir / filename)

            os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
            result.save(output_path)

            generation_time = time.time() - start_time
            logger.info(f"  菫晏ｭ・ {os.path.basename(output_path)}")

            return {
                "status": "success",
                "output_path": output_path,
                "parameters": {
                    "image_path": str(abs_image_path),
                    "model": self.current_model,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "strength": strength,
                    "steps": steps,
                    "seed": seed,
                    "device": self.device,
                    "controlnet": control_image is not None,
                    "controlnet_type": controlnet_type if control_image is not None else None,
                    "manual_mask": manual_mask
                },
                "model_used": self.current_model,
                "generation_time": f"{generation_time:.2f}s",
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }

    def __repr__(self):
        return f"<ChangeClothes(name={self.name}, version={self.version})>"


# ==================== 蜻ｽ莉､陦悟・蜿｣ ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="謐｢陦｣譛榊ｷ･蜈ｷ")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・・逶ｮ蠖・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・・逶ｮ蠖・)
    parser.add_argument("--batch", "-b", action="store_true", help="謇ｹ驥乗ｨ｡蠑・)
    parser.add_argument("--model", "-m", default="zenityXmix.inpainting.safetensors", help="讓｡蝙句錐遘ｰ")
    parser.add_argument("--prompt", "-p", default="wearing a beautiful dress, elegant, fashionable, high quality, detailed, masterpiece", help="譛崎｣・緒霑ｰ謠千､ｺ隸・)
    parser.add_argument("--negative", "-n", default="nude, naked, ugly, deformed, bad anatomy, extra limbs, missing limbs, bad proportions, blurry, low quality, cartoon, anime", help="雍滄擇謠千､ｺ隸・)
    parser.add_argument("--strength", "-s", type=float, default=0.6, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=25, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu", help="隶ｾ螟・)
    parser.add_argument("--save-mask", action="store_true", help="菫晏ｭ倬・鄂ｩ")
    parser.add_argument("--manual-mask", action="store_true", help="謇句勘扈伜宛驕ｮ鄂ｩ")
    parser.add_argument("--no-controlnet", action="store_true", help="遖∫畑 ControlNet")
    parser.add_argument("--controlnet-type", default="openpose",
                        choices=["canny", "openpose", "depth", "hed", "lineart", "normal", "mlsd", "openpose_full"],
                        help="ControlNet 邀ｻ蝙・)

    args = parser.parse_args()

    skill = ChangeClothes(config={
        'device': args.device,
        'use_controlnet': not args.no_controlnet,
        'default_controlnet_type': args.controlnet_type
    })

    if args.batch:
        result = skill.batch_process(
            input_dir=args.input,
            output_dir=args.output,
            model_name=args.model,
            prompt=args.prompt,
            negative_prompt=args.negative,
            strength=args.strength,
            steps=args.steps,
            seed=args.seed,
            save_mask=args.save_mask,
            manual_mask=args.manual_mask,
            controlnet_type=args.controlnet_type,
            use_controlnet=not args.no_controlnet
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = skill.execute(
            image_path=args.input,
            output_path=args.output,
            model_name=args.model,
            prompt=args.prompt,
            negative_prompt=args.negative,
            strength=args.strength,
            steps=args.steps,
            seed=args.seed,
            save_mask=args.save_mask,
            manual_mask=args.manual_mask,
            controlnet_type=args.controlnet_type,
            use_controlnet=not args.no_controlnet
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