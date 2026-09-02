# skills/comics/manga_generator/skill.py
"""
AI 漫画生成器 - 核心编排器
整合所有图片处理和生成能力
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


MANGA_STYLES = {
    "manga": {"name": "日漫", "prompt": "manga style, black and white, high contrast, detailed linework, japanese manga"},
    "anime": {"name": "动漫", "prompt": "anime style, vibrant colors, cel shading, detailed eyes, beautiful"},
    "comic": {"name": "美漫", "prompt": "comic book style, bold colors, dramatic shading, american comic"},
    "webtoon": {"name": "条漫", "prompt": "webtoon style, clean lines, soft colors, korean webcomic, vertical layout"}
}

EMOTIONS = {
    "happy": "smiling, happy, joyful, bright eyes",
    "sad": "sad, melancholic, tearful eyes, gloomy",
    "angry": "angry, fierce, intense eyes, gritting teeth",
    "surprised": "surprised, wide eyes, mouth open, shocked",
    "focused": "focused, determined, concentrated, serious",
    "calm": "calm, peaceful, serene, gentle smile",
    "excited": "excited, bright eyes, energetic, enthusiastic",
    "scared": "scared, fearful, wide eyes, trembling",
    "thinking": "thinking, thoughtful, looking away, pensive"
}

POSES = {
    "standing": "standing upright, full body, straight posture",
    "sitting": "sitting down, relaxed posture, legs together",
    "lying": "lying down, relaxed, peaceful",
    "walking": "walking forward, dynamic motion, confident stride",
    "running": "running, dynamic, arms swinging, energetic",
    "kneeling": "kneeling on the ground, elegant posture",
    "jumping": "jumping in the air, dynamic, energetic"
}


class MangaGenerator:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_generator"
        self.version = "1.0.0"
        self.skill_dir = Path(__file__).parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._setup_config()
        logger.info(f"MangaGenerator v{self.version} 初始化完成")

    def _setup_config(self):
        defaults = {
            'default_style': 'manga',
            'default_pages': 4,
            'default_strength': 0.65,
            'default_steps': 30,
            'default_negative': 'ugly, deformed, bad anatomy, extra limbs, blurry, low quality'
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def execute(self, **kwargs) -> Dict[str, Any]:
        start_time = time.time()
        logger.info(f"生成漫画")

        try:
            style = kwargs.get('style', self.config.get('default_style', 'manga'))
            pages = int(kwargs.get('pages', self.config.get('default_pages', 4)))
            character_image = kwargs.get('character_image')
            enable_audio = kwargs.get('audio', False)
            export_formats = kwargs.get('export_formats', ['pdf'])
            
            # ========== 从剧本文件读取 ==========
            script_path = kwargs.get('script_path')
            script = None
            
            if script_path:
                logger.info(f"📖 从剧本文件读取: {script_path}")
                with open(script_path, 'r', encoding='utf-8') as f:
                    script = json.load(f)
                pages = script.get('total_pages', pages)
            else:
                # 从文本生成剧本
                source_type = kwargs.get('source_type', 'text')
                source_content = kwargs.get('source_content', '')
                template = kwargs.get('template', 'story')
                script = self._generate_script(source_type, source_content, template, pages)
            
            # ========== 生成每一页 ==========
            pages_data = []
            scenes = script.get('scenes', [])
            
            for i, scene in enumerate(scenes):
                page_num = scene.get('page', i + 1)
                description = scene.get('description', f'第{page_num}页')
                emotion = scene.get('emotion', 'neutral')
                pose = scene.get('pose', 'standing')
                dialogue = scene.get('dialogue', '')
                background = scene.get('background', '')
                
                logger.info(f"  生成第 {page_num} 页...")
                
                # 构建提示词
                prompt = self._build_prompt(description, emotion, pose, style, background)
                negative = kwargs.get('negative_prompt', self.config.get('default_negative'))
                strength = kwargs.get('strength', self.config.get('default_strength', 0.65))
                
                image_path = None
                
                # 如果有角色图，尝试用 change_pose
                if character_image:
                    try:
                        result = execute_skill(
                            "change_pose",
                            image_path=character_image,
                            pose=pose,
                            prompt=prompt,
                            negative_prompt=negative,
                            strength=strength,
                            steps=kwargs.get('steps', self.config.get('default_steps', 30))
                        )
                        if result and result.get('status') == 'success':
                            image_path = result.get('output_path')
                    except Exception as e:
                        logger.warning(f"change_pose 失败: {e}")
                
                # 如果 change_pose 失败，直接生成
                if not image_path:
                    image_path = self._generate_with_sd(prompt, negative, **kwargs)
                
                pages_data.append({
                    "page": page_num,
                    "description": description,
                    "emotion": emotion,
                    "pose": pose,
                    "dialogue": dialogue,
                    "image_path": image_path,
                    "prompt": prompt
                })
            
            # ========== 排版 ==========
            layout_path = self._create_layout(pages_data, script.get('title', '漫画'), style)
            
            # ========== 导出 ==========
            exported = self._export(pages_data, script, export_formats)
            
            # ========== 有声版 ==========
            audio_path = None
            if enable_audio:
                audio_path = self._generate_audio(script, pages_data)

            return {
                "status": "success",
                "output_path": str(layout_path),
                "audio_path": audio_path,
                "exported_files": exported,
                "pages": pages_data,
                "metadata": {
                    "title": script.get('title'),
                    "pages": len(pages_data),
                    "style": style,
                    "generation_time": f"{time.time() - start_time:.2f}s"
                }
            }
        except Exception as e:
            logger.error(f"生成失败: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def _generate_script(self, source_type, source_content, template, pages):
        if not source_content:
            source_content = f"一个关于冒险的故事，共{pages}页"
        pages_data = [{"page": i+1, "description": f"场景{i+1}: {source_content[:50]}", "emotion": "neutral", "pose": "standing", "dialogue": ""} for i in range(pages)]
        return {"title": "漫画故事", "description": source_content[:200], "scenes": pages_data}

    def _build_prompt(self, description, emotion, pose, style, background):
        parts = []
        if description:
            parts.append(description)
        if emotion in EMOTIONS:
            parts.append(EMOTIONS[emotion])
        if style in MANGA_STYLES:
            parts.append(MANGA_STYLES[style]['prompt'])
        if pose in POSES:
            parts.append(POSES[pose])
        if background:
            parts.append(f"background: {background}")
        parts.append("high quality, detailed, masterpiece, best quality")
        return ", ".join(parts)

    def _generate_with_sd(self, prompt, negative, **kwargs):
        try:
            result = execute_skill(
                "sd_image_generator",
                prompt=prompt,
                negative_prompt=negative,
                width=kwargs.get('width', 512),
                height=kwargs.get('height', 768),
                steps=kwargs.get('steps', self.config.get('default_steps', 30)),
                cfg_scale=kwargs.get('cfg_scale', 7.5),
                seed=kwargs.get('seed', -1)
            )
            if result and result.get('status') == 'success':
                paths = result.get('image_paths', [])
                return paths[0] if paths else None
            return None
        except Exception as e:
            logger.error(f"SD 生成失败: {e}")
            return None

    def _create_layout(self, pages_data, title, style):
        from PIL import Image, ImageDraw, ImageFont
        output_path = self.output_dir / f"comic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        valid = [p for p in pages_data if p.get('image_path') and Path(p['image_path']).exists()]
        if not valid:
            return output_path
        try:
            images = [Image.open(p['image_path']) for p in valid]
            w, h = 512, 768
            imgs = [img.resize((w, h), Image.Resampling.LANCZOS) for img in images]
            cols = 2 if len(imgs) > 2 else len(imgs)
            rows = (len(imgs) + cols - 1) // cols
            pad = 20
            canvas = Image.new('RGB', (cols * w + (cols+1)*pad, rows * h + (rows+1)*pad + 80), 'white')
            draw = ImageDraw.Draw(canvas)
            try:
                font = ImageFont.truetype("simhei.ttf", 36)
            except:
                font = ImageFont.load_default()
            draw.text((canvas.width//2 - len(title)*9, 20), title, fill='black', font=font)
            for i, img in enumerate(imgs):
                row = i // cols
                col = i % cols
                x = pad + col * (w + pad)
                y = 80 + row * (h + pad)
                canvas.paste(img, (x, y))
            canvas.save(output_path)
        except Exception as e:
            logger.error(f"排版失败: {e}")
        return output_path

    def _export(self, pages_data, script, formats):
        exported = []
        for fmt in formats:
            fmt = fmt.lower()
            if fmt == 'pdf':
                path = self._export_pdf(pages_data, script)
                if path:
                    exported.append(path)
        return exported

    def _export_pdf(self, pages_data, script):
        output_path = self.output_dir / f"comic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        image_paths = [p.get('image_path') for p in pages_data if p.get('image_path')]
        if not image_paths:
            return None
        try:
            import img2pdf
            with open(output_path, 'wb') as f:
                f.write(img2pdf.convert(image_paths))
            logger.info(f"PDF 导出: {output_path}")
            return str(output_path)
        except ImportError:
            logger.warning("img2pdf 未安装")
            return None
        except Exception as e:
            logger.error(f"PDF 导出失败: {e}")
            return None

    def _generate_audio(self, script, pages_data):
        try:
            text = "\n".join([p.get('dialogue', p.get('description', '')) for p in pages_data])
            if not text.strip():
                text = script.get('title', '漫画')
            result = execute_skill(
                "voice_assistant",
                action="tts",
                text=text,
                voice="zh-CN-XiaoxiaoNeural"
            )
            if result and result.get('status') == 'success':
                return result.get('result', {}).get('audio_path')
            return None
        except Exception as e:
            logger.error(f"音频生成失败: {e}")
            return None

    def __repr__(self):
        return f"<MangaGenerator(name={self.name})>"