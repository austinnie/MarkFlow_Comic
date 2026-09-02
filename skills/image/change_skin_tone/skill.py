# skills/change_skin_tone/skill.py
"""
æ¹åè¤è² Skill - æ¹åäººç©è¤è²Eç½çEå¤éEæ·±è²ç­ï¼E
ä¼åEä½¿ç¨ YOLO å®ä½ç®è¤åºåï¼å¤ç¨éç¨ ControlNet å¼æè¿è¡å±é¨/å¨å±éç»E
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
    from PIL import Image, ImageDraw, ImageFilter
    import cv2
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("torch æEOpenCV æªå®è£E)

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLO æªå®è£E)

SKIN_TONES = {
    "fair": {
        "prompt": "fair skin, pale skin, light complexion, beautiful, masterpiece, high quality",
        "negative": "dark skin, tan, brown, ugly, deformed"
    },
    "tan": {
        "prompt": "tan skin, sun-kissed, golden complexion, beautiful, masterpiece, high quality",
        "negative": "pale, fair, dark, ugly, deformed"
    },
    "dark": {
        "prompt": "dark skin, beautiful brown skin, rich complexion, beautiful, masterpiece, high quality",
        "negative": "fair, pale, tan, ugly, deformed"
    },
    "olive": {
        "prompt": "olive skin, warm complexion, Mediterranean, beautiful, masterpiece, high quality",
        "negative": "fair, pale, dark, ugly, deformed"
    },
    "warm": {
        "prompt": "warm skin tone, golden undertone, glowing skin, beautiful, masterpiece, high quality",
        "negative": "pale, cold, dark, ugly, deformed"
    }
}


class ChangeSkinTone:
    """æ¹åè¤è²æè½ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "change_skin_tone"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.pipeline = None
        self.current_model = None
        self._yolo_model = None

        # ==================== åå§ååºå±å¼æ ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±EControlNet å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ChangeSkinTone v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  è¤è²ç±»åE {list(SKIN_TONES.keys())}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_steps': 30,
            'default_strength': 0.45,  # æ¹åè¤è²ä¸èEå¤ªå¤§å¼ºåº¦Eä»¥åæ¹åäºå®E
            'default_tone': 'fair',
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

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

    def _generate_skin_mask(self, image: Image.Image) -> Optional[Image.Image]:
        """çæEç®è¤é®ç½©EEOLO å¨èº«EE""
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

            skin_mask = combined
            kernel = np.ones((10, 10), np.uint8)
            skin_mask = cv2.dilate(skin_mask, kernel, iterations=1)
            skin_mask = cv2.GaussianBlur(skin_mask, (15, 15), 0)

            if np.sum(skin_mask > 0) < 100:
                return None

            return Image.fromarray(skin_mask, mode="L")

        except Exception as e:
            logger.warning(f"  ç®è¤é®ç½©çæEå¤±è´¥: {e}")
            return None

    def list_tones(self) -> Dict[str, Any]:
        return {"status": "success", "tones": list(SKIN_TONES.keys())}

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"æ§è¡æè½: {self.name}")

        try:
            # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

            tone = kwargs.get('tone', self.config.get('default_tone', 'fair'))
            if tone not in SKIN_TONES:
                return {"status": "error", "error": f"æªç¥è¤è²: {tone}Eå¯ç¨: {list(SKIN_TONES.keys())}"}

            tone_config = SKIN_TONES[tone]
            prompt = kwargs.get('prompt') or tone_config['prompt']
            negative_prompt = kwargs.get('negative_prompt') or tone_config.get('negative', self.config.get('default_negative'))

            strength = kwargs.get('strength', self.config.get('default_strength', 0.45))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)

            # é»è®¤è¾åEå°æ¬æè½ç®å½E
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_skintone_{tone}_{timestamp}.png")

            # ==================== ç´æ¥è°E¨åºå±å¼æEåEå±EE====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            logger.info(f"è¤è²: {tone}")
            logger.info(f"æç¤ºè¯E {prompt[:80]}...")

            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="HED",      # ä¿çäºå®åèº«ä½è½®å»E
                controlnet_model="canny",     # å¯¹åºæ¬å°æ¨¡åE
                strength=strength,            # ä½å¼ºåº¦Eé¿åäºå®åå½¢
                steps=steps,
                output_path=output_path
            )

            if result['status'] != 'success':
                return result

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "tone": tone,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {
                    "strength": strength, 
                    "steps": steps, 
                    "seed": seed,
                    "controlnet": "canny"
                }
            }

        except Exception as e:
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<ChangeSkinTone(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="æ¹åè¤è²å·¥å· v2.0")
    parser.add_argument("--input", "-i", required=True, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)
    parser.add_argument("--tone", "-t", default="fair",
                        choices=list(SKIN_TONES.keys()), help="è¤è²ç±»åE)
    parser.add_argument("--strength", type=float, default=0.45, help="éç»å¼ºåº¦")
    parser.add_argument("--steps", type=int, default=30, help="è¿­ä»£æ­¥æ°")
    parser.add_argument("--seed", type=int, default=-1, help="éæºç§å­E)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ChangeSkinTone(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        tone=args.tone,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))