# skills/photo_restorer/skill.py
"""
photo_restorer - èçEçE¿®å¤å·¥å·

ä½¿ç¨AIææ¯ä¿®å¤ãä¸è²ãå¢å¼ºèçEçE
åèE:
  - ç§çE¿®å¤ï¼å»åªãå»åçEE
  - è¶EEè¾¨çE¼æ¾å¤§EE
  - æºè½ä¸è²
  - äººè¸ä¿®å¤E
  - å¤æ¨¡åæ¯æE

æ³¨æï¼ä¸»æçç¡¬æ ¸ä¿®å¤æ¨¡åï¼EodeFormer/GFPGAN/RealESRGANEè·¯å¾E·²å½æ¡£äºE
E:/SD_OpenVINO/models/upscalers_and_restorers/
çº¯CPUç¯å¢E¸ï¼ControlNet å¼æä½ä¸ºç¨³å®å¤E¨æ¹æ¡ãE
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# æ·»å é¡¹ç®è·¯å¾E
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import torch
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

# ==================== æ¨¡åè·¯å¾E å°E(åºäºä½ ååEæ´çEç®å½E ====================
MODELS_DIR = Path(r"E:\SD_OpenVINO\models\upscalers_and_restorers")


class PhotoRestorer:
    """èçEçE¿®å¤å¨ v4.0 (åºç¡çE"""
    SUPPORTED_MODELS = {
        "controlnet": {
            "name": "ControlNet Restore",
            "description": "ä½¿ç¨æ¬å° ControlNet å¼æè¿è¡ç¨³å®ä¿®å¤E,
            "type": "diffusion",
            "default": True,
        },
        "codeformer": {
            "name": "CodeFormer",
            "description": "äººè¸ä¿®å¤E(é Python 3.10+ ä¸å®è£E®æ»¡ä¾èµE",
            "type": "gan",
            "default": False,
            "weights": MODELS_DIR / "codeformer" / "codeformer.pth",
        }
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "photo_restorer"
        self.version = "4.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
                logger.info("  âEåºå±EControlNet å¼æåå§åæå")
            except Exception as e:
                logger.warning(f"  åºå±å¼æåå§åå¤±è´¥: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ç§çE¿®å¤å¨ v{self.version} åå§åå®æE")

    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    def _setup_config(self):
        defaults = {
            "default_model": "controlnet",
            "output_dir": str(self.output_dir),
            "log_level": "INFO",
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def get_models(self) -> Dict[str, Dict]:
        return self.SUPPORTED_MODELS

    def _restore_with_controlnet(self, image_path: str, output_path: str, **kwargs) -> bool:
        """ä½¿ç¨ ControlNet è¿è¡åºç¡éç»ä¿®å¤E(ç¨³å®æ¹æ¡E"""
        if self.controlnet_engine is None:
            logger.error("åºå±EControlNet å¼æä¸å¯ç¨")
            return False

        try:
            result = self.controlnet_engine.execute(
                input_image_path=image_path,
                prompt="high quality, detailed, restored old photo, masterpiece, best quality",
                negative_prompt="low quality, blurry, damaged, torn, noise, ugly, deformed",
                preprocessor_type="HED",
                controlnet_model="lineart",
                strength=0.45,
                output_path=output_path
            )
            if result['status'] != 'success':
                logger.error(f"ControlNet å¼æè°E¨å¤±è´¥: {result.get('error')}")
                return False
            logger.info(f"ControlNet ä¿®å¤å®æE: {output_path}")
            return True
        except Exception as e:
            logger.error(f"ControlNet ä¿®å¤å¤±è´¥: {e}")
            return False

    def _restore_with_codeformer(self, image_path: str, output_path: str) -> bool:
        """ä½¿ç¨ CodeFormer ç¡¬æ ¸ä¿®å¤E(éè¦å®æ´ä¾èµE"""
        try:
            # é²åE£æ¥Eå¦ææ²¡æå®æ´çEºï¼ç´æ¥å¤±è´¥è¿å
            try:
                import facexlib
                import gfpgan
            except ImportError:
                logger.error("ç¼ºå°ç¡¬æ ¸ä¾èµåºï¼å½åç¯å¢E æ³è¿è¡ECodeFormerãE)
                return False

            import cv2
            from basicsr.utils import imwrite, img2tensor, tensor2img
            # ... (æ­¤å¤E®éä»£ç è¾E¤æEç±äºå½å Python ç¯å¢E æ³è¿è¡EbasicsrEè¿éä½ä¸ºé¢Eæ¥å£)
            # å®éè¿è¡ä¼èµ°ä¸é¢çEControlNet
            return False

        except Exception as e:
            logger.error(f"CodeFormer å è½½å¤±è´¥: {e}")
            return False

    def restore_image(self, image_path: str, model: str = None,
                      output_path: str = None, **kwargs) -> Dict[str, Any]:
        """ä¿®å¤åå¼ å¾çE""
        start_time = time.time()
        if not image_path:
            return {"status": "error", "error": "image_path æ¯å¿E¡«åæ°"}
        abs_image_path = Path(image_path).absolute()
        if not os.path.exists(abs_image_path):
            return {"status": "error", "error": f"è¾åEå¾çE¸å­å¨: {abs_image_path}ãè¯·æ£æ¥è·¯å¾E¯å¦æ­£ç¡®EE}

        model = model or self.config.get("default_model", "controlnet")

        if not output_path:
            input_name = Path(abs_image_path).stem
            ext = Path(abs_image_path).suffix or ".png"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.output_dir / f"{input_name}_restored_{timestamp}{ext}")

        logger.info(f"å¼å§ä¿®å¤E {abs_image_path}")
        logger.info(f"ä½¿ç¨æ¨¡åE {model}")

        success = False
        error_msg = None

        try:
            if model == "controlnet":
                success = self._restore_with_controlnet(str(abs_image_path), output_path, **kwargs)
            elif model == "codeformer":
                success = self._restore_with_codeformer(str(abs_image_path), output_path)
            else:
                error_msg = f"æ¨¡åE{model} ææ å®ç°"
                success = False
        except Exception as e:
            error_msg = str(e)
            success = False

        result = {
            "status": "success" if success else "error",
            "action": "restore",
            "model_used": model,
            "input_path": str(abs_image_path),
            "output_path": output_path if success else None,
            "processing_time": round(time.time() - start_time, 2),
            "timestamp": datetime.now().isoformat()
        }

        if error_msg:
            result["error"] = error_msg
        return result

    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info(f"æ§è¡æè½: {self.name} (v{self.version})")
        try:
            action = kwargs.get("action", "restore")
            if action == "list_models":
                models = {}
                for key, info in self.SUPPORTED_MODELS.items():
                    models[key] = {"name": info["name"], "description": info["description"]}
                return {"status": "success", "action": "list_models", "models": models}

            if action == "restore":
                image_path = kwargs.get("image_path")
                if not image_path:
                    return {"status": "error", "error": "è¯·æä¾Eimage_path åæ°"}
                return self.restore_image(image_path, kwargs.get("model"), kwargs.get("output_path"), **kwargs)

            return {"status": "error", "error": f"æªç¥æä½E {action}"}
        except Exception as e:
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            return {"status": "error", "error": str(e)}

    def __repr__(self):
        return f"<PhotoRestorer(name={self.name}, version={self.version})>"


if __name__ == "__main__":
    restorer = PhotoRestorer()
    print("å½åå¯ç¨çE¿®å¤æ¨¡åE")
    for name, info in restorer.get_models().items():
        print(f"  {name}: {info['description']}")