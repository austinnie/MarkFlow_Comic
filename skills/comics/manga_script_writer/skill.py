# skills/comics/manga_script_writer/skill.py
"""
漫画剧本生成器 - 增强版（支持直接读取小说文件）
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

import sys
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


class MangaScriptWriter:
    """漫画剧本生成器（支持直接读取小说文件）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "manga_script_writer"
        self.version = "2.0.0"
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # 小说目录（与 novel_writer 保持一致）
        self.novel_dir = Path("skills/content/novel_writer/output/novels")
        self.novel_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MangaScriptWriter v{self.version} 初始化完成")
        logger.info(f"  小说目录: {self.novel_dir}")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """生成剧本"""
        genre = kwargs.get('genre', '冒险')
        theme = kwargs.get('theme', '友情与成长')
        pages = int(kwargs.get('pages', 4))
        characters = kwargs.get('characters', '主角, 朋友')
        setting = kwargs.get('setting', '奇幻世界')
        plot = kwargs.get('plot', '')
        chapter_count = int(kwargs.get('chapter_count', 1))
        
        # ========== ✅ 新增：直接指定小说文件 ==========
        novel_file = kwargs.get('novel_file')
        novel_path = None
        
        if novel_file:
            # 如果指定了文件路径
            novel_path = Path(novel_file)
            if not novel_path.exists():
                logger.warning(f"指定的小说文件不存在: {novel_file}")
                novel_path = None
        
        try:
            # ========== 方法1: 直接读取已有小说文件 ==========
            story_text = None
            if novel_path and novel_path.exists():
                logger.info(f"📖 直接读取小说文件: {novel_path}")
                story_text = self._read_novel_file(novel_path)
            
            # ========== 方法2: 自动查找最新小说 ==========
            if not story_text:
                story_text = self._find_latest_novel()
            
            # ========== 方法3: 调用 novel_writer 生成（仅当没有现有小说时） ==========
            if not story_text:
                logger.info("未找到现有小说，调用 novel_writer 生成...")
                story_text = self._generate_with_novel_writer(genre, theme, characters, setting, plot, chapter_count)
            
            # ========== 如果仍然失败，用模板生成 ==========
            if not story_text or len(story_text) < 50:
                logger.warning("无法获取小说内容，使用模板生成")
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
                "source_file": str(novel_path) if novel_path else "generated",
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
    
    # ============================================================
    # ✅ 新增：直接读取小说文件
    # ============================================================
    
    def _read_novel_file(self, file_path: Path) -> Optional[str]:
        """从小说文件中提取内容"""
        if not file_path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取章节内容（去掉元数据）
            # 匹配 "第X章" 到下一个 "第X章" 或文件结尾
            chapters = re.findall(
                r'(?:第\d+章[：:]\s*.+?\n-{40,}\n)(.*?)(?=\n第\d+章|$)',
                content,
                re.DOTALL
            )
            
            if chapters:
                # 拼接所有章节内容
                full_text = "\n\n".join([ch.strip() for ch in chapters if ch.strip()])
                if len(full_text) > 50:
                    logger.info(f"✅ 从文件提取了 {len(chapters)} 章，共 {len(full_text)} 字")
                    return full_text
            
            # 如果没有章节标记，返回全部内容
            # 移除元数据头部（===== 到 ===== 之间的内容）
            content = re.sub(r'^=+.*?=+\s*\n', '', content, flags=re.DOTALL)
            # 移除小说简介部分
            content = re.sub(r'【.*?】.*?\n', '', content, flags=re.DOTALL)
            
            if len(content) > 50:
                logger.info(f"✅ 从文件读取内容，长度: {len(content)}")
                return content
            
            return None
            
        except Exception as e:
            logger.error(f"读取小说文件失败: {e}")
            return None
    
    def _find_latest_novel(self) -> Optional[str]:
        """自动查找最新的小说文件"""
        if not self.novel_dir.exists():
            return None
        
        # 查找所有小说文件（按修改时间排序）
        novel_files = sorted(
            self.novel_dir.glob("*.txt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # 只处理中文小说（按需调整）
        novel_files = [f for f in novel_files if f.stem.startswith('zh_')]
        
        if not novel_files:
            # 如果没有 zh_ 开头的，取最新的
            novel_files = sorted(
                self.novel_dir.glob("*.txt"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
        
        if novel_files:
            latest = novel_files[0]
            logger.info(f"📖 找到最新小说: {latest.name}")
            return self._read_novel_file(latest)
        
        return None
    
    # ============================================================
    # 原有方法（保留作为备选）
    # ============================================================
    
    def _generate_with_novel_writer(self, genre, theme, characters, setting, plot, chapter_count):
        """使用 novel_writer 生成故事"""
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
                
                # ========== ✅ 修复：从 chapters 提取内容 ==========
                # novel_writer 返回的数据结构：
                # {
                #   "title": "...",
                #   "genre": "...",
                #   "summary": "...",
                #   "chapters": [{"index": 1, "title": "...", "content": "..."}, ...],
                #   "saved_to": "..."
                # }
                
                # 方法1: 从 chapters 提取
                chapters = result_data.get('chapters', [])
                if chapters:
                    full_text = "\n\n".join([ch.get('content', '') for ch in chapters])
                    if full_text and len(full_text) > 50:
                        logger.info(f"✅ 从 chapters 提取内容，长度: {len(full_text)}")
                        return full_text
                
                # 方法2: 如果有 saved_to，读取文件
                saved_to = result_data.get('saved_to')
                if saved_to and Path(saved_to).exists():
                    with open(saved_to, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) > 50:
                            logger.info(f"✅ 从文件读取内容: {saved_to}，长度: {len(content)}")
                            return content
                
                # 方法3: 尝试其他字段
                for field in ['content', 'story', 'text', 'full_text', 'summary']:
                    if result_data.get(field):
                        content = result_data[field]
                        if len(content) > 50:
                            logger.info(f"✅ 从字段 '{field}' 获取内容，长度: {len(content)}")
                            return content
                
                # 如果 result_data 本身是字符串
                if isinstance(result_data, str) and len(result_data) > 50:
                    return result_data
                
                logger.warning(f"novel_writer 返回数据中未找到内容: {result_data.keys() if isinstance(result_data, dict) else type(result_data)}")
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