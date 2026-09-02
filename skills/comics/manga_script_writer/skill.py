# skills/comics/manga_script_writer/skill.py
"""
漫画剧本生成器 - 增强版
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

import sys
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


class MangaScriptWriter:
    """漫画剧本生成器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_script_writer"
        self.version = "1.0.0"
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"MangaScriptWriter v{self.version} 初始化完成")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """生成剧本"""
        genre = kwargs.get('genre', '冒险')
        theme = kwargs.get('theme', '友情与成长')
        pages = int(kwargs.get('pages', 4))
        characters = kwargs.get('characters', '主角, 朋友')
        setting = kwargs.get('setting', '奇幻世界')
        plot = kwargs.get('plot', '')
        chapter_count = int(kwargs.get('chapter_count', 1))
        
        try:
            # ========== 方法1: 尝试用 novel_writer 生成 ==========
            story_text = self._generate_with_novel_writer(genre, theme, characters, setting, plot, chapter_count)
            
            # ========== 如果 novel_writer 失败，用模板生成 ==========
            if not story_text or len(story_text) < 50:
                logger.warning("novel_writer 生成内容不足，使用模板生成")
                story_text = self._generate_with_template(genre, theme, characters, setting, pages)
            
            # ========== 分镜 ==========
            script = self._create_script(story_text, pages, characters, setting, genre, theme)
            
            # ========== 保存 ==========
            from datetime import datetime
            output_file = self.output_dir / f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "success",
                "script": script,
                "output_path": str(output_file),
                "story_text": story_text[:500],
                "metadata": {
                    "genre": genre,
                    "theme": theme,
                    "pages": pages,
                    "characters": characters,
                    "setting": setting,
                    "chapter_count": chapter_count
                }
            }
            
        except Exception as e:
            logger.error(f"剧本生成失败: {e}")
            import traceback
            traceback.print_exc()
            script = self._create_default_script(genre, theme, pages, characters, setting)
            return {
                "status": "success",
                "script": script,
                "metadata": {"error": str(e), "fallback": True}
            }
    
    def _generate_with_novel_writer(self, genre, theme, characters, setting, plot, chapter_count):
        """使用 novel_writer 生成故事"""
        # 构建更详细的提示词
        outline = f"""请生成一个{genre}题材的短篇漫画故事。

【世界观】{setting}
【主题】{theme}
【角色】{characters}

故事要求：
1. 有完整的起承转合
2. 角色之间有互动和对话
3. 场景描述生动

请用小说叙述方式写这个故事。"""
        
        if plot:
            outline += f"\n【剧情梗概】{plot}"
        
        logger.info(f"📝 调用 novel_writer，提示词长度: {len(outline)}")
        
        try:
            result = execute_skill(
                "novel_writer",
                genre=genre,
                title=f"{genre}{theme}故事",
                outline=outline,
                characters=characters,
                chapter_count=chapter_count,
                model="qwen2.5:7b"
            )
            
            if result and result.get('status') == 'success':
                result_data = result.get('result', {})
                # 尝试多个字段
                for field in ['content', 'story', 'text', 'full_text']:
                    if result_data.get(field):
                        content = result_data[field]
                        if len(content) > 50:
                            logger.info(f"✅ 从字段 '{field}' 获取内容，长度: {len(content)}")
                            return content
                
                # 如果 result_data 本身是字符串
                if isinstance(result_data, str) and len(result_data) > 50:
                    return result_data
                
                logger.warning(f"novel_writer 返回数据中未找到内容字段: {result_data.keys()}")
                return ""
            else:
                error = result.get('error', '未知错误') if result else '无返回值'
                logger.warning(f"novel_writer 返回失败: {error}")
                return ""
                
        except Exception as e:
            logger.error(f"novel_writer 调用异常: {e}")
            return ""
    
    def _generate_with_template(self, genre, theme, characters, setting, pages):
        """使用模板生成故事"""
        char_list = [c.strip() for c in characters.split(',') if c.strip()]
        protagonist = char_list[0] if char_list else "主角"
        
        story = f"在{setting}，{protagonist}踏上了一段{genre}冒险。\n\n"
        story += f"这次冒险的主题是{theme}。\n\n"
        
        scene_templates = [
            f"{protagonist}在{setting}的森林中遇到了{char_list[1] if len(char_list) > 1 else '伙伴'}。",
            f"他们一起面对了第一个挑战，展现了{theme}的力量。",
            f"在旅途中，他们遇到了神秘的{setting}遗迹。",
            f"一场激烈的{genre}战斗爆发了。",
            f"通过智慧和勇气，他们找到了解决之道。",
            f"最终，{protagonist}和伙伴们达成了目标，{theme}得到了升华。"
        ]
        
        for i in range(min(pages, len(scene_templates))):
            story += f"{i+1}. {scene_templates[i]}\n"
        
        while len(story.split('\n')) < pages + 1:
            story += f"{len(story.split('\n'))}. {protagonist}继续前行...\n"
        
        return story
    
    def _create_script(self, story: str, pages: int, characters: str, setting: str, genre: str, theme: str) -> Dict:
        """创建分镜剧本"""
        char_list = [c.strip() for c in characters.split(',') if c.strip()]
        protagonist = char_list[0] if char_list else "主角"
        
        # 按段落分割
        paragraphs = [p.strip() for p in story.split('\n') if p.strip()]
        
        # 如果段落不够，按句号分割
        if len(paragraphs) < pages:
            sentences = re.split(r'[。！？.!?]', story)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
            if len(sentences) >= pages:
                paragraphs = sentences[:pages]
        
        # 如果还不够，生成场景
        while len(paragraphs) < pages:
            paragraphs.append(f"第{len(paragraphs)+1}幕：{protagonist}继续冒险")
        
        # 取前 pages 个
        scenes = paragraphs[:pages]
        
        # 情绪和姿态循环
        emotions = ["happy", "focused", "calm", "excited", "thinking", "surprised"]
        poses = ["standing", "walking", "sitting", "jumping", "kneeling", "running"]
        backgrounds = [setting, f"{setting}的森林", f"{setting}的城堡", f"{setting}的山脉", f"{setting}的村庄", f"{setting}的河流"]
        
        scenes_data = []
        for i, desc in enumerate(scenes):
            # 提取对话
            dialogue = self._extract_dialogue(desc)
            
            scenes_data.append({
                "page": i + 1,
                "description": desc[:200],
                "characters_in_scene": char_list,
                "emotion": emotions[i % len(emotions)],
                "pose": poses[i % len(poses)],
                "dialogue": dialogue,
                "background": backgrounds[i % len(backgrounds)]
            })
        
        return {
            "title": f"{genre}{theme}故事",
            "total_pages": pages,
            "characters": char_list,
            "setting": setting,
            "genre": genre,
            "theme": theme,
            "scenes": scenes_data
        }
    
    def _create_default_script(self, genre: str, theme: str, pages: int, characters: str, setting: str) -> Dict:
        """创建默认剧本"""
        char_list = [c.strip() for c in characters.split(',') if c.strip()]
        protagonist = char_list[0] if char_list else "主角"
        
        emotions = ["happy", "focused", "calm", "excited", "thinking", "surprised"]
        poses = ["standing", "walking", "sitting", "jumping", "kneeling", "running"]
        backgrounds = [setting, f"{setting}的森林", f"{setting}的城堡", f"{setting}的山脉", f"{setting}的村庄", f"{setting}的河流"]
        
        scenes = []
        for i in range(pages):
            scenes.append({
                "page": i + 1,
                "description": f"{protagonist}在{backgrounds[i % len(backgrounds)]}中继续{genre}冒险，{theme}的主题贯穿始终",
                "characters_in_scene": char_list,
                "emotion": emotions[i % len(emotions)],
                "pose": poses[i % len(poses)],
                "dialogue": "",
                "background": backgrounds[i % len(backgrounds)]
            })
        
        return {
            "title": f"{genre}{theme}故事",
            "total_pages": pages,
            "characters": char_list,
            "setting": setting,
            "genre": genre,
            "theme": theme,
            "scenes": scenes
        }
    
    def _extract_dialogue(self, text: str) -> str:
        """提取对话"""
        dialogues = re.findall(r'[""](.*?)[""]', text)
        dialogues.extend(re.findall(r'“(.*?)”', text))
        dialogues.extend(re.findall(r"'(.*?)'", text))
        dialogues.extend(re.findall(r'《(.*?)》', text))
        return ' '.join(dialogues) if dialogues else ''
    
    def __repr__(self):
        return f"<MangaScriptWriter(name={self.name})>"