"""
MechaGenerator - æºç²å°å¥³/æºå¨äººé«ç«¯æEå¾ä¸å¾çå¾çæEå¨

è¾åEåæ°:
  - mode (string): çæEæ¨¡å¼E("txt2img" æEå¾ / "img2img" å¾çå¾)
  - prompt (string): æ­£é¢æç¤ºè¯E(å¿E¡«, txt2img)
  - negative_prompt (string): è´é¢æç¤ºè¯E
  - input_image (string): å¾çå¾çE¾åEå¾çE·¯å¾E(img2imgæ¨¡å¼ä¸å¿E¡«)
  - output_path (string): è¾åEè·¯å¾E(å¯éï¼é»è®¤èªå¨çæE)
  - width (int): å®½åº¦ (é»è®¤ 768)
  - height (int): é«åº¦ (é»è®¤ 1024)
  - steps (int): è¿­ä»£æ­¥æ° (é»è®¤ 30)
  - cfg_scale (float): æç¤ºè¯å¼å¯¼ç³»æ° (é»è®¤ 7.5)
  - seed (int): éæºç§å­E(é»è®¤ -1 éæº)
  - model_name (string): ä½¿ç¨åªä¸ªåºæ¨¡ (é»è®¤è¯»åç¨æ·å¨å±éç½®)
  - style (string): é¢E®¾é£æ ¼ (å¯¹åºæ¬å°æç¤ºè¯æä»¶Eå¦Emecha_glow / mecha_girl / none)
  - controlnet_type (string): img2imgæ¨¡å¼ä¸çå§¿ææ§å¶ ("openpose", "canny", "depth" ç­E
  - strength (float): å¾çå¾éç»å¼ºåº¦ (0.0-1.0Eé»è®¤ 0.75)

è¾åE:
  - status: æ§è¡ç¶æE
  - image_paths: çæEå¾çEè·¯å¾EEè¡¨
  - used_model: å®éä½¿ç¨çEºæ¨¡åç§°
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

# å¯¼å¥æ¡E¶åE¨ç»E»¶
try:
    from markflow.utils.model_config import get_models, get_loras, get_model_config, resolve_model_path
    from markflow.cli.commands import execute_skill
    MODEL_UTILS_AVAILABLE = True
except ImportError:
    MODEL_UTILS_AVAILABLE = False
    logger.warning("æªè½å¯¼å¥ Markflow æ¨¡åéEç½®å·¥å·")

# å°è¯å¯¼å¥ ControlNet
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False

# å°è¯å¯¼å¥ SD å¾åçæä¸»å¼æ
try:
    from skills.sd_image_generator.skill import Sdimagegenerator
    SD_ENGINE_AVAILABLE = True
except ImportError:
    SD_ENGINE_AVAILABLE = False
    logger.warning("æªè½å¯¼å¥ SD ä¸»å¼æEå°è¯å¯»æ¾å¶ä»å¼æ")


class Mechagenerator:
    """æºç²å°å¥³çæEå¨Eæ¯ææçå¾ãå¾çå¾ååEå±æç¤ºè¯ç»E"""

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
        """åå§ååºå±çæå¼æ"""
        self.sd_engine = None
        if SD_ENGINE_AVAILABLE:
            try:
                self.sd_engine = Sdimagegenerator(config={'device': self.config.get('device', 'cpu')})
                logger.info("SD ä¸»å¼æå è½½æå")
            except Exception as e:
                logger.warning(f"SD ä¸»å¼æåå§åå¤±è´¥: {e}")

        # å¦æä¸»å¼æä¸å¯ç¨Eå°è¯å¯»æ¾å¶ä»åºå±E
        if not self.sd_engine:
            # å°è¯å¯¼å¥é¡¹ç®ä¸­çEgenerate_images çæEå¨
            try:
                sys.path.insert(0, str(project_root / "scripts"))
                from generate_images import SDImageGenerator
                self.script_generator = SDImageGenerator()
                logger.info("Scripts ç®å½ä¸çå¾çEæå¨å è½½æå")
            except Exception as e:
                logger.warning(f"Scripts çæEå¨å è½½å¤±è´¥: {e}")

    def _apply_style_preset(self, style: str, prompt: str) -> str:
        """æ ¹æ®é¢E®¾é£æ ¼æåæç¤ºè¯å¢å¼º (å½æ¬å°æ æ­¤æE»¶æ¶çEéæºå¶)"""
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
        """ä»å½åæè½ç®å½å è½½æç¤ºè¯åºï¼èEå¨ééEæ¬å°æE»¶EE""
        local_py_files = list(self.skill_dir.glob("*.py"))
        
        for py_file in local_py_files:
            if py_file.name == "skill.py":
                continue
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"style_module_{py_file.stem}", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # æ ¸å¿E¼èEå¨å¯»æ¾æE»¶éç STYLE å­åEEå¹¶å¹éåEé®å­E
                if hasattr(module, 'STYLE'):
                    styles = module.STYLE
                    # å¹éæä»¶åçå³é®è¯ï¼æEèE­åEéç key
                    for key in styles.keys():
                        if style_name in key or style_name in py_file.stem:
                            return styles[key]
            except Exception as e:
                logger.warning(f"å è½½æç¤ºè¯æä»¶ {py_file.name} å¤±è´¥: {e}")
        
        return {}
        
    def _generate_text_to_image(self, prompt: str, negative_prompt: str, width: int, height: int, steps: int, cfg: float, seed: int, model_name: Optional[str]) -> Dict:
        """æ§è¡æçå¾"""
        
        # ===== æ ¸å¿E¿®æ¹Eå¨æè·åç¨æ·éç½®çE¨¡åE=====
        # ä»Emodel_config.py ä¸­æ¿å°å½åç¨æ·éå®çæ¨¡åE
        try:
            from markflow.utils.model_config import get_model_config
            global_sd_config = get_model_config()
            if not model_name and global_sd_config.get('model_path'):
                model_name = global_sd_config.get('model_name')  # è·åéEç½®çE¨¡åå
        except Exception as e:
            logger.warning(f"è·ååEå±æ¨¡åéEç½®å¤±è´¥: {e}")

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
                return {"status": "error", "error": result.get('error', 'SDå¼æå¤±è´¥')}
            except Exception as e:
                logger.error(f"SDå¼æå¼å¸¸: {e}")
                return {"status": "error", "error": str(e)}

        # åéå°èæ¬çæEå¨
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

        return {"status": "error", "error": "æªæ¾å°ä»»ä½å¯ç¨çEºå±çæå¼æEè¯·æ£æ¥ skills/sd_image_generator"}

    def _generate_image_to_image(self, input_image: str, prompt: str, negative_prompt: str, controlnet_type: str, strength: float, output_path: str) -> Dict:
        """æ§è¡å¾çå¾Eè°E¨ ControlNet"""
        if not CONTROLNET_AVAILABLE:
            return {"status": "error", "error": "æªæ¾å° ControlNet å¼æ (skills/controlnet_img2img)"}
        
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
        """æ§è¡æè½"""
        logger.info(f"æ§è¡æè½: {self.name} (v{self.version})")
        start_time = time.time()

        try:
            # 1. è§£æåºæ¬åæ°
            mode = kwargs.get('mode', 'txt2img')
            prompt = kwargs.get('prompt', '')
            negative_prompt = kwargs.get('negative_prompt', 
                'worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature')
            style = kwargs.get('style', self.config.get('default_style', 'none'))
            
            # 2. åºç¨é¢E®¾é£æ ¼Eæ¯æä»æ¬å°æç¤ºè¯åºå è½½EE
            if style and style != 'none':
                # å°è¯å è½½æ¬å°åç®å½ä¸ç .py æç¤ºè¯æä»¶
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
                    
                    # ç»EåE±æç¤ºè¯E
                    if prompt_parts:
                        if prompt:
                            prompt = f"{prompt}, {', '.join(prompt_parts)}"
                        else:
                            prompt = ", ".join(prompt_parts)
                        logger.info(f"ð å·²å è½½æ¬å°é£æ ¼ [ {style} ] çEEå±æç¤ºè¯ç»E")
                else:
                    # å¦ææ¬å°æ²¡æï¼åéå°åE½®é¢E®¾
                    prompt = self._apply_style_preset(style, prompt)

            # 3. åºç¡åæ°
            width = int(kwargs.get('width', self.config.get('default_width', 768)))
            height = int(kwargs.get('height', self.config.get('default_height', 1024)))
            steps = int(kwargs.get('steps', self.config.get('default_steps', 30)))
            cfg_scale = float(kwargs.get('cfg_scale', self.config.get('default_cfg', 7.5)))
            seed = int(kwargs.get('seed', -1))
            model_name = kwargs.get('model_name')
            output_path = kwargs.get('output_path', str(self.output_dir / f"mecha_{int(time.time())}.png"))

            # 4. æ ¡éªE
            if mode == 'txt2img' and not prompt:
                return {"status": "error", "error": "txt2img æ¨¡å¼ä¸å¿E¡»æä¾Eprompt"}
            
            input_image = kwargs.get('input_image')
            if mode == 'img2img' and not input_image:
                # å¦ææ²¡ä¼  input_imageEèEå¨å¯»æ¾æ¬ç®å½ä¸çåèE¾
                ref_imgs = sorted(list(self.skill_dir.glob("Gemini_Generated_Image*.png")))
                if ref_imgs:
                    input_image = str(ref_imgs[0])
                    logger.info(f"ð¼EEèªå¨ä½¿ç¨ç®å½ä¸ç¬¬ä¸å¼ åèE¾: {input_image}")
                else:
                    return {"status": "error", "error": "img2img æ¨¡å¼ä¸å¿E¡»æä¾Einput_image"}

            # 5. æ§è¡çæE
            if mode == 'txt2img':
                result = self._generate_text_to_image(prompt, negative_prompt, width, height, steps, cfg_scale, seed, model_name)
            elif mode == 'img2img':
                controlnet_type = kwargs.get('controlnet_type', 'canny')
                strength = float(kwargs.get('strength', self.config.get('default_strength', 0.75)))
                result = self._generate_image_to_image(input_image, prompt, negative_prompt, controlnet_type, strength, output_path)
            else:
                return {"status": "error", "error": f"æªç¥æ¨¡å¼E {mode}"}

            # 6. å¤Eç»æ
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
            logger.error(f"æ§è¡å¤±è´¥: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
            
    def __repr__(self):
        return f"<Mechagenerator(name={self.name}, version={self.version})>"