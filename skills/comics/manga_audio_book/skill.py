# skills/comics/manga_audio_book/skill.py
"""
有声漫画生成器 - 将漫画转换为有声读物
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


# ============================================================
# 语音配置
# ============================================================
VOICE_CONFIG = {
    "zh-CN-XiaoxiaoNeural": {"name": "晓晓", "gender": "女", "language": "中文"},
    "zh-CN-YunyangNeural": {"name": "云阳", "gender": "男", "language": "中文"},
    "zh-CN-YunjianNeural": {"name": "云健", "gender": "男", "language": "中文"},
    "ja-JP-NanamiNeural": {"name": "七海", "gender": "女", "language": "日语"},
    "en-US-JennyNeural": {"name": "Jenny", "gender": "女", "language": "英语"},
}


class MangaAudioBook:
    """有声漫画生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_audio_book"
        self.version = "1.0.0"
        
        self.skill_dir = Path(__file__).parent
        self.output_dir = self.skill_dir / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._setup_logging()
        logger.info(f"MangaAudioBook v{self.version} 初始化完成")
        logger.info(f"  支持语音: {list(VOICE_CONFIG.keys())}")
    
    def _setup_logging(self):
        log_level = self.config.get('log_level', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """生成有声漫画"""
        start_time = time.time()
        
        script_data = kwargs.get('script_data')  # 包含每页文本
        image_paths = kwargs.get('image_paths', [])
        voice = kwargs.get('voice', 'zh-CN-XiaoxiaoNeural')
        speed = kwargs.get('speed', 1.0)
        output_path = kwargs.get('output_path')
        
        if not script_data and not image_paths:
            return {"status": "error", "error": "需要提供 script_data 或 image_paths"}
        
        if not output_path:
            from datetime import datetime
            output_path = str(self.output_dir / f"audiobook_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🔊 生成有声漫画: {output_path.name}")
        logger.info(f"🎤 语音: {voice}")
        logger.info(f"📁 图片数: {len(image_paths)}")
        
        try:
            # 构建文本
            text = self._build_text(script_data, image_paths)
            
            if not text.strip():
                return {"status": "error", "error": "没有可朗读的文本"}
            
            logger.info(f"📝 总字数: {len(text)}")
            
            # 使用 voice_assistant 生成音频
            result = execute_skill(
                "voice_assistant",
                action="tts",
                text=text,
                voice=voice,
                speed=speed,
                output_file=str(output_path)
            )
            
            if result and result.get('status') == 'success':
                audio_path = result.get('result', {}).get('audio_path', str(output_path))
                return {
                    "status": "success",
                    "output_path": audio_path,
                    "duration": result.get('duration', 0),
                    "text_length": len(text),
                    "voice": voice,
                    "metadata": {
                        "voice_name": VOICE_CONFIG.get(voice, {}).get('name', voice),
                        "speed": speed,
                        "generation_time": f"{time.time() - start_time:.2f}s"
                    }
                }
            else:
                error = result.get('error', '未知错误') if result else '执行失败'
                return {"status": "error", "error": error}
            
        except Exception as e:
            logger.error(f"有声漫画生成失败: {e}")
            return {"status": "error", "error": str(e)}
    
    def _build_text(self, script_data: Dict, image_paths: List[str]) -> str:
        """构建朗读文本"""
        parts = []
        
        # 如果有剧本数据
        if script_data:
            title = script_data.get('title', '漫画')
            parts.append(f"欢迎收听《{title}》")
            parts.append("")
            
            scenes = script_data.get('scenes', [])
            for scene in scenes:
                page_num = scene.get('page', len(parts))
                description = scene.get('description', '')
                dialogue = scene.get('dialogue', '')
                
                if description:
                    parts.append(f"第{page_num}页: {description}")
                if dialogue:
                    parts.append(dialogue)
                parts.append("")
        
        # 如果只有图片，为每张图片生成描述
        elif image_paths:
            parts.append("漫画有声版")
            parts.append("")
            for i, img_path in enumerate(image_paths):
                parts.append(f"第{i+1}页")
                parts.append(f"图片: {Path(img_path).stem}")
                parts.append("")
        
        return "\n".join(parts)
    
    def generate_from_pages(self, pages_data: List[Dict], **kwargs) -> Dict[str, Any]:
        """从页面数据生成有声版"""
        script_data = {
            "title": kwargs.get('title', '漫画'),
            "scenes": []
        }
        
        for i, page in enumerate(pages_data):
            script_data["scenes"].append({
                "page": i + 1,
                "description": page.get('description', ''),
                "dialogue": page.get('dialogue', '')
            })
        
        return self.execute(script_data=script_data, **kwargs)
    
    def __repr__(self):
        return f"<MangaAudioBook(name={self.name}, version={self.version})>"