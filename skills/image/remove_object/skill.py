# skills/remove_object/skill.py
"""
çé¤ç©ä½ESkill - äå¾çE¸­çé¤æE®ç©ä½E
éè®¤ä½¿ç¨æå¨é®ç½©Eè¥é®ç½©çæEæåEåEå¤ç¨éç¨ ControlNet å¼æå¹¶éå Inpaint ååºE
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
    import numpy as np
    from PIL import Image
    import cv2
    from diffusers import StableDiffusionInpaintPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("diffusers æªå®è£E)

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")


class RemoveObject:
    """çé¤ç©ä½æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "remove_object"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.pipeline = None
        self.current_model = None

        # ==================== ååååºå±å¼æ ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±EControlNet å¼æåååæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåååå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"RemoveObject v{self.version} åååå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  åºå±å¼æ: {'âEå¯ç¨' if self.controlnet_engine else 'âEä¸å¯ç¨'}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.7,
            'default_prompt': 'clean background, empty, clear, masterpiece, high quality',
            'default_negative': 'ugly, deformed, blurry, low quality, object',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _find_model(self, model_name: str) -> Optional[Path]:
        return Path(self.models_dir / "sd-v1-5" / model_name) if model_name else None

    def _load_pipeline(self, model_path: Path) -> bool:
        """å è½½çº¯ Inpaint ç®¡çº¿Eä½ä¸ºååºï¼E""
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
            return True
        except Exception as e:
            logger.error(f"  æ¨¡åå è½½å¤±è´¥: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        model_path = self._find_model(model_name)
        if not model_path or not model_path.exists():
            logger.error(f"æ¨¡åä¸å­å¨: {model_name}")
            return False
        return self._load_pipeline(model_path)

    def _generate_manual_mask(self, image: Image.Image) -> Image.Image:
        """æå¨çå¶è¦çé¤çE©ä½éEç½©"""
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w), dtype=np.uint8)
        drawing = False
        brush_size = 30

        print("\n" + "=" * 50)
        print("æå¨çå¶è¦çé¤çE©ä½E)
        print("=" * 50)
        print("  æä½é¼ æ E·¦é®çå¶è¦çé¤çEºåï¼ç½è²EE)
        print("  æè½®è°Eçç¬å¤å°E)
        print("  æER é®éç½®")
        print("  æEQ æEç©ºæ ¼é® å®æE")
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
                print(f"   çç¬å¤å°E {brush_size}")

        cv2.namedWindow('Draw Object to Remove')
        cv2.setMouseCallback('Draw Object to Remove', draw_callback)

        while True:
            display = img_cv.copy()
            mask_overlay = cv2.addWeighted(display, 0.5, overlay, 0.5, 0)
            cv2.putText(mask_overlay, f"Brush: {brush_size}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(mask_overlay, "Draw object to remove, press Q to finish", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.imshow('Draw Object to Remove', mask_overlay)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 32:
                break
            elif key == ord('r'):
                mask = np.zeros((h, w), dtype=np.uint8)
                overlay = np.zeros((h, w, 3), dtype=np.uint8)
                print("  å·²éç½®")

        cv2.destroyAllWindows()

        if np.sum(mask > 0) < 100:
            print("  æªçå¶ää½åºåï¼ä½¿ç¨éè®¤æ¤­åEEç½©")
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = w // 2, h // 2
            cv2.ellipse(mask, (cx, cy), (w // 4, h // 4), 0, 0, 360, 255, -1)

        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        return Image.fromarray(mask, mode="L")

    def _resize_image(self, image: Image.Image) -> tuple:
        w, h = image.size
        max_size = 768
        if max(w, h) > max_size:
            ratio = max_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return image, image.size

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"æè¡æè½: {self.name}")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            prompt = kwargs.get('prompt') or self.config.get('default_prompt')
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))

            # å è½½åå¾
            image = Image.open(abs_image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            # ==================== ç¬¬ä¸æ­¥EçæéEç½© ====================
            # å¦æä½ å°E¥æ³è¦èEå¨åï¼è¿éå¯ä¥æ¥å¥ YOLO/SAMãE
            # ç®åä¸ºäºE¨³å®ï¼ç´æ¥è°E¨æå¨çå¶Eå¯ä¥ä¼  skip_manual=True è·³è¿E¼E
            if not kwargs.get('skip_manual', False):
                object_mask = self._generate_manual_mask(image)
            else:
                # å¦æè·³è¿Eå¨Eçæä¸ä¸ªå¨éçé®ç½©Eç­åäºåEå±éçï¼E
                object_mask = Image.new("L", image.size, 0)

            # éè®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_removed_{timestamp}.png")

            # ==================== ç¬¬äºæ­¥Eæè¡ï¼å¼æä¼åEEInpaintååºï¼E====================
            # å¦æåºå±å¼æå¯ç¨Eä¸ç¨æ·åè®¸Eè°E¨å¼æçæE
            if self.controlnet_engine is not None:
                logger.info("  ð¥ ä½¿ç¨éç¨ ControlNet å¼æè¿è¡çé¤Eä¿æåæçæEE..")
                result = self.controlnet_engine.execute(
                    input_image_path=str(abs_image_path),
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    preprocessor_type="HED",      # æåè½¯è¾¹ç¼ï¼ä¿çèæ¯
                    controlnet_model="canny",     # å¯¹åºæ¬å°æ¨¡åE
                    strength=strength,
                    output_path=output_path
                )
                if result['status'] == 'success':
                    return {
                        "status": "success",
                        "output_path": result.get('image_path', output_path),
                        "generation_time": f"{time.time() - start_time:.2f}s",
                        "parameters": {"strength": strength, "steps": steps, "seed": seed, "engine": "controlnet"}
                    }
                else:
                    logger.warning(f"  å¼æè°E¨å¤±è´¥: {result.get('error')}Eåéå° Inpaint")

            # ååºï¼å è½½çº¯ Inpaint æ¨¡åå¹¶çæE
            if not self._load_model(model_name):
                return {"status": "error", "error": f"æ æ³å è½½æ¨¡åE {model_name}"}

            if seed == -1:
                seed = random.randint(0, 2 ** 32 - 1)
            generator = torch.Generator(device=self.device).manual_seed(seed)

            current_size = image.size
            result = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=image,
                mask_image=object_mask,
                strength=strength,
                num_inference_steps=steps,
                guidance_scale=7.5,
                generator=generator,
                width=current_size[0],
                height=current_size[1],
            ).images[0]

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            result.save(output_path)

            return {
                "status": "success",
                "output_path": output_path,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {"strength": strength, "steps": steps, "seed": seed, "engine": "inpaint"}
            }

        except Exception as e:
            logger.error(f"æè¡å¤±è´¥: {e}")
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="çé¤ç©ä½å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--skip-manual", action="store_true", help="è·³è¿Eå¨çå¶é®ç½©")
    parser.add_argument("--strength", type=float, default=0.7, help="éçå¼ºåº¦")
    parser.add_argument("--steps", type=int, default=30, help="è¿­ä£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºçå­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = RemoveObject(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        skip_manual=args.skip_manual,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
"""