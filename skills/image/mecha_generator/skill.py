"""
MechaGenerator - æºç²å°å¥³/æºå¨äººé«ç«¯æEå¾ä¸å¾çå¾çæEå¨

è¾åEåæ°:
  - mode (string): çæEæ¨¡å¼E("txt2img" æEå¾ / "img2img" å¾çå¾)
  - prompt (string): æ­£é¢æç¤ºè¯E(å¿E¡«, txt2img)
  - negative_prompt (string): è´é¢æç¤ºè¯E
  - input_image (string): å¾çå¾çE¾åEå¾çE·¯å¾E(img2imgæ¨¡å¼ä¸å¿E¡«)
  - output_path (string): è¾åEè·¯å¾E(å¯éï¼éè®¤èªå¨çæE)
  - width (int): å®½åº¦ (éè®¤ 768)
  - height (int): é«åº¦ (éè®¤ 1024)
  - steps (int): è¿­ä£æ­¥æ° (éè®¤ 30)
  - cfg_scale (float): æç¤ºè¯å¼å¯¼ç³æ° (éè®¤ 7.5)
  - seed (int): éæºçå­E(éè®¤ -1 éæº)
  - model_name (string): ä½¿ç¨åªä¸ªåºæ¨¡ (éè®¤è¯åç¨æ·å¨å±éç½®)
  - style (string): é¢E®¾é£æ ¼ (å¯¹åºæ¬å°æç¤ºè¯æä¶Eå¦Emecha_glow / mecha_girl / none)
  - controlnet_type (string): img2imgæ¨¡å¼ä¸çå¿ææå¶ ("openpose", "canny", "depth" ç­E
  - strength (float): å¾çå¾éçå¼ºåº¦ (0.0-1.0Eéè®¤ 0.75)

è¾åE:
  - status: æè¡ç¶æE
  - image_paths: çæEå¾çEè·¯å¾EEè¡¨
  - used_model: å®éä½¿ç¨çEºæ¨¡åç°
"""

import os
import sys
import json
import time
import random
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

# å¯¼å¥æ¡E¶åE¨çE¶
try:
    from markflow.utils.model_config import get_models, get_loras, get_model_config, resolve_model_path
    from markflow.cli.commands import execute_skill
    MODEL_UTILS_AVAILABLE = True
except ImportError:
    MODEL_UTILS_AVAILABLE = False
    logger.warning("æªè½å¯¼å¥ Markflow æ¨¡åéEç½®å·¥å·")

# å°è¯å¯¼å¥ ControlNet
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False

# å°è¯å¯¼å¥ SD å¾åçæä¸å¼æ
try:
    from skills.sd_image_generator.skill import Sdimagegenerator
    SD_ENGINE_AVAILABLE = True
except ImportError:
    SD_ENGINE_AVAILABLE = False
    logger.warning("æªè½å¯¼å¥ SD ä¸å¼æEå°è¯å¯æ¾å¶äå¼æ")


class Mechagenerator:
    """æºç²å°å¥³çæEå¨Eæ¯ææçå¾ãå¾çå¾ååEå±æç¤ºè¯çE"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "mecha_generator"
        self.version = "1.0.0"
        self.skill_dir = Path(__file__).parent.absolute()
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._setup_logging()
        self._setup_config()
        self._init_engine()
        
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(level=getattr(logging, log_level.upper()),
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def _setup_config(self):
        defaults = {
            'output_dir': str(self.output_dir),
            'default_width': 768,
            'default_height': 1024,
            'default_steps': 30,
            'default_cfg': 7.5,
            'default_strength': 0.75,
            'default_style': 'none',
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _init_engine(self):
        """ååååºå±çæå¼æ"""
        self.sd_engine = None
        if SD_ENGINE_AVAILABLE:
            try:
                self.sd_engine = Sdimagegenerator(config={'device': self.config.get('device', 'cpu')})
                logger.info("SD ä¸å¼æå è½½æå")
            except Exception as e:
                logger.warning(f"SD ä¸å¼æåååå¤±è´¥: {e}")

        # å¦æä¸å¼æä¸å¯ç¨Eå°è¯å¯æ¾å¶äåºå±E
        if not self.sd_engine:
            # å°è¯å¯¼å¥é¡¹ç®ä¸­çEgenerate_images çæEå¨
            try:
                sys.path.insert(0, str(project_root / "scripts"))
                from generate_images import SDImageGenerator
                self.script_generator = SDImageGenerator()
                logger.info("Scripts ç®å½ä¸çå¾çEæå¨å è½½æå")
            except Exception as e:
                logger.warning(f"Scripts çæEå¨å è½½å¤±è´¥: {e}")

    def _apply_style_preset(self, style: str, prompt: str) -> str:
        """æ ¹æ®é¢E®¾é£æ ¼æåæç¤ºè¯å¢å¼º (å½æ¬å°æ æ­¤æE¶æ¶çEéæºå¶)"""
        style_presets = {
            "cyber_android_sdxl": "cyber android, translucent polymer skin, intricate blue energy circuits, glossy white mechanical skeleton",
            "mecha_girl": "mecha girl, metallic joints, sleek white and grey armor, exposed wiring, sci-fi weapon",
            "mecha_blueprint": "white mechanical android, blueprint lines, glowing blue core, uncolored 3D render, engineering diagram style",
            "mecha_glow": "biomechanical android, semi-transparent shell, glowing inner mechanical parts, ethereal pale lighting, 8k",
        }
        
        if style in style_presets:
            return f"{prompt}, {style_presets[style]}"
        return prompt

    def _load_prompts_from_library(self, style_name: str) -> Dict:
        """äå½åæè½ç®å½å è½½æç¤ºè¯åºï¼èEå¨ééEæ¬å°æE¶EE""
        local_py_files = list(self.skill_dir.glob("*.py"))
        
        for py_file in local_py_files:
            if py_file.name == "skill.py":
                continue
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"style_module_{py_file.stem}", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # æ ¸å¿E¼èEå¨å¯æ¾æE¶éç STYLE å­åEEå¹¶å¹éåEé®å­E
                if hasattr(module, 'STYLE'):
                    styles = module.STYLE
                    # å¹éæä¶åçå³é®è¯ï¼æEèE­åEéç key
                    for key in styles.keys():
                        if style_name in key or style_name in py_file.stem:
                            return styles[key]
            except Exception as e:
                logger.warning(f"å è½½æç¤ºè¯æä¶ {py_file.name} å¤±è´¥: {e}")
        
        return {}
        
    def _generate_text_to_image(self, prompt: str, negative_prompt: str, width: int, height: int, steps: int, cfg: float, seed: int, model_name: Optional[str]) -> Dict:
        """æè¡æçå¾"""
        
        # ===== æ ¸å¿E¿®æ¹Eå¨æè·åç¨æ·éç½®çE¨¡åE=====
        # äEmodel_config.py ä¸­æ¿å°å½åç¨æ·éå®çæ¨¡åE
        try:
            from markflow.utils.model_config import get_model_config
            global_sd_config = get_model_config()
            if not model_name and global_sd_config.get('model_path'):
                model_name = global_sd_config.get('model_name')  # è·åéEç½®çE¨¡åå
        except Exception as e:
            logger.warning(f"è·ååEå±æ¨¡åéEç½®å¤±è´¥: {e}")

        if self.sd_engine:
            try:
                result = self.sd_engine.execute(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    steps=steps,
                    cfg_scale=cfg,
                    seed=seed,
                    model_name=model_name,
                    batch_size=1
                )
                if result.get('status') == 'success':
                    return result
                return {"status": "error", "error": result.get('error', 'SDå¼æå¤±è´¥')}
            except Exception as e:
                logger.error(f"SDå¼æå¼å¸¸: {e}")
                return {"status": "error", "error": str(e)}

        # åéå°èæ¬çæEå¨
        if hasattr(self, 'script_generator') and self.script_generator:
            try:
                scheme = {
                    'prompt': prompt,
                    'negative_prompt': negative_prompt,
                    'params': {
                        'width': width, 'height': height, 'steps': steps,
                        'cfg_scale': cfg, 'seed': seed, 'model': model_name
                    }
                }
                success = self.script_generator.generate_one(scheme)
                if success:
                    out_dir = Path("./output/python_generated")
                    latest = sorted(out_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)[0]
                    return {"status": "success", "image_paths": [str(latest)], "using": "script_generator"}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        return {"status": "error", "error": "æªæ¾å°ää½å¯ç¨çEºå±çæå¼æEè¯·æ£æ¥ skills/sd_image_generator"}

    def _generate_image_to_image(self, input_image: str, prompt: str, negative_prompt: str, controlnet_type: str, strength: float, output_path: str) -> Dict:
        """æè¡å¾çå¾Eè°E¨ ControlNet"""
        if not CONTROLNET_AVAILABLE:
            return {"status": "error", "error": "æªæ¾å° ControlNet å¼æ (skills/controlnet_img2img)"}
        
        try:
            cn_engine = ControlNetImg2Img(config={'device': self.config.get('device', 'cpu')})
            result = cn_engine.execute(
                input_image_path=input_image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                preprocessor_type=controlnet_type,
                controlnet_model=controlnet_type,
                strength=strength,
                output_path=output_path
            )
            return result
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def execute(self, **kwargs) -> Dict[str, Any]:
        """æè¡æè½"""
        logger.info(f"æè¡æè½: {self.name} (v{self.version})")
        start_time = time.time()

        try:
            # 1. è£æåºæ¬åæ°
            mode = kwargs.get('mode', 'txt2img')
            prompt = kwargs.get('prompt', '')
            negative_prompt = kwargs.get('negative_prompt', 
                'worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature')
            style = kwargs.get('style', self.config.get('default_style', 'none'))
            
            # 2. åºç¨é¢E®¾é£æ ¼Eæ¯æäæ¬å°æç¤ºè¯åºå è½½EE
            if style and style != 'none':
                # å°è¯å è½½æ¬å°åç®å½ä¸ç .py æç¤ºè¯æä¶
                local_style = self._load_prompts_from_library(style)
                if local_style:
                    subjects = local_style.get('subjects', [])
                    local_styles = local_style.get('styles', [])
                    local_moods = local_style.get('moods', [])
                    
                    prompt_parts = []
                    if subjects:
                        prompt_parts.append(random.choice(subjects))
                    if local_styles:
                        prompt_parts.append(random.choice(local_styles))
                    if local_moods:
                        prompt_parts.append(random.choice(local_moods))
                    
                    # çEåE±æç¤ºè¯E
                    if prompt_parts:
                        if prompt:
                            prompt = f"{prompt}, {', '.join(prompt_parts)}"
                        else:
                            prompt = ", ".join(prompt_parts)
                        logger.info(f"ð å·²å è½½æ¬å°é£æ ¼ [ {style} ] çEEå±æç¤ºè¯çE")
                else:
                    # å¦ææ¬å°æ²¡æï¼åéå°åE½®é¢E®¾
                    prompt = self._apply_style_preset(style, prompt)

            # 3. åºç¡åæ°
            width = int(kwargs.get('width', self.config.get('default_width', 768)))
            height = int(kwargs.get('height', self.config.get('default_height', 1024)))
            steps = int(kwargs.get('steps', self.config.get('default_steps', 30)))
            cfg_scale = float(kwargs.get('cfg_scale', self.config.get('default_cfg', 7.5)))
            seed = int(kwargs.get('seed', -1))
            model_name = kwargs.get('model_name')
            output_path = kwargs.get('output_path', str(self.output_dir / f"mecha_{int(time.time())}.png"))

            # 4. æ ¡éªE
            if mode == 'txt2img' and not prompt:
                return {"status": "error", "error": "txt2img æ¨¡å¼ä¸å¿E¡æä¾Eprompt"}
            
            input_image = kwargs.get('input_image')
            if mode == 'img2img' and not input_image:
                # å¦ææ²¡ä¼  input_imageEèEå¨å¯æ¾æ¬ç®å½ä¸çåèE¾
                ref_imgs = sorted(list(self.skill_dir.glob("Gemini_Generated_Image*.png")))
                if ref_imgs:
                    input_image = str(ref_imgs[0])
                    logger.info(f"ð¼EEèªå¨ä½¿ç¨ç®å½ä¸ç¬¬ä¸å¼ åèE¾: {input_image}")
                else:
                    return {"status": "error", "error": "img2img æ¨¡å¼ä¸å¿E¡æä¾Einput_image"}

            # 5. æè¡çæE
            if mode == 'txt2img':
                result = self._generate_text_to_image(prompt, negative_prompt, width, height, steps, cfg_scale, seed, model_name)
            elif mode == 'img2img':
                controlnet_type = kwargs.get('controlnet_type', 'canny')
                strength = float(kwargs.get('strength', self.config.get('default_strength', 0.75)))
                result = self._generate_image_to_image(input_image, prompt, negative_prompt, controlnet_type, strength, output_path)
            else:
                return {"status": "error", "error": f"æªç¥æ¨¡å¼E {mode}"}

            # 6. å¤Eçæ
            if result.get('status') == 'success':
                elapsed = time.time() - start_time
                return {
                    "status": "success",
                    "result": {
                        "mode": mode,
                        "image_paths": result.get('image_paths', [output_path]),
                        "elapsed_time": f"{elapsed:.2f}s",
                        "prompt_used": prompt,
                        "used_model": model_name
                    },
                    "metadata": {
                        "skill": self.name,
                        "version": self.version,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
            else:
                return result

        except Exception as e:
            logger.error(f"æè¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
            
    def __repr__(self):
        return f"<Mechagenerator(name={self.name}, version={self.version})>"
"""