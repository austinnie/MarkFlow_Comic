"""
MechaGenerator - 譛ｺ逕ｲ蟆大･ｳ/譛ｺ蝎ｨ莠ｺ鬮倡ｫｯ譁・函蝗ｾ荳主崟逕溷崟逕滓・蝎ｨ

霎灘・蜿よ焚:
  - mode (string): 逕滓・讓｡蠑・("txt2img" 譁・函蝗ｾ / "img2img" 蝗ｾ逕溷崟)
  - prompt (string): 豁｣髱｢謠千､ｺ隸・(蠢・｡ｫ, txt2img)
  - negative_prompt (string): 雍滄擇謠千､ｺ隸・
  - input_image (string): 蝗ｾ逕溷崟逧・ｾ灘・蝗ｾ迚・ｷｯ蠕・(img2img讓｡蠑丈ｸ句ｿ・｡ｫ)
  - output_path (string): 霎灘・霍ｯ蠕・(蜿ｯ騾会ｼ碁ｻ倩ｮ､閾ｪ蜉ｨ逕滓・)
  - width (int): 螳ｽ蠎ｦ (鮟倩ｮ､ 768)
  - height (int): 鬮伜ｺｦ (鮟倩ｮ､ 1024)
  - steps (int): 霑ｭ莉｣豁･謨ｰ (鮟倩ｮ､ 30)
  - cfg_scale (float): 謠千､ｺ隸榊ｼ募ｯｼ邉ｻ謨ｰ (鮟倩ｮ､ 7.5)
  - seed (int): 髫乗惻遘榊ｭ・(鮟倩ｮ､ -1 髫乗惻)
  - model_name (string): 菴ｿ逕ｨ蜩ｪ荳ｪ蠎墓ｨ｡ (鮟倩ｮ､隸ｻ蜿也畑謌ｷ蜈ｨ螻驟咲ｽｮ)
  - style (string): 鬚・ｮｾ鬟取ｼ (蟇ｹ蠎疲悽蝨ｰ謠千､ｺ隸肴枚莉ｶ・悟ｦ・mecha_glow / mecha_girl / none)
  - controlnet_type (string): img2img讓｡蠑丈ｸ狗噪蟋ｿ諤∵而蛻ｶ ("openpose", "canny", "depth" 遲・
  - strength (float): 蝗ｾ逕溷崟驥咲ｻ伜ｼｺ蠎ｦ (0.0-1.0・碁ｻ倩ｮ､ 0.75)

霎灘・:
  - status: 謇ｧ陦檎憾諤・
  - image_paths: 逕滓・蝗ｾ迚・噪霍ｯ蠕・・陦ｨ
  - used_model: 螳樣刔菴ｿ逕ｨ逧・ｺ墓ｨ｡蜷咲ｧｰ
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

# 蟇ｼ蜈･譯・楔蜀・Κ扈・ｻｶ
try:
    from markflow.utils.model_config import get_models, get_loras, get_model_config, resolve_model_path
    from markflow.cli.commands import execute_skill
    MODEL_UTILS_AVAILABLE = True
except ImportError:
    MODEL_UTILS_AVAILABLE = False
    logger.warning("譛ｪ閭ｽ蟇ｼ蜈･ Markflow 讓｡蝙矩・鄂ｮ蟾･蜈ｷ")

# 蟆晁ｯ募ｯｼ蜈･ ControlNet
try:
    from skills.image.controlnet_img2img.skill import ControlNetImg2Img
    CONTROLNET_AVAILABLE = True
except ImportError:
    CONTROLNET_AVAILABLE = False

# 蟆晁ｯ募ｯｼ蜈･ SD 蝗ｾ蜒冗函謌蝉ｸｻ蠑墓梼
try:
    from skills.sd_image_generator.skill import Sdimagegenerator
    SD_ENGINE_AVAILABLE = True
except ImportError:
    SD_ENGINE_AVAILABLE = False
    logger.warning("譛ｪ閭ｽ蟇ｼ蜈･ SD 荳ｻ蠑墓梼・悟ｰ晁ｯ募ｯｻ謇ｾ蜈ｶ莉門ｼ墓梼")


class Mechagenerator:
    """譛ｺ逕ｲ蟆大･ｳ逕滓・蝎ｨ・壽髪謖∵枚逕溷崟縲∝崟逕溷崟蜥悟・螻よ署遉ｺ隸咲ｻ・粋"""

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
        """蛻晏ｧ句喧蠎募ｱら函謌仙ｼ墓梼"""
        self.sd_engine = None
        if SD_ENGINE_AVAILABLE:
            try:
                self.sd_engine = Sdimagegenerator(config={'device': self.config.get('device', 'cpu')})
                logger.info("SD 荳ｻ蠑墓梼蜉霓ｽ謌仙粥")
            except Exception as e:
                logger.warning(f"SD 荳ｻ蠑墓梼蛻晏ｧ句喧螟ｱ雍･: {e}")

        # 螯よ棡荳ｻ蠑墓梼荳榊庄逕ｨ・悟ｰ晁ｯ募ｯｻ謇ｾ蜈ｶ莉門ｺ募ｱ・
        if not self.sd_engine:
            # 蟆晁ｯ募ｯｼ蜈･鬘ｹ逶ｮ荳ｭ逧・generate_images 逕滓・蝎ｨ
            try:
                sys.path.insert(0, str(project_root / "scripts"))
                from generate_images import SDImageGenerator
                self.script_generator = SDImageGenerator()
                logger.info("Scripts 逶ｮ蠖穂ｸ狗噪蝗ｾ迚・函謌仙勣蜉霓ｽ謌仙粥")
            except Exception as e:
                logger.warning(f"Scripts 逕滓・蝎ｨ蜉霓ｽ螟ｱ雍･: {e}")

    def _apply_style_preset(self, style: str, prompt: str) -> str:
        """譬ｹ謐ｮ鬚・ｮｾ鬟取ｼ謠仙叙謠千､ｺ隸榊｢槫ｼｺ (蠖捺悽蝨ｰ譌豁､譁・ｻｶ譌ｶ逧・屓騾譛ｺ蛻ｶ)"""
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
        """莉主ｽ灘燕謚閭ｽ逶ｮ蠖募刈霓ｽ謠千､ｺ隸榊ｺ難ｼ郁・蜉ｨ騾る・譛ｬ蝨ｰ譁・ｻｶ・・""
        local_py_files = list(self.skill_dir.glob("*.py"))
        
        for py_file in local_py_files:
            if py_file.name == "skill.py":
                continue
            
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"style_module_{py_file.stem}", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 譬ｸ蠢・ｼ夊・蜉ｨ蟇ｻ謇ｾ譁・ｻｶ驥檎噪 STYLE 蟄怜・・悟ｹｶ蛹ｹ驟榊・髞ｮ蟄・
                if hasattr(module, 'STYLE'):
                    styles = module.STYLE
                    # 蛹ｹ驟肴枚莉ｶ蜷咲噪蜈ｳ髞ｮ隸搾ｼ梧・閠・ｭ怜・驥檎噪 key
                    for key in styles.keys():
                        if style_name in key or style_name in py_file.stem:
                            return styles[key]
            except Exception as e:
                logger.warning(f"蜉霓ｽ謠千､ｺ隸肴枚莉ｶ {py_file.name} 螟ｱ雍･: {e}")
        
        return {}
        
    def _generate_text_to_image(self, prompt: str, negative_prompt: str, width: int, height: int, steps: int, cfg: float, seed: int, model_name: Optional[str]) -> Dict:
        """謇ｧ陦梧枚逕溷崟"""
        
        # ===== 譬ｸ蠢・ｿｮ謾ｹ・壼勘諤∬執蜿也畑謌ｷ驟咲ｽｮ逧・ｨ｡蝙・=====
        # 莉・model_config.py 荳ｭ諡ｿ蛻ｰ蠖灘燕逕ｨ謌ｷ騾牙ｮ夂噪讓｡蝙・
        try:
            from markflow.utils.model_config import get_model_config
            global_sd_config = get_model_config()
            if not model_name and global_sd_config.get('model_path'):
                model_name = global_sd_config.get('model_name')  # 闔ｷ蜿夜・鄂ｮ逧・ｨ｡蝙句錐
        except Exception as e:
            logger.warning(f"闔ｷ蜿門・螻讓｡蝙矩・鄂ｮ螟ｱ雍･: {e}")

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
                return {"status": "error", "error": result.get('error', 'SD蠑墓梼螟ｱ雍･')}
            except Exception as e:
                logger.error(f"SD蠑墓梼蠑ょｸｸ: {e}")
                return {"status": "error", "error": str(e)}

        # 蝗樣蛻ｰ閼壽悽逕滓・蝎ｨ
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

        return {"status": "error", "error": "譛ｪ謇ｾ蛻ｰ莉ｻ菴募庄逕ｨ逧・ｺ募ｱら函謌仙ｼ墓梼・瑚ｯｷ譽譟･ skills/sd_image_generator"}

    def _generate_image_to_image(self, input_image: str, prompt: str, negative_prompt: str, controlnet_type: str, strength: float, output_path: str) -> Dict:
        """謇ｧ陦悟崟逕溷崟・瑚ｰ・畑 ControlNet"""
        if not CONTROLNET_AVAILABLE:
            return {"status": "error", "error": "譛ｪ謇ｾ蛻ｰ ControlNet 蠑墓梼 (skills/controlnet_img2img)"}
        
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
        """謇ｧ陦梧橿閭ｽ"""
        logger.info(f"謇ｧ陦梧橿閭ｽ: {self.name} (v{self.version})")
        start_time = time.time()

        try:
            # 1. 隗｣譫仙渕譛ｬ蜿よ焚
            mode = kwargs.get('mode', 'txt2img')
            prompt = kwargs.get('prompt', '')
            negative_prompt = kwargs.get('negative_prompt', 
                'worst quality, low quality, ugly, deformed, blurry, bad anatomy, bad hands, missing fingers, extra digits, watermark, text, signature')
            style = kwargs.get('style', self.config.get('default_style', 'none'))
            
            # 2. 蠎皮畑鬚・ｮｾ鬟取ｼ・域髪謖∽ｻ取悽蝨ｰ謠千､ｺ隸榊ｺ灘刈霓ｽ・・
            if style and style != 'none':
                # 蟆晁ｯ募刈霓ｽ譛ｬ蝨ｰ蜷檎岼蠖穂ｸ狗噪 .py 謠千､ｺ隸肴枚莉ｶ
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
                    
                    # 扈・粋蛻・ｱよ署遉ｺ隸・
                    if prompt_parts:
                        if prompt:
                            prompt = f"{prompt}, {', '.join(prompt_parts)}"
                        else:
                            prompt = ", ".join(prompt_parts)
                        logger.info(f"唐 蟾ｲ蜉霓ｽ譛ｬ蝨ｰ鬟取ｼ [ {style} ] 逧・・螻よ署遉ｺ隸咲ｻ・粋")
                else:
                    # 螯よ棡譛ｬ蝨ｰ豐｡譛会ｼ悟屓騾蛻ｰ蜀・ｽｮ鬚・ｮｾ
                    prompt = self._apply_style_preset(style, prompt)

            # 3. 蝓ｺ遑蜿よ焚
            width = int(kwargs.get('width', self.config.get('default_width', 768)))
            height = int(kwargs.get('height', self.config.get('default_height', 1024)))
            steps = int(kwargs.get('steps', self.config.get('default_steps', 30)))
            cfg_scale = float(kwargs.get('cfg_scale', self.config.get('default_cfg', 7.5)))
            seed = int(kwargs.get('seed', -1))
            model_name = kwargs.get('model_name')
            output_path = kwargs.get('output_path', str(self.output_dir / f"mecha_{int(time.time())}.png"))

            # 4. 譬｡鬪・
            if mode == 'txt2img' and not prompt:
                return {"status": "error", "error": "txt2img 讓｡蠑丈ｸ句ｿ・｡ｻ謠蝉ｾ・prompt"}
            
            input_image = kwargs.get('input_image')
            if mode == 'img2img' and not input_image:
                # 螯よ棡豐｡莨 input_image・瑚・蜉ｨ蟇ｻ謇ｾ譛ｬ逶ｮ蠖穂ｸ狗噪蜿り・崟
                ref_imgs = sorted(list(self.skill_dir.glob("Gemini_Generated_Image*.png")))
                if ref_imgs:
                    input_image = str(ref_imgs[0])
                    logger.info(f"名・・閾ｪ蜉ｨ菴ｿ逕ｨ逶ｮ蠖穂ｸ狗ｬｬ荳蠑蜿り・崟: {input_image}")
                else:
                    return {"status": "error", "error": "img2img 讓｡蠑丈ｸ句ｿ・｡ｻ謠蝉ｾ・input_image"}

            # 5. 謇ｧ陦檎函謌・
            if mode == 'txt2img':
                result = self._generate_text_to_image(prompt, negative_prompt, width, height, steps, cfg_scale, seed, model_name)
            elif mode == 'img2img':
                controlnet_type = kwargs.get('controlnet_type', 'canny')
                strength = float(kwargs.get('strength', self.config.get('default_strength', 0.75)))
                result = self._generate_image_to_image(input_image, prompt, negative_prompt, controlnet_type, strength, output_path)
            else:
                return {"status": "error", "error": f"譛ｪ遏･讓｡蠑・ {mode}"}

            # 6. 螟・炊扈捺棡
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
            logger.error(f"謇ｧ陦悟､ｱ雍･: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
            
    def __repr__(self):
        return f"<Mechagenerator(name={self.name}, version={self.version})>"