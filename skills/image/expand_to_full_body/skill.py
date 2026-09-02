# skills/expand_to_full_body/skill.py
"""
Expand to Full Body - å°Eººç©åèº«/å¤´åå¾æ©å±ä¸ºå¨èº«å¾
å¤ç¨éç¨ ControlNet å¼æEä½¿ç¨ MediaPipe æEè½»éæ£æµå®ä½å¤´é¨
"""

import os
import sys
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
    import numpy as np
    from PIL import Image
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("torch æEPIL æªå®è£E)

# ==================== å¼åEéç¨å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")


class ExpandToFullBody:
    """åèº«å¾è½¬å¨èº«å¾æè½ v2.0 (MediaPipe + OpenPose éå§¿æE"""

    # å¯ç¨æ¨¡ååEè¡¨Eç¨äºå±ç¤ºEE
    AVAILABLE_MODELS = {
        "anytimeRealistic_v10.safetensors": {"name": "Anytime Realistic", "size": "2.13 GB", "type": "åå®E},
        "aiiiii01_v10.safetensors": {"name": "AIiiii v1.0", "size": "2.13 GB", "type": "åå®E},
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "expand_to_full_body"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.default_model = self.config.get('default_model', 'anytimeRealistic_v10.safetensors')
        self.default_steps = self.config.get('default_steps', 30)
        self.target_height = self.config.get('target_height', 1024)
        self.target_width = self.config.get('target_width', 768)

        # ç¼å­E
        self.controlnet_engine = None

        # ==================== åå§ååºå±å¼æ ====================
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  âEåºå±EControlNet å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        # ==================== åå§å MediaPipeEæ°çEAPIEE====================
        self._mediapipe_pose = None
        self._init_mediapipe()

        self._setup_logging()
        self._setup_config()

        logger.info(f"ExpandToFullBody v{self.version} åå§åå®æE")
        logger.info(f"  è®¾å¤E {self.device}")
        logger.info(f"  ç®æ E°ºå¯¸: {self.target_width}x{self.target_height}")
        logger.info(f"  ControlNet: {'âE if self.controlnet_engine else 'âE}")

    def _init_mediapipe(self):
        """åå§å MediaPipeEæ°çEAPIEE""
        self._mediapipe_pose = None
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # æ¨¡åæä»¶è·¯å¾E
            model_path = self.skill_dir / "pose_landmarker_heavy.task"

            # å¦ææ¨¡åä¸å­å¨Eå°è¯ä¸è½½
            if not model_path.exists():
                logger.info("  ð¥ ä¸è½½ MediaPipe å§¿ææ¨¡åE..")
                try:
                    import urllib.request
                    url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
                    urllib.request.urlretrieve(url, str(model_path))
                    logger.info(f"  âEæ¨¡åå·²ä¸è½½: {model_path}")
                except Exception as e:
                    logger.warning(f"  â EEæ¨¡åä¸è½½å¤±è´¥: {e}")
                    return

            # åå§åå§¿ææ£æµå¨
            pose_options = vision.PoseLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self._mediapipe_pose = vision.PoseLandmarker.create_from_options(pose_options)
            logger.info("  âEMediaPipe (æ°çEAPI) åå§åæå")

        except ImportError as e:
            logger.warning(f"  â EEMediaPipe æªå®è£E {e}")
            logger.warning("  å°E½¿ç¨é»è®¤æ©å±é»è¾E)
        except Exception as e:
            logger.warning(f"  â EEMediaPipe åå§åå¤±è´¥: {e}")
            logger.warning("  å°E½¿ç¨é»è®¤æ©å±é»è¾E)

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'target_width': 768,
            'target_height': 1024,
            'default_model': 'anytimeRealistic_v10.safetensors',
            'default_steps': 30,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _detect_head_position(self, image: Image.Image) -> tuple:
        """ä½¿ç¨ MediaPipe æ£æµå¤´é¨å¨å¾åä¸­çEY åæ E¯ä¾ï¼æ°çEAPIEE""
        try:
            if self._mediapipe_pose is None:
                return image.size[1] * 0.15, image.size[0] // 2

            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # å°EPIL Image è½¬æ¢ä¸º MediaPipe Image
            img_rgb = image.convert('RGB')
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(img_rgb))

            # æ£æµå§¿æE
            detection_result = self._mediapipe_pose.detect(mp_image)

            if detection_result and detection_result.pose_landmarks:
                landmarks = detection_result.pose_landmarks[0]
                h, w = img_rgb.size[1], img_rgb.size[0]
                # 0 æ¯é¼»å­E
                nose = landmarks[0]
                head_y = int(nose.y * h)
                head_x = int(nose.x * w)
                return head_y, head_x
        except Exception as e:
            logger.warning(f"å¤´é¨æ£æµå¤±è´¥: {e}")

        return image.size[1] * 0.15, image.size[0] // 2

    def _expand_image_area(self, image: Image.Image, target_width: int, target_height: int,
                           head_y: float, head_x: float) -> Image.Image:
        """æ©å±ç»å¸E¼å°Eå¾æ¾ç½®å¨å¤´é¨ä½äºE15% é«åº¦çE½ç½®"""
        src_w, src_h = image.size

        # è®¡ç®ç¼©æ¾æ¯ä¾ï¼è®©å¤´é¨å¤§çº¦å¨ 15% ä½ç½®
        head_ratio = 0.15
        scale = (target_height * head_ratio) / max(src_h * 0.15, head_y)

        # éå¶ç¼©æ¾èE´
        scale = max(0.5, min(2.0, scale))

        # ç¼©æ¾å¾çE
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # è®¡ç®ç²è´´ä½ç½®
        offset_y = int(target_height * 0.15 - head_y * scale)
        offset_x = int((target_width - new_w) // 2)

        # åå»ºæ©å±å¾çE
        expanded = Image.new("RGB", (target_width, target_height), (128, 128, 128))
        expanded.paste(resized, (offset_x, offset_y))

        return expanded

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

            image = Image.open(abs_image_path).convert("RGB")

            output_path = kwargs.get('output_path')
            model_name = kwargs.get('model_name', self.default_model)
            prompt = kwargs.get('prompt', 'a person, beautiful, detailed, full body, standing')
            negative_prompt = kwargs.get('negative_prompt', 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality')
            steps = kwargs.get('steps', self.default_steps)
            seed = kwargs.get('seed', -1)

            # æ´æ°ç®æ E°ºå¯¸
            target_w = kwargs.get('target_width', self.config.get('target_width', 768))
            target_h = kwargs.get('target_height', self.config.get('target_height', 1024))

            # ==================== 1. æ©å±ç»å¸E====================
            head_y, head_x = self._detect_head_position(image)
            expanded = self._expand_image_area(image, target_w, target_h, head_y, head_x)
            logger.info(f"ç»å¸E©å±å®æE: {target_w}x{target_h}")

            # ==================== 2. ä¿å­æ©å±å¾ä½ä¸ºä¸´æ¶è¾åE ====================
            temp_input = self.output_dir / "_temp_expanded.png"
            expanded.save(temp_input)

            # ==================== 3. ç´æ¥è°E¨åºå±å¼æ ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "åºå±EControlNet å¼æä¸å¯ç¨"}

            # é»è®¤è¾åEå°æ¬æè½ç®å½E
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"full_body_{timestamp}.png")

            prompt = f"{prompt}, full body, whole body, standing, detailed, masterpiece, best quality, photorealistic"

            # ä½¿ç¨ OpenPose éæ­»äººç©åå§ç»æ
            result = self.controlnet_engine.execute(
                input_image_path=str(temp_input),
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type="OPENPOSE",
                controlnet_model="openpose",
                strength=0.75,
                steps=steps,
                output_path=output_path
            )

            # æ¸Eä¸´æ¶æE»¶
            if temp_input.exists():
                temp_input.unlink()

            if result['status'] != 'success':
                return result

            elapsed = time.time() - start_time

            return {
                "status": "success",
                "output_path": result.get('image_path', output_path),
                "parameters": {
                    "model": model_name,
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "steps": steps,
                    "seed": seed,
                    "controlnet_type": "openpose",
                    "target_size": f"{target_w}x{target_h}",
                },
                "generation_time": f"{elapsed:.2f}s",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def list_models(self) -> Dict[str, Any]:
        models = {}
        for key, info in self.AVAILABLE_MODELS.items():
            models[key] = {"name": info["name"], "size": info["size"], "type": info["type"]}
        return {"status": "success", "models": models, "count": len(models), "default": self.default_model}

    def __repr__(self):
        return f"<ExpandToFullBody(name={self.name}, version={self.version})>"


# ==================== å½ä»¤è¡åEå£ ====================
if __name__ == "__main__":
    import argparse

    MODEL_CHOICES = list(ExpandToFullBody.AVAILABLE_MODELS.keys())

    parser = argparse.ArgumentParser(description="åèº«å¾è½¬å¨èº«å¾ v2.0")
    parser.add_argument("--input", "-i", required=False, help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--prompt", "-p", default="a person, beautiful, detailed, full body", help="äººç©æè¿°æç¤ºè¯E)
    parser.add_argument("--model", "-m", default="anytimeRealistic_v10.safetensors", choices=MODEL_CHOICES, help="æ¨¡ååç§°")
    parser.add_argument("--steps", "-s", type=int, default=30, help="æ¨çE­¥æ°")
    parser.add_argument("--width", type=int, default=768, help="ç®æ E®½åº¦")
    parser.add_argument("--height", type=int, default=1024, help="ç®æ E«åº¦")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="è®¾å¤E)
    parser.add_argument("--list-models", action="store_true", help="ååEææå¯ç¨æ¨¡åE)

    args = parser.parse_args()

    if args.list_models:
        skill = ExpandToFullBody()
        result = skill.list_models()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if not args.input:
        parser.error("--input æ¯å¿E¡«åæ°")

    skill = ExpandToFullBody(config={'device': args.device, 'target_width': args.width, 'target_height': args.height})

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        prompt=args.prompt,
        model_name=args.model,
        steps=args.steps,
        target_width=args.width,
        target_height=args.height,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))