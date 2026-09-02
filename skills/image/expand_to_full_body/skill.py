# skills/expand_to_full_body/skill.py
"""
Expand to Full Body - 蟆・ｺｺ迚ｩ蜊願ｺｫ/螟ｴ蜒丞崟謇ｩ螻穂ｸｺ蜈ｨ霄ｫ蝗ｾ
螟咲畑騾夂畑 ControlNet 蠑墓梼・御ｽｿ逕ｨ MediaPipe 譫・溯ｽｻ驥乗｣豬句ｮ壻ｽ榊､ｴ驛ｨ
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
    logger.warning("torch 謌・PIL 譛ｪ螳芽｣・)

# ==================== 蠑募・騾夂畑蠑墓梼・域婿譯・・・====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"騾夂畑 ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")


class ExpandToFullBody:
    """蜊願ｺｫ蝗ｾ霓ｬ蜈ｨ霄ｫ蝗ｾ謚閭ｽ v2.0 (MediaPipe + OpenPose 髞∝ｧｿ諤・"""

    # 蜿ｯ逕ｨ讓｡蝙句・陦ｨ・育畑莠主ｱ慕､ｺ・・
    AVAILABLE_MODELS = {
        "anytimeRealistic_v10.safetensors": {"name": "Anytime Realistic", "size": "2.13 GB", "type": "蜀吝ｮ・},
        "aiiiii01_v10.safetensors": {"name": "AIiiii v1.0", "size": "2.13 GB", "type": "蜀吝ｮ・},
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "expand_to_full_body"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 蠑ｺ蛻ｶ譛ｬ謚閭ｽ霎灘・逶ｮ蠖・====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.default_model = self.config.get('default_model', 'anytimeRealistic_v10.safetensors')
        self.default_steps = self.config.get('default_steps', 30)
        self.target_height = self.config.get('target_height', 1024)
        self.target_width = self.config.get('target_width', 768)

        # 郛灘ｭ・
        self.controlnet_engine = None

        # ==================== 蛻晏ｧ句喧蠎募ｱょｼ墓梼 ====================
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  笨・蠎募ｱ・ControlNet 蠑墓梼蛻晏ｧ句喧謌仙粥")
            except Exception as e:
                logger.warning(f"  蠎募ｱょｼ墓梼蛻晏ｧ句喧螟ｱ雍･: {e}")

        # ==================== 蛻晏ｧ句喧 MediaPipe・域眠迚・API・・====================
        self._mediapipe_pose = None
        self._init_mediapipe()

        self._setup_logging()
        self._setup_config()

        logger.info(f"ExpandToFullBody v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")
        logger.info(f"  逶ｮ譬・ｰｺ蟇ｸ: {self.target_width}x{self.target_height}")
        logger.info(f"  ControlNet: {'笨・ if self.controlnet_engine else '笶・}")

    def _init_mediapipe(self):
        """蛻晏ｧ句喧 MediaPipe・域眠迚・API・・""
        self._mediapipe_pose = None
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # 讓｡蝙区枚莉ｶ霍ｯ蠕・
            model_path = self.skill_dir / "pose_landmarker_heavy.task"

            # 螯よ棡讓｡蝙倶ｸ榊ｭ伜惠・悟ｰ晁ｯ穂ｸ玖ｽｽ
            if not model_path.exists():
                logger.info("  踏 荳玖ｽｽ MediaPipe 蟋ｿ諤∵ｨ｡蝙・..")
                try:
                    import urllib.request
                    url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task"
                    urllib.request.urlretrieve(url, str(model_path))
                    logger.info(f"  笨・讓｡蝙句ｷｲ荳玖ｽｽ: {model_path}")
                except Exception as e:
                    logger.warning(f"  笞・・讓｡蝙倶ｸ玖ｽｽ螟ｱ雍･: {e}")
                    return

            # 蛻晏ｧ句喧蟋ｿ諤∵｣豬句勣
            pose_options = vision.PoseLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self._mediapipe_pose = vision.PoseLandmarker.create_from_options(pose_options)
            logger.info("  笨・MediaPipe (譁ｰ迚・API) 蛻晏ｧ句喧謌仙粥")

        except ImportError as e:
            logger.warning(f"  笞・・MediaPipe 譛ｪ螳芽｣・ {e}")
            logger.warning("  蟆・ｽｿ逕ｨ鮟倩ｮ､謇ｩ螻暮ｻ霎・)
        except Exception as e:
            logger.warning(f"  笞・・MediaPipe 蛻晏ｧ句喧螟ｱ雍･: {e}")
            logger.warning("  蟆・ｽｿ逕ｨ鮟倩ｮ､謇ｩ螻暮ｻ霎・)

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
        """菴ｿ逕ｨ MediaPipe 譽豬句､ｴ驛ｨ蝨ｨ蝗ｾ蜒丈ｸｭ逧・Y 蝮先・ｯ比ｾ具ｼ域眠迚・API・・""
        try:
            if self._mediapipe_pose is None:
                return image.size[1] * 0.15, image.size[0] // 2

            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            # 蟆・PIL Image 霓ｬ謐｢荳ｺ MediaPipe Image
            img_rgb = image.convert('RGB')
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.array(img_rgb))

            # 譽豬句ｧｿ諤・
            detection_result = self._mediapipe_pose.detect(mp_image)

            if detection_result and detection_result.pose_landmarks:
                landmarks = detection_result.pose_landmarks[0]
                h, w = img_rgb.size[1], img_rgb.size[0]
                # 0 譏ｯ鮠ｻ蟄・
                nose = landmarks[0]
                head_y = int(nose.y * h)
                head_x = int(nose.x * w)
                return head_y, head_x
        except Exception as e:
            logger.warning(f"螟ｴ驛ｨ譽豬句､ｱ雍･: {e}")

        return image.size[1] * 0.15, image.size[0] // 2

    def _expand_image_area(self, image: Image.Image, target_width: int, target_height: int,
                           head_y: float, head_x: float) -> Image.Image:
        """謇ｩ螻慕判蟶・ｼ悟ｰ・次蝗ｾ謾ｾ鄂ｮ蝨ｨ螟ｴ驛ｨ菴堺ｺ・15% 鬮伜ｺｦ逧・ｽ咲ｽｮ"""
        src_w, src_h = image.size

        # 隶｡邂礼ｼｩ謾ｾ豈比ｾ具ｼ夊ｮｩ螟ｴ驛ｨ螟ｧ郤ｦ蝨ｨ 15% 菴咲ｽｮ
        head_ratio = 0.15
        scale = (target_height * head_ratio) / max(src_h * 0.15, head_y)

        # 髯仙宛郛ｩ謾ｾ闌・峩
        scale = max(0.5, min(2.0, scale))

        # 郛ｩ謾ｾ蝗ｾ迚・
        new_w = int(src_w * scale)
        new_h = int(src_h * scale)
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # 隶｡邂礼ｲ倩ｴｴ菴咲ｽｮ
        offset_y = int(target_height * 0.15 - head_y * scale)
        offset_x = int((target_width - new_w) // 2)

        # 蛻帛ｻｺ謇ｩ螻募崟迚・
        expanded = Image.new("RGB", (target_width, target_height), (128, 128, 128))
        expanded.paste(resized, (offset_x, offset_y))

        return expanded

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name} (v{self.version})")

        try:
            # ==================== 荳･譬ｼ霍ｯ蠕・｡鬪・====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 譏ｯ蠢・｡ｫ蜿よ焚"}

            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}縲りｯｷ譽譟･霍ｯ蠕・弍蜷ｦ豁｣遑ｮ・・}

            image = Image.open(abs_image_path).convert("RGB")

            output_path = kwargs.get('output_path')
            model_name = kwargs.get('model_name', self.default_model)
            prompt = kwargs.get('prompt', 'a person, beautiful, detailed, full body, standing')
            negative_prompt = kwargs.get('negative_prompt', 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality')
            steps = kwargs.get('steps', self.default_steps)
            seed = kwargs.get('seed', -1)

            # 譖ｴ譁ｰ逶ｮ譬・ｰｺ蟇ｸ
            target_w = kwargs.get('target_width', self.config.get('target_width', 768))
            target_h = kwargs.get('target_height', self.config.get('target_height', 1024))

            # ==================== 1. 謇ｩ螻慕判蟶・====================
            head_y, head_x = self._detect_head_position(image)
            expanded = self._expand_image_area(image, target_w, target_h, head_y, head_x)
            logger.info(f"逕ｻ蟶・黄螻募ｮ梧・: {target_w}x{target_h}")

            # ==================== 2. 菫晏ｭ俶黄螻募崟菴應ｸｺ荳ｴ譌ｶ霎灘・ ====================
            temp_input = self.output_dir / "_temp_expanded.png"
            expanded.save(temp_input)

            # ==================== 3. 逶ｴ謗･隹・畑蠎募ｱょｼ墓梼 ====================
            if self.controlnet_engine is None:
                return {"status": "error", "error": "蠎募ｱ・ControlNet 蠑墓梼荳榊庄逕ｨ"}

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"full_body_{timestamp}.png")

            prompt = f"{prompt}, full body, whole body, standing, detailed, masterpiece, best quality, photorealistic"

            # 菴ｿ逕ｨ OpenPose 髞∵ｭｻ莠ｺ迚ｩ蜴溷ｧ狗ｻ捺桷
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

            # 貂・炊荳ｴ譌ｶ譁・ｻｶ
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
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
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


# ==================== 蜻ｽ莉､陦悟・蜿｣ ====================
if __name__ == "__main__":
    import argparse

    MODEL_CHOICES = list(ExpandToFullBody.AVAILABLE_MODELS.keys())

    parser = argparse.ArgumentParser(description="蜊願ｺｫ蝗ｾ霓ｬ蜈ｨ霄ｫ蝗ｾ v2.0")
    parser.add_argument("--input", "-i", required=False, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--prompt", "-p", default="a person, beautiful, detailed, full body", help="莠ｺ迚ｩ謠剰ｿｰ謠千､ｺ隸・)
    parser.add_argument("--model", "-m", default="anytimeRealistic_v10.safetensors", choices=MODEL_CHOICES, help="讓｡蝙句錐遘ｰ")
    parser.add_argument("--steps", "-s", type=int, default=30, help="謗ｨ逅・ｭ･謨ｰ")
    parser.add_argument("--width", type=int, default=768, help="逶ｮ譬・ｮｽ蠎ｦ")
    parser.add_argument("--height", type=int, default=1024, help="逶ｮ譬・ｫ伜ｺｦ")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="隶ｾ螟・)
    parser.add_argument("--list-models", action="store_true", help="蛻怜・謇譛牙庄逕ｨ讓｡蝙・)

    args = parser.parse_args()

    if args.list_models:
        skill = ExpandToFullBody()
        result = skill.list_models()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    if not args.input:
        parser.error("--input 譏ｯ蠢・｡ｫ蜿よ焚")

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