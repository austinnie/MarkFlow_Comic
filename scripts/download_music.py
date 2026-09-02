#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
音乐批量下载脚本 - 多语种精选歌单（200+ 首）

用法：
  python scripts/download_all_music.py            # 下载所有歌曲
  python scripts/download_all_music.py --list     # 显示歌单列表
  python scripts/download_all_music.py --start 1  # 从第 1 首开始下载
  python scripts/download_all_music.py --count 5  # 只下载前 5 首
  python scripts/download_all_music.py --category K-POP  # 只下载 K-POP
"""

import sys
import argparse
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


class MusicDownloader:
    """音乐批量下载器"""

    PLAYLIST = [
        # ==================== 中文经典 ====================
        {"artist": "周杰伦", "title": "七里香", "query": "周杰伦 七里香", "category": "中文"},
        {"artist": "周杰伦", "title": "晴天", "query": "周杰伦 晴天", "category": "中文"},
        {"artist": "周杰伦", "title": "告白气球", "query": "周杰伦 告白气球", "category": "中文"},
        {"artist": "周杰伦", "title": "稻香", "query": "周杰伦 稻香", "category": "中文"},
        {"artist": "周杰伦", "title": "青花瓷", "query": "周杰伦 青花瓷", "category": "中文"},
        {"artist": "周杰伦", "title": "夜曲", "query": "周杰伦 夜曲", "category": "中文"},
        {"artist": "周杰伦", "title": "简单爱", "query": "周杰伦 简单爱", "category": "中文"},
        {"artist": "周杰伦", "title": "半岛铁盒", "query": "周杰伦 半岛铁盒", "category": "中文"},
        {"artist": "林俊杰", "title": "江南", "query": "林俊杰 江南", "category": "中文"},
        {"artist": "林俊杰", "title": "不为谁而作的歌", "query": "林俊杰 不为谁而作的歌", "category": "中文"},
        {"artist": "林俊杰", "title": "修炼爱情", "query": "林俊杰 修炼爱情", "category": "中文"},
        {"artist": "林俊杰", "title": "她说", "query": "林俊杰 她说", "category": "中文"},
        {"artist": "林俊杰", "title": "可惜没如果", "query": "林俊杰 可惜没如果", "category": "中文"},
        {"artist": "邓紫棋", "title": "光年之外", "query": "邓紫棋 光年之外", "category": "中文"},
        {"artist": "邓紫棋", "title": "泡沫", "query": "邓紫棋 泡沫", "category": "中文"},
        {"artist": "邓紫棋", "title": "倒数", "query": "邓紫棋 倒数", "category": "中文"},
        {"artist": "陈奕迅", "title": "十年", "query": "陈奕迅 十年", "category": "中文"},
        {"artist": "陈奕迅", "title": "富士山下", "query": "陈奕迅 富士山下", "category": "中文"},
        {"artist": "陈奕迅", "title": "浮夸", "query": "陈奕迅 浮夸", "category": "中文"},
        {"artist": "周深", "title": "大鱼", "query": "周深 大鱼", "category": "中文"},
        {"artist": "李荣浩", "title": "年少有为", "query": "李荣浩 年少有为", "category": "中文"},
        {"artist": "田馥甄", "title": "小幸运", "query": "田馥甄 小幸运", "category": "中文"},
        {"artist": "张韶涵", "title": "隐形的翅膀", "query": "张韶涵 隐形的翅膀", "category": "中文"},
        {"artist": "张惠妹", "title": "听海", "query": "张惠妹 听海", "category": "中文"},

        # ==================== K-POP ====================
        {"artist": "IU", "title": "夜信", "query": "IU 夜信", "category": "K-POP"},
        {"artist": "IU", "title": "好日子", "query": "IU 好日子", "category": "K-POP"},
        {"artist": "IU", "title": "Blueming", "query": "IU Blueming", "category": "K-POP"},
        {"artist": "IU", "title": "Palette", "query": "IU Palette", "category": "K-POP"},
        {"artist": "IU", "title": "Twenty-three", "query": "IU Twenty-three", "category": "K-POP"},
        {"artist": "太妍", "title": "Fine", "query": "Taeyeon Fine", "category": "K-POP"},
        {"artist": "太妍", "title": "四季", "query": "Taeyeon Four Seasons", "category": "K-POP"},
        {"artist": "太妍", "title": "INVU", "query": "Taeyeon INVU", "category": "K-POP"},
        {"artist": "太妍", "title": "I", "query": "Taeyeon I", "category": "K-POP"},
        {"artist": "BLACKPINK", "title": "How You Like That", "query": "BLACKPINK How You Like That", "category": "K-POP"},
        {"artist": "BLACKPINK", "title": "Playing with Fire", "query": "BLACKPINK Playing with Fire", "category": "K-POP"},
        {"artist": "BLACKPINK", "title": "As If It's Your Last", "query": "BLACKPINK As If Its Your Last", "category": "K-POP"},
        {"artist": "BLACKPINK", "title": "Lovesick Girls", "query": "BLACKPINK Lovesick Girls", "category": "K-POP"},
        {"artist": "BTS", "title": "Dynamite", "query": "BTS Dynamite", "category": "K-POP"},
        {"artist": "BTS", "title": "Butter", "query": "BTS Butter", "category": "K-POP"},
        {"artist": "BTS", "title": "Spring Day", "query": "BTS Spring Day", "category": "K-POP"},
        {"artist": "乐童音乐家", "title": "200%", "query": "AKMU 200", "category": "K-POP"},
        {"artist": "乐童音乐家", "title": "Give Love", "query": "AKMU Give Love", "category": "K-POP"},
        {"artist": "脸红思春期", "title": "给你宇宙", "query": "Bolbbalgan4 Galaxy", "category": "K-POP"},
        {"artist": "脸红思春期", "title": "Some", "query": "Bolbbalgan4 Some", "category": "K-POP"},
        {"artist": "10CM", "title": "春天喜欢的话", "query": "10cm 春天喜欢的话", "category": "K-POP"},
        {"artist": "G-Dragon", "title": "无题", "query": "G-Dragon Untitled", "category": "K-POP"},
        {"artist": "G-Dragon", "title": "Crooked", "query": "G-Dragon Crooked", "category": "K-POP"},
        {"artist": "Zico", "title": "Any Song", "query": "Zico Any Song", "category": "K-POP"},
        {"artist": "BIBI", "title": "栗子羊羹", "query": "BIBI Chestnut", "category": "K-POP"},
        {"artist": "BIBI", "title": "The Weekend", "query": "BIBI The Weekend", "category": "K-POP"},
        {"artist": "朴春", "title": "春", "query": "Park Bom Spring", "category": "K-POP"},

        # ==================== J-POP / 动漫 ====================
        {"artist": "宇多田光", "title": "First Love", "query": "宇多田光 First Love", "category": "J-POP"},
        {"artist": "宇多田光", "title": "Automatic", "query": "宇多田光 Automatic", "category": "J-POP"},
        {"artist": "宇多田光", "title": "樱流", "query": "宇多田光 樱流", "category": "J-POP"},
        {"artist": "宇多田光", "title": "Flavor Of Life", "query": "宇多田光 Flavor Of Life", "category": "J-POP"},
        {"artist": "米津玄师", "title": "Lemon", "query": "米津玄師 Lemon", "category": "J-POP"},
        {"artist": "米津玄师", "title": "感电", "query": "米津玄师 感电", "category": "J-POP"},
        {"artist": "米津玄师", "title": "灰色与青", "query": "米津玄师 灰色与青", "category": "J-POP"},
        {"artist": "米津玄师", "title": "马与鹿", "query": "米津玄师 马与鹿", "category": "J-POP"},
        {"artist": "米津玄师", "title": "Pale Blue", "query": "米津玄师 Pale Blue", "category": "J-POP"},
        {"artist": "RADWIMPS", "title": "前前前世", "query": "RADWIMPS 前前前世", "category": "J-POP"},
        {"artist": "RADWIMPS", "title": "梦灯笼", "query": "RADWIMPS 梦灯笼", "category": "J-POP"},
        {"artist": "RADWIMPS", "title": "爱にできることはまだあるかい", "query": "RADWIMPS 爱にできる", "category": "J-POP"},
        {"artist": "藤井风", "title": "死ぬのがいいわ", "query": "藤井风 死ぬのがいいわ", "category": "J-POP"},
        {"artist": "藤井风", "title": "まつり", "query": "藤井风 まつり", "category": "J-POP"},
        {"artist": "藤井风", "title": "青春病", "query": "藤井风 青春病", "category": "J-POP"},
        {"artist": "Official髭男dism", "title": "Pretender", "query": "Official髭男dism Pretender", "category": "J-POP"},
        {"artist": "Official髭男dism", "title": "I LOVE...", "query": "Official髭男dism I LOVE", "category": "J-POP"},
        {"artist": "Official髭男dism", "title": "Subtitle", "query": "Official髭男dism Subtitle", "category": "J-POP"},
        {"artist": "爱缪", "title": "金盏花", "query": "Aimyon 金盏花", "category": "J-POP"},
        {"artist": "爱缪", "title": "爱を伝えたい", "query": "Aimyon 爱を伝えたい", "category": "J-POP"},
        {"artist": "YOASOBI", "title": "夜に駆ける", "query": "YOASOBI 夜に駆ける", "category": "J-POP"},
        {"artist": "YOASOBI", "title": "群青", "query": "YOASOBI 群青", "category": "J-POP"},
        {"artist": "YOASOBI", "title": "怪物", "query": "YOASOBI 怪物", "category": "J-POP"},
        {"artist": "中岛美嘉", "title": "雪之华", "query": "中岛美嘉 雪之华", "category": "J-POP"},
        {"artist": "中岛美嘉", "title": "曾经我也想过一了百了", "query": "中岛美嘉 曾经我也想过一了百了", "category": "J-POP"},
        {"artist": "松隆子", "title": "梦的点滴", "query": "松隆子 梦的点滴", "category": "J-POP"},
        {"artist": "花泽香菜", "title": "恋爱循环", "query": "花泽香菜 恋爱循环", "category": "J-POP"},
        {"artist": "LiSA", "title": "红莲华", "query": "LiSA 红莲华", "category": "J-POP"},
        {"artist": "LiSA", "title": "炎", "query": "LiSA 炎", "category": "J-POP"},
        {"artist": "LiSA", "title": "一番の宝物", "query": "LiSA 一番の宝物", "category": "J-POP"},

        # ==================== 欧美流行 ====================
        {"artist": "Taylor Swift", "title": "Love Story", "query": "Taylor Swift Love Story", "category": "欧美"},
        {"artist": "Taylor Swift", "title": "Blank Space", "query": "Taylor Swift Blank Space", "category": "欧美"},
        {"artist": "Taylor Swift", "title": "Shake It Off", "query": "Taylor Swift Shake It Off", "category": "欧美"},
        {"artist": "Taylor Swift", "title": "Anti-Hero", "query": "Taylor Swift Anti-Hero", "category": "欧美"},
        {"artist": "Taylor Swift", "title": "Cruel Summer", "query": "Taylor Swift Cruel Summer", "category": "欧美"},
        {"artist": "Taylor Swift", "title": "Cardigan", "query": "Taylor Swift Cardigan", "category": "欧美"},
        {"artist": "Ariana Grande", "title": "Thank U, Next", "query": "Ariana Grande Thank U Next", "category": "欧美"},
        {"artist": "Ariana Grande", "title": "7 Rings", "query": "Ariana Grande 7 Rings", "category": "欧美"},
        {"artist": "Ariana Grande", "title": "No Tears Left to Cry", "query": "Ariana Grande No Tears", "category": "欧美"},
        {"artist": "Lady Gaga", "title": "Shallow", "query": "Lady Gaga Shallow", "category": "欧美"},
        {"artist": "Lady Gaga", "title": "Bad Romance", "query": "Lady Gaga Bad Romance", "category": "欧美"},
        {"artist": "Beyoncé", "title": "Halo", "query": "Beyonce Halo", "category": "欧美"},
        {"artist": "Beyoncé", "title": "Crazy In Love", "query": "Beyonce Crazy In Love", "category": "欧美"},
        {"artist": "Rihanna", "title": "Diamonds", "query": "Rihanna Diamonds", "category": "欧美"},
        {"artist": "Rihanna", "title": "Stay", "query": "Rihanna Stay", "category": "欧美"},
        {"artist": "Bruno Mars", "title": "Just the Way You Are", "query": "Bruno Mars Just the Way You Are", "category": "欧美"},
        {"artist": "Bruno Mars", "title": "Talking to the Moon", "query": "Bruno Mars Talking to the Moon", "category": "欧美"},
        {"artist": "Bruno Mars", "title": "Versace on the Floor", "query": "Bruno Mars Versace", "category": "欧美"},
        {"artist": "Post Malone", "title": "Circles", "query": "Post Malone Circles", "category": "欧美"},
        {"artist": "Post Malone", "title": "Sunflower", "query": "Post Malone Sunflower", "category": "欧美"},
        {"artist": "Lewis Capaldi", "title": "Someone You Loved", "query": "Lewis Capaldi Someone You Loved", "category": "欧美"},
        {"artist": "Billie Eilish", "title": "Bad Guy", "query": "Billie Eilish Bad Guy", "category": "欧美"},
        {"artist": "Billie Eilish", "title": "Everything I Wanted", "query": "Billie Eilish Everything I Wanted", "category": "欧美"},
        {"artist": "Lauv", "title": "I Like Me Better", "query": "Lauv I Like Me Better", "category": "欧美"},
        {"artist": "Shawn Mendes", "title": "Señorita", "query": "Shawn Mendes Senorita", "category": "欧美"},
        {"artist": "Shawn Mendes", "title": "Stitches", "query": "Shawn Mendes Stitches", "category": "欧美"},
        {"artist": "Dua Lipa", "title": "Don't Start Now", "query": "Dua Lipa Don't Start Now", "category": "欧美"},
        {"artist": "Dua Lipa", "title": "Levitating", "query": "Dua Lipa Levitating", "category": "欧美"},
        {"artist": "The Weeknd", "title": "Blinding Lights", "query": "The Weeknd Blinding Lights", "category": "欧美"},
        {"artist": "The Weeknd", "title": "Starboy", "query": "The Weeknd Starboy", "category": "欧美"},
        {"artist": "Harry Styles", "title": "As It Was", "query": "Harry Styles As It Was", "category": "欧美"},
        {"artist": "Harry Styles", "title": "Watermelon Sugar", "query": "Harry Styles Watermelon Sugar", "category": "欧美"},
        {"artist": "Olivia Rodrigo", "title": "Drivers License", "query": "Olivia Rodrigo Drivers License", "category": "欧美"},
        {"artist": "Olivia Rodrigo", "title": "Good 4 U", "query": "Olivia Rodrigo Good 4 U", "category": "欧美"},
        {"artist": "Imagine Dragons", "title": "Believer", "query": "Imagine Dragons Believer", "category": "欧美"},
        {"artist": "Imagine Dragons", "title": "Radioactive", "query": "Imagine Dragons Radioactive", "category": "欧美"},
        {"artist": "Imagine Dragons", "title": "Demons", "query": "Imagine Dragons Demons", "category": "欧美"},
        {"artist": "Coldplay", "title": "Viva La Vida", "query": "Coldplay Viva La Vida", "category": "欧美"},
        {"artist": "Coldplay", "title": "Yellow", "query": "Coldplay Yellow", "category": "欧美"},
        {"artist": "Coldplay", "title": "Fix You", "query": "Coldplay Fix You", "category": "欧美"},
        {"artist": "Coldplay", "title": "The Scientist", "query": "Coldplay The Scientist", "category": "欧美"},
        {"artist": "Ed Sheeran", "title": "Perfect", "query": "Ed Sheeran Perfect", "category": "欧美"},
        {"artist": "Ed Sheeran", "title": "Shape of You", "query": "Ed Sheeran Shape of You", "category": "欧美"},
        {"artist": "Ed Sheeran", "title": "Photograph", "query": "Ed Sheeran Photograph", "category": "欧美"},
        {"artist": "Adele", "title": "Someone Like You", "query": "Adele Someone Like You", "category": "欧美"},
        {"artist": "Adele", "title": "Hello", "query": "Adele Hello", "category": "欧美"},
        {"artist": "Adele", "title": "Rolling in the Deep", "query": "Adele Rolling in the Deep", "category": "欧美"},

        # ==================== 经典摇滚 ====================
        {"artist": "Queen", "title": "Bohemian Rhapsody", "query": "Queen Bohemian Rhapsody", "category": "摇滚"},
        {"artist": "Queen", "title": "We Will Rock You", "query": "Queen We Will Rock You", "category": "摇滚"},
        {"artist": "Queen", "title": "We Are The Champions", "query": "Queen We Are The Champions", "category": "摇滚"},
        {"artist": "The Beatles", "title": "Hey Jude", "query": "The Beatles Hey Jude", "category": "摇滚"},
        {"artist": "The Beatles", "title": "Let It Be", "query": "The Beatles Let It Be", "category": "摇滚"},
        {"artist": "The Beatles", "title": "Yesterday", "query": "The Beatles Yesterday", "category": "摇滚"},
        {"artist": "Guns N' Roses", "title": "Sweet Child O' Mine", "query": "Guns N Roses Sweet Child", "category": "摇滚"},
        {"artist": "Bon Jovi", "title": "Livin' On A Prayer", "query": "Bon Jovi Livin On A Prayer", "category": "摇滚"},
        {"artist": "Bon Jovi", "title": "It's My Life", "query": "Bon Jovi Its My Life", "category": "摇滚"},
        {"artist": "Green Day", "title": "Wake Me Up When September Ends", "query": "Green Day Wake Me Up", "category": "摇滚"},
        {"artist": "Green Day", "title": "21 Guns", "query": "Green Day 21 Guns", "category": "摇滚"},
        {"artist": "Radiohead", "title": "Creep", "query": "Radiohead Creep", "category": "摇滚"},
        {"artist": "Oasis", "title": "Wonderwall", "query": "Oasis Wonderwall", "category": "摇滚"},
        {"artist": "Oasis", "title": "Don't Look Back in Anger", "query": "Oasis Dont Look Back in Anger", "category": "摇滚"},
        {"artist": "Nirvana", "title": "Smells Like Teen Spirit", "query": "Nirvana Smells Like Teen Spirit", "category": "摇滚"},
        {"artist": "Linkin Park", "title": "In the End", "query": "Linkin Park In the End", "category": "摇滚"},
        {"artist": "Linkin Park", "title": "Numb", "query": "Linkin Park Numb", "category": "摇滚"},

        # ==================== 轻音乐 / 治愈系 ====================
        {"artist": "久石让", "title": "Summer", "query": "久石让 Summer", "category": "轻音乐"},
        {"artist": "久石让", "title": "天空之城", "query": "久石让 天空之城", "category": "轻音乐"},
        {"artist": "久石让", "title": "龙猫", "query": "久石让 龙猫", "category": "轻音乐"},
        {"artist": "久石让", "title": "千与千寻", "query": "久石让 千与千寻", "category": "轻音乐"},
        {"artist": "久石让", "title": "幽灵公主", "query": "久石让 幽灵公主", "category": "轻音乐"},
        {"artist": "坂本龙一", "title": "Merry Christmas Mr. Lawrence", "query": "坂本龙一 Merry Christmas", "category": "轻音乐"},
        {"artist": "坂本龙一", "title": "Energy Flow", "query": "坂本龙一 Energy Flow", "category": "轻音乐"},
        {"artist": "坂本龙一", "title": "Aqua", "query": "坂本龙一 Aqua", "category": "轻音乐"},
        {"artist": "押尾光太郎", "title": "风之诗", "query": "押尾光太郎 风之诗", "category": "轻音乐"},
        {"artist": "押尾光太郎", "title": "黄昏", "query": "押尾光太郎 黄昏", "category": "轻音乐"},
        {"artist": "岸部真明", "title": "奇迹的山", "query": "岸部真明 奇迹的山", "category": "轻音乐"},
        {"artist": "岸部真明", "title": "流行的云", "query": "岸部真明 流行的云", "category": "轻音乐"},
        {"artist": "Yiruma", "title": "River Flows in You", "query": "Yiruma River Flows in You", "category": "轻音乐"},
        {"artist": "Yiruma", "title": "Kiss the Rain", "query": "Yiruma Kiss the Rain", "category": "轻音乐"},
        {"artist": "Yiruma", "title": "May Be", "query": "Yiruma May Be", "category": "轻音乐"},
        {"artist": "George Winston", "title": "Colors", "query": "George Winston Colors", "category": "轻音乐"},
        {"artist": "George Winston", "title": "Variations", "query": "George Winston Variations", "category": "轻音乐"},
    ]

    def __init__(self):
        self.total = len(self.PLAYLIST)
        self.success = 0
        self.failed = 0
        self.failed_list = []

    def _clean_title(self, title: str) -> str:
        """清理标题，只保留汉字、字母和数字"""
        import re
        # 去掉括号内的内容
        title = re.sub(r'[（(][^)）]*[)）]', '', title)
        # 去掉特殊字符，只保留汉字、字母、数字
        title = re.sub(r'[^\w\u4e00-\u9fff]', '', title)
        return title

    def _check_exists(self, title: str) -> bool:
        """检查歌曲是否已下载"""
        output_dir = Path("skills/music_player/output")
        if not output_dir.exists():
            return False
        
        title_clean = self._clean_title(title)
        for file_path in output_dir.glob("*.mp3"):
            file_title = self._clean_title(file_path.stem)
            # 模糊匹配：标题包含或文件名包含
            if title_clean and (title_clean in file_title or file_title in title_clean):
                return True
            # 也检查原始标题的包含关系
            if title.lower() in file_path.stem.lower() or file_path.stem.lower() in title.lower():
                return True
        return False

    def download_one(self, index: int, song: dict) -> bool:
        """下载一首歌"""
        query = song["query"]
        title = song["title"]
        artist = song["artist"]
        category = song["category"]

        print(f"\n[{index + 1}/{self.total}] [{category}] {artist} - {title}")
        
        # 检查是否已下载
        if self._check_exists(title):
            print(f"   ⏭️ 已存在，跳过")
            return True
        
        print(f"   🔍 搜索: {query}")

        try:
            result = execute_skill("music_player", action="download", query=query)
            if result and result.get("status") == "success":
                print(f"   ✅ 下载成功")
                return True
            else:
                print(f"   ❌ 下载失败")
                return False
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            return False
            
    def download_all(self, start: int = 0, count: int = None, category: str = None):
        """批量下载"""
        # 过滤分类
        songs = self.PLAYLIST
        if category:
            songs = [s for s in self.PLAYLIST if s["category"] == category]
            if not songs:
                print(f"❌ 未找到分类: {category}")
                print(f"📋 可用分类: {', '.join(set(s['category'] for s in self.PLAYLIST))}")
                return

        total = len(songs)
        end = total if count is None else min(start + count, total)

        print("\n" + "=" * 60)
        print("   🎵 音乐批量下载器")
        print("=" * 60)
        if category:
            print(f"📂 分类: {category}")
        print(f"📋 歌单总数: {total} 首")
        print(f"📥 本次下载: {end - start} 首 (从第 {start + 1} 首开始)")
        print("=" * 60)

        for i in range(start, end):
            song = songs[i]
            if self.download_one(i, song):
                self.success += 1
            else:
                self.failed += 1
                self.failed_list.append(f"{song['category']} - {song['artist']} - {song['title']}")

            if (i + 1) % 5 == 0 and i + 1 < end:
                print("   ⏳ 休息 1 秒...")
                time.sleep(1)

        # 显示结果
        print("\n" + "=" * 60)
        print("   📊 下载完成")
        print("=" * 60)
        print(f"✅ 成功: {self.success} 首")
        print(f"❌ 失败: {self.failed} 首")
        if self.failed_list:
            print("\n❌ 失败列表:")
            for item in self.failed_list:
                print(f"   - {item}")

    def list_songs(self, category: str = None):
        """显示歌单列表"""
        songs = self.PLAYLIST
        if category:
            songs = [s for s in self.PLAYLIST if s["category"] == category]

        print("\n" + "=" * 60)
        print(f"   📋 精选歌单{' - ' + category if category else ''}")
        print("=" * 60)
        print(f"{'序号':<6} {'分类':<8} {'艺术家':<20} {'歌曲':<20}")
        print("-" * 60)
        for i, song in enumerate(songs):
            print(f"{i + 1:<6} {song['category']:<8} {song['artist']:<20} {song['title']:<20}")
        print("-" * 60)
        print(f"共 {len(songs)} 首歌曲")

        # 按分类统计
        if not category:
            print("\n📊 分类统计:")
            cats = {}
            for s in self.PLAYLIST:
                cats[s["category"]] = cats.get(s["category"], 0) + 1
            for cat, count in cats.items():
                print(f"   {cat}: {count} 首")


def main():
    parser = argparse.ArgumentParser(
        description="音乐批量下载脚本 - 多语种精选歌单（200+ 首）",
        epilog="示例:\n"
               "  python scripts/download_all_music.py                    # 下载所有歌曲\n"
               "  python scripts/download_all_music.py --list             # 显示歌单列表\n"
               "  python scripts/download_all_music.py --list --category 中文  # 显示中文歌单\n"
               "  python scripts/download_all_music.py --category K-POP   # 只下载 K-POP\n"
               "  python scripts/download_all_music.py --start 10         # 从第 10 首开始下载\n"
               "  python scripts/download_all_music.py --count 5          # 只下载前 5 首"
    )
    parser.add_argument("--list", "-l", action="store_true", help="显示歌单列表")
    parser.add_argument("--category", "-c", type=str, default=None,
                        help="按分类下载 (中文/K-POP/J-POP/欧美/摇滚/轻音乐)")
    parser.add_argument("--start", "-s", type=int, default=0, help="起始索引（从 0 开始）")
    parser.add_argument("--count", "-n", type=int, default=None, help="下载数量")

    args = parser.parse_args()

    downloader = MusicDownloader()

    if args.list:
        downloader.list_songs(args.category)
        return

    downloader.download_all(args.start, args.count, args.category)


if __name__ == "__main__":
    main()