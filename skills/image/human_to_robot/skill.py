# skills/human_to_robot/skill.py
"""
HumanToRobot - 蟆・ｺｺ迚ｩ辣ｧ迚・ｽｬ謐｢荳ｺ譛ｺ蝎ｨ莠ｺ/譛ｺ譴ｰ鬟取ｼ

霎灘・蜿よ焚:
  - image_path (string): 霎灘・蝗ｾ迚・ｷｯ蠕・(蠢・｡ｫ)
  - output_path (string): 霎灘・蝗ｾ迚・ｷｯ蠕・(蠢・｡ｻ荳ｺ .png)
  - ai_convert (boolean): 譏ｯ蜷ｦ蠑蜷ｯ AI 蝗ｾ逕溷崟霓ｬ謐｢ (鮟倩ｮ､: False・御ｽｿ逕ｨ OpenCV 譛ｺ譴ｰ貊､髟・
  - style (string): 譛ｺ蝎ｨ莠ｺ鬟取ｼ (cyberpunk_robot / mechanical / android)
  - save_result (boolean): 譏ｯ蜷ｦ菫晏ｭ伜､・炊譌･蠢・

霎灘・:
  - status: 謇ｧ陦檎憾諤・ｼ嘖uccess / error
  - result: 蛹・性霎灘・霍ｯ蠕・柱霓ｬ謐｢隸ｦ諠・噪蟄怜・
  - metadata: 謚閭ｽ謇ｧ陦悟・謨ｰ謐ｮ
"""

import os
import sys
import json
import random
import logging
from pathlib import Path
from typing import Dict, Any

# 豺ｻ蜉鬘ｹ逶ｮ霍ｯ蠕・
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 萓晁ｵ匁｣譟･
try:
    import cv2
    import numpy as np
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# 蟆晁ｯ募ｼ募・ ControlNet 蠑墓梼
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_ENGINE_AVAILABLE = True
except ImportError:
    CONTROLNET_ENGINE_AVAILABLE = False

logger = logging.getLogger(__name__)


class HumanToRobot:
    """莠ｺ迚ｩ霓ｬ譛ｺ蝎ｨ莠ｺ謚閭ｽ"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "HumanToRobot"
        self.version = "1.0.0"

        # 隶ｾ螳夊ｾ灘・逶ｮ蠖・
        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 蛻晏ｧ句喧 ControlNet
        self.controlnet_engine = None
        if CONTROLNET_ENGINE_AVAILABLE:
            try:
                self.controlnet_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
            except Exception as e:
                logger.warning(f"ControlNet 蛻晏ｧ句喧螟ｱ雍･: {e}")

        self._setup_logging()
        self._setup_config()

    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'default_style': 'cyberpunk_robot',
            'default_ai_convert': False,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _apply_cyberpunk_filters(self, image: Image.Image, style: str = "cyberpunk_robot") -> Image.Image:
        """菴ｿ逕ｨ OpenCV 襍帛忽譛句・貊､髟・""
        if not CV2_AVAILABLE:
            return image

        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        h, w = img_cv.shape[:2]

        # 1. 謠仙叙霎ｹ郛・
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)

        # 2. 襍帛忽譛句・鬚懆牡蛛冗ｧｻ (髱定牡/豢狗ｺ｢)
        b, g, r = cv2.split(img_cv)
        b = cv2.add(b, 60)
        r = cv2.add(r, 30)
        cyber_img = cv2.merge((b, g, r))

        # 3. 豺ｻ蜉譛ｺ譴ｰ鄂第ｼ郤ｹ逅・
        noise = np.random.randint(0, 30, (h, w), dtype=np.uint8)
        grid = np.zeros((h, w), dtype=np.uint8)
        grid[::4, :] = 255
        grid[:, ::4] = 255
        grid = cv2.bitwise_and(grid, noise)

        # 4. 蜷亥ｹｶ蝗ｾ螻・
        cyber_img[edges > 0] = [255, 255, 255]
        cyber_img[grid > 0] = [0, 255, 255]

        return Image.fromarray(cv2.cvtColor(cyber_img, cv2.COLOR_BGR2RGB))

    def execute(self, **kwargs) -> Dict[str, Any]:
        """謇ｧ陦梧橿閭ｽ・域髪謖∝黒蠑蜥梧音驥冗岼蠖包ｼ・""
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name} (v{self.version})")
        
        try:
            # 1. 鬪瑚ｯ∬ｾ灘・
            image_path = kwargs.get('image_path')
            if not image_path:
                return {"status": "error", "error": "郛ｺ蟆大ｿ・｡ｫ蜿よ焚: image_path"}
            
            abs_image_path = Path(image_path).absolute()
            if not abs_image_path.exists():
                return {"status": "error", "error": f"霎灘・蝗ｾ迚・ｸ榊ｭ伜惠: {abs_image_path}"}

            # 隸ｻ蜿門盾謨ｰ
            ai_convert = kwargs.get('ai_convert', self.config.get('default_ai_convert', False))
            style = kwargs.get('style', self.config.get('default_style', 'cyberpunk_robot'))

            # ================= 謾ｯ謖∵音驥乗ｨ｡蠑・=================
            # 螯よ棡莨蜈･逧・弍逶ｮ蠖包ｼ悟・謇ｹ驥丞､・炊
            if abs_image_path.is_dir():
                valid_exts = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
                images = [p for p in abs_image_path.iterdir() if p.suffix.lower() in valid_exts]
                
                if not images:
                    return {"status": "error", "error": f"逶ｮ蠖穂ｸｭ豐｡譛画伽蛻ｰ蝗ｾ迚・ {abs_image_path}"}
                
                logger.info(f"唐 蜿醍鴫 {len(images)} 蠑蝗ｾ迚・ｼ悟ｼ蟋区音驥丞､・炊...")
                results = []
                
                for idx, img_path in enumerate(images):
                    # 閾ｪ蜉ｨ逕滓・霎灘・霍ｯ蠕・
                    output_filename = f"{img_path.stem}_robot_{idx}.png"
                    output_path = str(self.output_dir / output_filename)
                    
                    # 隹・畑蜀・Κ螟・炊譁ｹ豕・
                    result = self._process_single_image(str(img_path), output_path, ai_convert, style)
                    results.append(result)
                
                return {
                    "status": "success",
                    "result": {
                        "batch": True,
                        "total": len(results),
                        "items": results
                    },
                    "metadata": {
                        "skill": self.name,
                        "version": self.version,
                        "executed_at": str(__import__('datetime').datetime.now().isoformat())
                    }
                }
            
            # ================= 蜊募ｼ讓｡蠑・=================
            output_path = kwargs.get('output_path')
            if not output_path:
                timestamp = Path(abs_image_path).stem
                output_path = str(self.output_dir / f"{timestamp}_robot.png")

            result = self._process_single_image(str(abs_image_path), output_path, ai_convert, style)
            
            return {
                "status": result.get("status"),
                "result": result,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": str(__import__('datetime').datetime.now().isoformat())
                }
            }

        except Exception as e:
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": str(__import__('datetime').datetime.now().isoformat())
            }

    def _process_single_image(self, input_path: str, output_path: str, ai_convert: bool, style: str) -> Dict:
        """螟・炊蜊募ｼ蝗ｾ迚・噪遘∵怏譁ｹ豕・""
        try:
            if ai_convert and self.controlnet_engine:
                style_prompts = {
                    "cyberpunk_robot": "cyberpunk robot, humanoid robot, metallic skin, cybernetic implants, neon lights, 4k, masterpiece",
                    "mechanical": "mechanical android, metallic joints, industrial robot, exposed wires, highly detailed",
                    "android": "advanced android, artificial intelligence, human-like face, sleek metal, 8k"
                }
                prompt = style_prompts.get(style, style_prompts["cyberpunk_robot"])

                result = self.controlnet_engine.execute(
                    input_image_path=input_path,
                    prompt=prompt,
                    negative_prompt="human, skin, hair, organic, cartoon, blurry, low quality, deformed",
                    preprocessor_type="HED",
                    controlnet_model="canny",
                    strength=0.65,
                    output_path=output_path
                )
                if result['status'] != 'success':
                    return result
            else:
                image = Image.open(input_path).convert("RGB")
                image = self._apply_cyberpunk_filters(image, style=style)
                
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                image.save(output_path, format='PNG')

            return {
                "status": "success",
                "output_path": output_path,
                "style": style,
                "ai_converted": ai_convert
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "input_path": input_path
            }
            
    def __repr__(self):
        return f"<HumanToRobot(name={self.name}, version={self.version})>"