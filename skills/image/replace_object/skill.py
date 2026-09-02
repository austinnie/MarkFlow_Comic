# skills/replace_object/skill.py
"""
譖ｿ謐｢迚ｩ菴・Skill - 蟆・崟迚・ｸｭ逧・黄菴捺崛謐｢荳ｺ蜿ｦ荳荳ｪ迚ｩ菴・
鮟倩ｮ､菴ｿ逕ｨ謇句勘驕ｮ鄂ｩ・悟､咲畑騾夂畑 ControlNet 蠑墓梼霑幄｡悟・螻扈捺桷菫晄戟
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
    logger.warning("diffusers 譛ｪ螳芽｣・)

# ==================== 蠑募・騾夂畑蠑墓梼・域婿譯・・・====================
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError as e:
    CONTROLNET_ENGINE_AVAILABLE = False
    logger.warning(f"騾夂畑 ControlNet 蠑墓梼荳榊庄逕ｨ: {e}")


class ReplaceObject:
    """譖ｿ謐｢迚ｩ菴捺橿閭ｽ v2.0"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "replace_object"
        self.version = "2.0.0"

        self.skill_dir = Path(__file__).parent.absolute()
        self.project_root = self.skill_dir.parent.parent.parent
        # ==================== 蠑ｺ蛻ｶ譛ｬ謚閭ｽ霎灘・逶ｮ蠖・====================
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models_dir = Path(self.config.get('models_dir', self.project_root / 'models'))
        self.device = self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')

        self.pipeline = None
        self.current_model = None

        # ==================== 蛻晏ｧ句喧蠎募ｱょｼ墓梼 ====================
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.device})
                logger.info("  笨・蠎募ｱ・ControlNet 蠑墓梼蛻晏ｧ句喧謌仙粥")
            except Exception as e:
                logger.warning(f"  蠎募ｱょｼ墓梼蛻晏ｧ句喧螟ｱ雍･: {e}")

        self._setup_logging()
        self._setup_config()

        logger.info(f"ReplaceObject v{self.version} 蛻晏ｧ句喧螳梧・")
        logger.info(f"  隶ｾ螟・ {self.device}")

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'default_model': 'zenityXmix.inpainting.safetensors',
            'default_steps': 30,
            'default_strength': 0.7,
            'default_negative': 'ugly, deformed, blurry, low quality',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _find_model(self, model_name: str) -> Optional[Path]:
        return Path(self.models_dir / "sd-v1-5" / model_name) if model_name else None

    def _load_pipeline(self, model_path: Path) -> bool:
        """蜉霓ｽ郤ｯ Inpaint 邂｡郤ｿ・井ｽ應ｸｺ蜈懷ｺ包ｼ・""
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
            logger.error(f"  讓｡蝙句刈霓ｽ螟ｱ雍･: {e}")
            return False

    def _load_model(self, model_name: str) -> bool:
        model_path = self._find_model(model_name)
        if not model_path or not model_path.exists():
            logger.error(f"讓｡蝙倶ｸ榊ｭ伜惠: {model_name}")
            return False
        return self._load_pipeline(model_path)

    def _generate_manual_mask(self, image: Image.Image) -> Image.Image:
        """謇句勘扈伜宛隕∵崛謐｢逧・黄菴馴・鄂ｩ"""
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w), dtype=np.uint8)
        drawing = False
        brush_size = 30

        print("\n" + "=" * 50)
        print("謇句勘扈伜宛隕∵崛謐｢逧・黄菴・)
        print("=" * 50)
        print("  謖我ｽ城ｼ譬・ｷｦ髞ｮ扈伜宛隕∵崛謐｢逧・玄蝓滂ｼ育區濶ｲ・・)
        print("  貊夊ｽｮ隹・鰍逕ｻ隨泌､ｧ蟆・)
        print("  謖・R 髞ｮ驥咲ｽｮ")
        print("  謖・Q 謌・遨ｺ譬ｼ髞ｮ 螳梧・")
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

        cv2.namedWindow('Draw Object to Replace')
        cv2.setMouseCallback('Draw Object to Replace', draw_callback)

        while True:
            display = img_cv.copy()
            mask_overlay = cv2.addWeighted(display, 0.5, overlay, 0.5, 0)
            cv2.putText(mask_overlay, f"Brush: {brush_size}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(mask_overlay, "Draw object to replace, press Q to finish", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.imshow('Draw Object to Replace', mask_overlay)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 32:
                break
            elif key == ord('r'):
                mask = np.zeros((h, w), dtype=np.uint8)
                overlay = np.zeros((h, w, 3), dtype=np.uint8)
                print("  蟾ｲ驥咲ｽｮ")

        cv2.destroyAllWindows()

        if np.sum(mask > 0) < 100:
            print("  譛ｪ扈伜宛莉ｻ菴募玄蝓滂ｼ御ｽｿ逕ｨ鮟倩ｮ､讀ｭ蝨・・鄂ｩ")
            mask = np.zeros((h, w), dtype=np.uint8)
            cx, cy = w // 2, h // 2
            cv2.ellipse(mask, (cx, cy), (w // 4, h // 4), 0, 0, 360, 255, -1)

        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        print(f"  驕ｮ鄂ｩ隕・尠 {np.sum(mask > 0)} 蜒冗ｴ")
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
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name}")

        try:
            # ==================== 荳･譬ｼ霍ｯ蠕・｡鬪・====================
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "image_path 譏ｯ蠢・｡ｫ蜿よ焚"}
            
            abs_image_path = Path(image_path).absolute()
            if not os.path.exists(abs_image_path):
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}縲りｯｷ譽譟･霍ｯ蠕・弍蜷ｦ豁｣遑ｮ・・}

            object_prompt = kwargs.get('object_prompt') or "new object"
            prompt = kwargs.get('prompt') or f"{object_prompt}, high quality, detailed, masterpiece, beautiful"
            negative_prompt = kwargs.get('negative_prompt') or self.config.get('default_negative')

            strength = kwargs.get('strength', self.config.get('default_strength', 0.7))
            steps = kwargs.get('steps', self.config.get('default_steps', 30))
            seed = kwargs.get('seed', -1)
            model_name = kwargs.get('model_name', self.config.get('default_model'))

            # 蜉霓ｽ蜴溷崟
            image = Image.open(abs_image_path).convert("RGB")
            image, original_size = self._resize_image(image)

            logger.info(f"譖ｿ謐｢荳ｺ: {object_prompt}")
            logger.info(f"謠千､ｺ隸・ {prompt[:80]}...")

            # ==================== 隨ｬ荳豁･・夂函謌宣・鄂ｩ ====================
            if not kwargs.get('skip_manual', False):
                object_mask = self._generate_manual_mask(image)
            else:
                object_mask = Image.new("L", image.size, 0)

            # 鮟倩ｮ､霎灘・蛻ｰ譛ｬ謚閭ｽ逶ｮ蠖・
            output_path = kwargs.get('output_path')
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{Path(abs_image_path).stem}_replaced_{timestamp}.png")

            # ==================== 隨ｬ莠梧ｭ･・壽鴬陦鯉ｼ亥ｼ墓梼莨伜・・栗npaint蜈懷ｺ包ｼ・====================
            # 螯よ棡蠎募ｱょｼ墓梼蜿ｯ逕ｨ・瑚ｰ・畑蠑墓梼逕滓・
            if self.controlnet_engine is not None:
                logger.info("  櫨 菴ｿ逕ｨ騾夂畑 ControlNet 蠑墓梼霑幄｡梧崛謐｢・井ｿ晄戟蜴滓怏扈捺桷・・..")
                result = self.controlnet_engine.execute(
                    input_image_path=str(abs_image_path),
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    preprocessor_type="HED",      # 謠仙叙霓ｯ霎ｹ郛假ｼ悟ｮ檎ｾ惹ｿ晉蕗蜴溷崟閭梧勹扈捺桷
                    controlnet_model="canny",     # 蟇ｹ蠎疲悽蝨ｰ讓｡蝙・
                    strength=strength,
                    output_path=output_path
                )
                if result['status'] == 'success':
                    return {
                        "status": "success",
                        "output_path": result.get('image_path', output_path),
                        "object": object_prompt,
                        "generation_time": f"{time.time() - start_time:.2f}s",
                        "parameters": {"strength": strength, "steps": steps, "seed": seed, "engine": "controlnet"}
                    }
                else:
                    logger.warning(f"  蠑墓梼隹・畑螟ｱ雍･: {result.get('error')}・悟屓騾蛻ｰ Inpaint")

            # 蜈懷ｺ包ｼ壼刈霓ｽ郤ｯ Inpaint 讓｡蝙句ｹｶ逕滓・
            if not self._load_model(model_name):
                return {"status": "error", "error": f"譌豕募刈霓ｽ讓｡蝙・ {model_name}"}

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
                "object": object_prompt,
                "generation_time": f"{time.time() - start_time:.2f}s",
                "parameters": {"strength": strength, "steps": steps, "seed": seed, "engine": "inpaint"}
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="譖ｿ謐｢迚ｩ菴灘ｷ･蜈ｷ v2.0")
    parser.add_argument("--input", "-i", required=True, help="霎灘・蝗ｾ迚・ｷｯ蠕・)
    parser.add_argument("--output", "-o", help="霎灘・霍ｯ蠕・)
    parser.add_argument("--object", "-obj", required=True, help="譖ｿ謐｢荳ｺ逧・黄菴捺緒霑ｰ")
    parser.add_argument("--skip-manual", action="store_true", help="霍ｳ霑・焔蜉ｨ扈伜宛驕ｮ鄂ｩ")
    parser.add_argument("--strength", type=float, default=0.7, help="驥咲ｻ伜ｼｺ蠎ｦ")
    parser.add_argument("--steps", type=int, default=30, help="霑ｭ莉｣豁･謨ｰ")
    parser.add_argument("--seed", type=int, default=-1, help="髫乗惻遘榊ｭ・)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")

    args = parser.parse_args()
    skill = ReplaceObject(config={'device': args.device})
    result = skill.execute(
        image_path=args.input, output_path=args.output,
        object_prompt=args.object,
        skip_manual=args.skip_manual,
        strength=args.strength, steps=args.steps, seed=args.seed
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))