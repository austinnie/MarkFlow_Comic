#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说生成器 - 每日续写指定章节 + 有声书（多语言）
用法：python novel_generator.py [章节数] --lang [语言代码]
示例：python novel_generator.py 6 --lang ja    # 生成6章日语小说
      python novel_generator.py 3 --lang en    # 生成3章英语小说
      python novel_generator.py                # 默认中文+3章
"""

import sys
import argparse
import re
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill
# ✅ 从共享配置导入所有配置
from novel_config import DEFAULT_CHAPTERS, DEFAULT_MODEL, LANG_CONFIG

class NovelGenerator:
    def __init__(self, lang: str = "zh"):
        self.base_dir = Path(__file__).parent.parent
        self.lang = lang
        self.config = LANG_CONFIG.get(lang, LANG_CONFIG["zh"])
        
        # 输出路径
        self.novel_dir = self.base_dir / "skills" / "novel_writer" / "output" / "novels"
        self.audio_dir = self.base_dir / "skills" / "voice_assistant" / "output" / "audio"
        self.novel_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def get_today(self):
        return datetime.now().strftime("%Y%m%d")

    def get_today_display(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_chapter_patterns(self) -> list:
        return self.config.get("chapter_patterns", [r'第\d+章'])

    def get_current_chapters(self, novel_file: Path) -> int:
        if not novel_file or not novel_file.exists():
            return 0
        try:
            with open(novel_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"   📄 读取文件: {novel_file}")
            print(f"   📄 内容预览: {content[:500]}")
            
            # ✅ 多语言章节标题匹配（行首）
            patterns = [
                r'^第\d+章[：:]\s*.+$',           # 中文/日语
                r'^Chapter \d+[：:]\s*.+$',        # 英语
                r'^Capítulo \d+[：:]\s*.+$',       # 西班牙语
                r'^Chapitre \d+[：:]\s*.+$',       # 法语
                r'^Kapitel \d+[：:]\s*.+$',        # 德语
                r'^Capitolo \d+[：:]\s*.+$',       # 意大利语
                r'^제\d+장[：:]\s*.+$',             # 韩语
                r'^الفصل \d+[：:]\s*.+$',          # 阿拉伯语
                r'^บทที่ \d+[：:]\s*.+$',          # 泰语
                r'^Hoofdstuk \d+[：:]\s*.+$',      # 荷兰语
                r'^Rozdzia\u0142 \d+[：:]\s*.+$',  # 波兰语
                r'^Luku \d+[：:]\s*.+$',           # 芬兰语
                r'^Κεφάλαιο \d+[：:]\s*.+$',      # 希腊语
                r'^פרק \d+[：:]\s*.+$',            # 希伯来语
                r'^अध्याय \d+[：:]\s*.+$',        # 印地语
            ]
            
            total = 0
            for pattern in patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
                total += len(matches)
            
            print(f"   📊 统计到 {total} 章")
            return total
        except Exception as e:
            print(f"   ❌ 读取失败: {e}")
            return 0
        
    def get_novel_file(self) -> Path:
        """
        获取当前语言的小说文件
        严格按语言隔离，不跨语言查找
        """
        # 1. 只查找该语言的文件（新格式：语言_标题_日期_时间.txt）
        lang_files = list(self.novel_dir.glob(f"{self.lang}_*.txt"))
        if not lang_files:
            return None
        
        # 2. 优先返回今天生成的该语言文件
        today = self.get_today()
        today_files = []
        for f in lang_files:
            if today in f.stem:
                today_files.append(f)
        if today_files:
            return sorted(today_files, key=lambda p: p.stat().st_mtime)[-1]
        
        # 3. 返回该语言的最新文件
        return sorted(lang_files, key=lambda p: p.stat().st_mtime)[-1]

    def continue_novel(self, novel_file: Path, target_chapters: int) -> bool:
        current = self.get_current_chapters(novel_file)
        
        if current >= target_chapters:
            target_chapters = current + DEFAULT_CHAPTERS
            print(f"📝 已有 {current} 章，自动续写到 {target_chapters} 章")
        
        print(f"📝 从 {current} 章续写到 {target_chapters} 章（+{target_chapters - current} 章）")
        
        try:
            result = execute_skill(
                "novel_writer",
                genre=self.config.get("genre"),          # ✅ 无默认值，必须从配置读取
                title=self.config.get("title"),          # ✅ 无默认值，必须从配置读取
                outline=self.config.get("outline", ""),
                characters=self.config.get("characters", ""),
                chapter_count=target_chapters,
                model=DEFAULT_MODEL,
                continue_from=str(novel_file) if novel_file and novel_file.exists() else "",
                language=self.lang
            )
            return result is not None
        except Exception as e:
            print(f"❌ 续写失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def generate_audiobook(self, text_file: Path) -> bool:
        print("[2/2] 正在生成有声书...")
        voice = self.config.get("voice", "zh-CN-XiaoxiaoNeural")
        
        if text_file:
            base_name = text_file.stem
            audio_file = self.audio_dir / f"{base_name}.mp3"
        else:
            today = self.get_today()
            audio_file = self.audio_dir / f"novel_{self.lang}_{today}.mp3"
        
        try:
            result = execute_skill(
                "voice_assistant",
                action="tts",
                text_file=str(text_file) if text_file and text_file.exists() else "",
                voice=voice,
                chunk_size=10000,
                output_file=str(audio_file)
            )
            
            if result is not None:
                print(f"   ✅ 有声书：{audio_file}")
                return True
            else:
                print("   ❌ 有声书生成失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 有声书生成失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self, target_chapters: int = None):
        lang_name = self.config.get("name", self.lang)
        
        print("\n" + "=" * 60)
        print(f"   📖 {lang_name} 小说生成器")
        print("=" * 60)
        print()
        print(f"📅 时间：{self.get_today_display()}")
        print(f"🌐 语言：{lang_name} ({self.lang})")
        print()

        if target_chapters is None:
            target_chapters = DEFAULT_CHAPTERS

        novel_file = self.get_novel_file()
        
        if novel_file is None or not novel_file.exists():
            print(f"📝 首次生成 {lang_name} 语言 {target_chapters} 章...")
            result = execute_skill(
                "novel_writer",
                genre=self.config.get("genre"),
                title=self.config.get("title"),
                outline=self.config.get("outline", ""),
                characters=self.config.get("characters", ""),
                chapter_count=target_chapters,
                model=DEFAULT_MODEL,
                continue_from="",
                language=self.lang
            )
        else:
            current = self.get_current_chapters(novel_file)
            target_total = current + target_chapters
            print(f"📝 从 {current} 章追加 {target_chapters} 章到 {target_total} 章...")
            result = execute_skill(
                "novel_writer",
                genre=self.config.get("genre"),
                title=self.config.get("title"),
                outline=self.config.get("outline", ""),
                characters=self.config.get("characters", ""),
                chapter_count=target_chapters,
                model=DEFAULT_MODEL,
                continue_from=str(novel_file),
                language=self.lang
            )
        
        if result is None:
            print("❌ 生成失败")
            return
        
        novel_file = self.get_novel_file()
        if novel_file is None:
            print("❌ 未找到小说文件")
            return

        # ✅ 生成有声书
        self.generate_audiobook(novel_file)

        print("\n" + "=" * 60)
        print("   ✅ 完成！")
        print("=" * 60)
        print()
        print(f"   📖 小说：{novel_file}")
        print(f"   📊 章节：{self.get_current_chapters(novel_file)} 章")
        print(f"   🎤 有声书：{self.audio_dir}/{novel_file.stem}.mp3")
        print()
    
def main():
    parser = argparse.ArgumentParser(
        description="小说生成器 - 多语言版本"
    )
    parser.add_argument(
        "--chapters", "-c",
        type=int,
        default=3,
        help="目标章节数 (默认: 3)"
    )
    parser.add_argument(
        "--lang", "-l",
        type=str,
        default="zh",
        help="语言代码 (zh/en/ja/es/fr/de/it/pt/ko/ar/th/nl/pl/sv/fi/el/he/hi)"
    )
    args = parser.parse_args()
    generator = NovelGenerator(lang=args.lang)
    generator.run(target_chapters=args.chapters)
    
if __name__ == "__main__":
    main()