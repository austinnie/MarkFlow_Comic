# skills/photo_realistic/skill.py
"""
ç§çEå®å Skill - ç»å ControlNet å¾çå¾ä¸EOpenCV åæå¤E
é»è®¤åªåçº¯åæå¤EEå¼å¯ ai_realistic åå¯è¿è¡çå®åéç»E
"""

import os
import sys
import random
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

# æ·»å é¡¹ç®è·¯å¾E
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import cv2
    import numpy as np
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV æªå®è£E¼å¾åå¤EåèEä¸å¯ç¨")

# ==================== å¼åEéç¨ ControlNet å¼æEæ¹æ¡EEE====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"éç¨ ControlNet å¼æä¸å¯ç¨: {e}")

# ==================== ç¸æºé¢E®¾ ====================
CAMERA_PRESETS = {
    "sony_a7iv": {
        "Make": "Sony", "Model": "ILCE-7M4",
        "ISO": [100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 105],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "FE 24-70mm F2.8 GM"
    },
    "canon_r5": {
        "Make": "Canon", "Model": "Canon EOS R5",
        "ISO": [100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 100],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "RF 24-70mm F2.8 L IS USM"
    },
    "nikon_z8": {
        "Make": "Nikon", "Model": "NIKON Z 8",
        "ISO": [64, 100, 200, 400, 800, 1600],
        "FNumber": [1.8, 2.8, 4.0, 5.6],
        "ExposureTime": ["1/60", "1/125", "1/250", "1/500", "1/1000"],
        "FocalLength": [24, 35, 50, 85, 105],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "NIKKOR Z 24-70mm f/2.8 S"
    },
    "iphone_15": {
        "Make": "Apple", "Model": "iPhone 15 Pro Max",
        "ISO": [32, 40, 50, 64, 80, 100, 125, 160, 200],
        "FNumber": [1.78, 2.2, 2.8],
        "ExposureTime": ["1/60", "1/120", "1/250", "1/500", "1/1000", "1/2000"],
        "FocalLength": [24, 48, 77],
        "Software": "Adobe Photoshop Lightroom 6.0",
        "LensModel": "iPhone 15 Pro Max back triple camera"
    }
}

PHOTO_STYLES = {
    "portrait": {"ISO": [100, 200], "FNumber": [1.8, 2.8], "FocalLength": [50, 85, 105]},
    "landscape": {"ISO": [64, 100], "FNumber": [5.6, 8.0, 11.0], "FocalLength": [24, 35, 50]},
    "street": {"ISO": [200, 400, 800], "FNumber": [2.8, 4.0, 5.6], "FocalLength": [24, 35, 50]},
    "night": {"ISO": [1600, 3200, 6400], "FNumber": [1.8, 2.8], "FocalLength": [24, 35, 50]}
}


class PhotoRealistic:
    """ç§çEå®åæè½"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_realistic"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        # ==================== å¼ºå¶æ¬æè½è¾åEç®å½E====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # ==================== ControlNet å¼æå®ä¾å ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
                logger.info("  âEåºå±EControlNet å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ç§çEå®åæè½ v{self.version} åå§åå®æE")
        logger.info(f"  ControlNet: {'âEå¯ç¨' if self.controlnet_engine else 'âEä¸å¯ç¨'}")
        logger.info(f"  OpenCV: {'âEå¯ç¨' if CV2_AVAILABLE else 'âEä¸å¯ç¨'}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'default_camera': 'sony_a7iv',
            'default_style': 'portrait',
            'default_strength': 'medium',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _inject_exif(self, image_path: str, camera: str = "sony_a7iv", style: str = "portrait", randomize: bool = True) -> Dict[str, Any]:
        """æ³¨å¥ EXIF åE°æ®Eä½¿ç¨ ExifToolEE""
        camera_preset = CAMERA_PRESETS.get(camera, CAMERA_PRESETS["sony_a7iv"])
        style_preset = PHOTO_STYLES.get(style, PHOTO_STYLES["portrait"])

        exif_params = {
            "Make": camera_preset.get("Make", "Sony"),
            "Model": camera_preset.get("Model", "ILCE-7M4"),
            "Software": camera_preset.get("Software", "Adobe Photoshop Lightroom 6.0"),
        }

        if randomize:
            exif_params["ISO"] = random.choice(camera_preset.get("ISO", [100]))
            exif_params["FNumber"] = random.choice(camera_preset.get("FNumber", [1.8]))
            exif_params["ExposureTime"] = random.choice(camera_preset.get("ExposureTime", ["1/125"]))
            exif_params["FocalLength"] = random.choice(camera_preset.get("FocalLength", [50]))
        else:
            exif_params["ISO"] = style_preset.get("ISO", [100])[0]
            exif_params["FNumber"] = style_preset.get("FNumber", [2.8])[0]
            exif_params["FocalLength"] = style_preset.get("FocalLength", [50])[0]
            exif_params["ExposureTime"] = "1/250"

        exif_params["LensModel"] = camera_preset.get("LensModel", "")

        exiftool = shutil.which("exiftool")
        if exiftool is None:
            return {"status": "warning", "message": "exiftool æªæ¾å°"}

        try:
            cmd = [exiftool, "-overwrite_original"]
            for key, value in exif_params.items():
                if value:
                    cmd.extend([f"-{key}", str(value)])
            cmd.append(image_path)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return {"status": "warning", "message": f"EXIF æ³¨å¥å¤±è´¥: {result.stderr}"}
            return {"status": "success", "exif_params": exif_params}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def add_realistic_features(self, image: Image.Image, iso: int = 400, add_noise: bool = True, add_vignette: bool = True, add_sharpening: bool = True) -> Image.Image:
        """æ·»å çå®ç¸æºç¹å¾E¼EpenCVEE""
        if not CV2_AVAILABLE:
            return image

        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        if add_noise:
            noise_strength = max(1, min(20, iso / 50))
            noise = np.random.normal(0, noise_strength, img_cv.shape).astype(np.uint8)
            img_cv = cv2.add(img_cv, noise)
            logger.info(f"  âEæ·»å åªç¹ (ISO {iso})")

        if add_vignette:
            kernel_x = cv2.getGaussianKernel(w, w * 0.3)
            kernel_y = cv2.getGaussianKernel(h, h * 0.3)
            kernel = kernel_y * kernel_x.T
            mask = 1 - kernel * 0.25
            for i in range(3):
                img_cv[:, :, i] = (img_cv[:, :, i] * mask).astype(np.uint8)
            logger.info("  âEæ·»å æè§E)

        if add_sharpening:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]) * 0.8 + 0.2 * np.eye(3)
            kernel = kernel / np.sum(kernel)
            img_cv = cv2.filter2D(img_cv, -1, kernel)
            logger.info("  âEéå")

        return Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))

    def process(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        # ===== æ ¸å¿E¼å³ =====
        ai_realistic: bool = False,       # æ¯å¦å¼å¯ ControlNet éç»E
        enable_noise: bool = False,
        enable_vignette: bool = False,
        enable_sharpen: bool = False,
        enable_exif: bool = False,
        # ===== åæ° =====
        camera: str = "sony_a7iv",
        style: str = "portrait",
        strength: str = "medium",
        iso: Optional[int] = None,
        randomize: bool = True
    ) -> Dict[str, Any]:
        """
        å¤Eå¾çE
        Args:
            image_path: è¾åEå¾çE·¯å¾E
            output_path: è¾åEè·¯å¾E
            ai_realistic: æ¯å¦å¼å¯ ControlNet AI çå®åéç»E(è®¾ä¸º True å°E¼åEè°E¨ controlnet_img2img)
            enable_noise: æ¯å¦æ·»å åªç¹
            enable_vignette: æ¯å¦æ·»å æè§E
            enable_sharpen: æ¯å¦éå
            enable_exif: æ¯å¦æ³¨å¥ EXIF
        """
        # ==================== ä¸¥æ ¼è·¯å¾E ¡éªE====================
        if not image_path:
            return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
        abs_image_path = Path(image_path).absolute()
        if not os.path.exists(abs_image_path):
            return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}"}

        # é»è®¤è¾åEå°æ¬æè½ç®å½E
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_realistic_{timestamp}.jpg")

        # 1. åå¤æ­æ¯å¦è°E¨ ControlNet è¿è¡éç»E
        if ai_realistic:
            if self.controlnet_engine is None:
                return {"status": "error", "error": "ControlNet å¼æä¸å¯ç¨"}
            logger.info("  ð¥ å¼å¯ ControlNet AI çå®åéç»E..")
            result = self.controlnet_engine.execute(
                input_image_path=str(abs_image_path),
                prompt="photorealistic, real person, realistic skin texture, natural lighting, detailed, masterpiece, high quality, 8k",
                negative_prompt="anime, cartoon, 2d, illustration, drawing, painting, sketch, blurry, low quality",
                preprocessor_type="HED",
                controlnet_model="canny",
                strength=0.45,  # ä½éç»å¹Eº¦Eä¿æåå¾ç»æ
                output_path=output_path
            )
            if result['status'] != 'success':
                return result
            # éç»åçE¾çE
            image = Image.open(output_path).convert("RGB")
        else:
            # ä¸éç»ï¼ç´æ¥è¯»ååå¾
            image = Image.open(abs_image_path).convert("RGB")

        # 2. OpenCV åæææEåºäºéç»åçE¾çE¼E
        applied = {"noise": False, "vignette": False, "sharpen": False, "exif": False}

        # ç¡®å®EISO
        strength_map = {"light": {"iso": 200}, "medium": {"iso": 400}, "strong": {"iso": 800}}
        if iso is None:
            iso = strength_map.get(strength, strength_map["medium"])["iso"]
            if randomize:
                iso = random.choice([iso, iso * 2])

        if enable_noise or enable_vignette or enable_sharpen:
            image = self.add_realistic_features(
                image, iso=iso,
                add_noise=enable_noise,
                add_vignette=enable_vignette,
                add_sharpening=enable_sharpen
            )
            applied["noise"] = enable_noise
            applied["vignette"] = enable_vignette
            applied["sharpen"] = enable_sharpen

        # 3. ä¿å­æç»ç»æ
        image.save(output_path, format='JPEG', quality=92, optimize=True)

        result = {
            "status": "success",
            "output_path": output_path,
            "applied": applied,
            "ai_realistic": ai_realistic,
            "iso": iso,
        }

        # 4. EXIF æ³¨å¥
        if enable_exif:
            exif_result = self._inject_exif(output_path, camera=camera, style=style, randomize=randomize)
            applied["exif"] = True
            result["exif"] = exif_result
            logger.info(f"  âEEXIF æ³¨å¥æå (ç¸æº: {camera})")

        logger.info(f"âEå¤Eå®æE: {output_path}")
        return result

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æ§è¡æè½"""
        action = kwargs.get('action', 'process')

        if action == 'process':
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}

            return self.process(
                image_path=image_path,
                output_path=kwargs.get('output_path'),
                ai_realistic=kwargs.get('ai_realistic', False),
                enable_noise=kwargs.get('enable_noise', False),
                enable_vignette=kwargs.get('enable_vignette', False),
                enable_sharpen=kwargs.get('enable_sharpen', False),
                enable_exif=kwargs.get('enable_exif', False),
                camera=kwargs.get('camera', self.config.get('default_camera', 'sony_a7iv')),
                style=kwargs.get('style', self.config.get('default_style', 'portrait')),
                strength=kwargs.get('strength', self.config.get('default_strength', 'medium')),
                iso=kwargs.get('iso'),
                randomize=kwargs.get('randomize', True)
            )

        elif action == 'list_cameras':
            return {"status": "success", "cameras": list(CAMERA_PRESETS.keys())}

        elif action == 'list_styles':
            return {"status": "success", "styles": list(PHOTO_STYLES.keys())}

        else:
            return {"status": "error", "error": f"æªç¥æä½E {action}"}

    def __repr__(self):
        return f"<PhotoRealistic(name={self.name}, version={self.version})>"


# ==================== å½ä»¤è¡åEå£ ====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ç§çEå®åå·¥å· v2.0")

    parser.add_argument("--input", "-i", help="è¾åEå¾çE·¯å¾E)
    parser.add_argument("--output", "-o", help="è¾åEè·¯å¾E)

    parser.add_argument("--ai-realistic", action="store_true", help="å¼å¯ ControlNet AI çå®å")
    parser.add_argument("--noise", action="store_true", help="æ·»å åªç¹")
    parser.add_argument("--vignette", action="store_true", help="æ·»å æè§E)
    parser.add_argument("--sharpen", action="store_true", help="éå")
    parser.add_argument("--exif", action="store_true", help="æ³¨å¥ EXIF")

    parser.add_argument("--camera", default="sony_a7iv", choices=list(CAMERA_PRESETS.keys()), help="ç¸æºé¢E®¾")
    parser.add_argument("--style", default="portrait", choices=list(PHOTO_STYLES.keys()), help="ç§çE£æ ¼")
    parser.add_argument("--strength", default="medium", choices=["light", "medium", "strong"], help="å¼ºåº¦")
    parser.add_argument("--iso", type=int, help="ISO å¼")

    args = parser.parse_args()

    skill = PhotoRealistic()

    result = skill.execute(
        image_path=args.input,
        output_path=args.output,
        ai_realistic=args.ai_realistic,
        enable_noise=args.noise,
        enable_vignette=args.vignette,
        enable_sharpen=args.sharpen,
        enable_exif=args.exif,
        camera=args.camera,
        style=args.style,
        strength=args.strength,
        iso=args.iso
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))