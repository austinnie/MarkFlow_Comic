#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
漫画续写器 - 使用配置文件
自动检测最新章节并续写漫画
"""

import sys
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill
from comic_utils import ComicConfig, ComicLogger, get_image_paths, config as global_config


class ComicContinuer:
    """漫画续写器 - 使用配置文件"""
        
    def __init__(self, config: ComicConfig = None):
        self.config = config or global_config
        self.project_root = project_root
        
        # 目录配置
        self.novel_dir = self.project_root / "skills/content/novel_writer/output/novels"
        self.script_dir = self.project_root / "skills/comics/manga_script_writer/output"
        self.image_dir = self.project_root / "skills/image/sd_image_generator/output/images"
        self.bubble_dir = self.project_root / "skills/comics/manga_bubble_adder/output"
        self.output_dir = self.project_root / "output/comic_continued"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # ✅ 先定义 title
        self.title = self.config.get('project.name', '漫画')
        
        # ✅ 再加载状态
        self.state_file = self.output_dir / "state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """加载续写状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_chapter": 0,
            "processed_novels": [],
            "title": self.title,
            "total_pages": 0
        }
    
    def _save_state(self):
        """保存续写状态"""
        self.state['title'] = self.title
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def _get_latest_novel(self) -> Optional[Path]:
        """获取最新未处理的小说"""
        novels = sorted(self.novel_dir.glob("zh_*.txt"), 
                       key=lambda p: p.stat().st_mtime, reverse=True)
        
        for n in novels:
            if str(n) not in self.state.get('processed_novels', []):
                return n
        return None
    
    def _continue_novel(self, chapters: int = None) -> Optional[Path]:
        """续写小说"""
        ComicLogger.info(f"续写小说", "步骤1")
        
        if chapters is None:
            chapters = self.config.get('novel.chapters', 3)
        
        novel_config = self.config.novel_config
        novel_file = self._get_latest_novel()
        
        result = execute_skill(
            "novel_writer",
            genre=novel_config.get('genre', '科幻'),
            title=novel_config.get('title', self.title),
            outline=novel_config.get('outline', ''),
            characters=novel_config.get('characters', ''),
            chapter_count=chapters,
            continue_from=str(novel_file) if novel_file else "",
            language=novel_config.get('language', 'zh')
        )
        
        if result and result.get('status') == 'success':
            result_data = result.get('result', {})
            saved_to = result_data.get('saved_to')
            if saved_to and Path(saved_to).exists():
                ComicLogger.success(f"小说续写完成: {saved_to}", "步骤1")
                self.state['last_chapter'] += chapters
                return Path(saved_to)
        
        ComicLogger.error("小说续写失败", "步骤1")
        return None
    
    def _continue_comic(self, novel_file: Path, pages: int = None) -> Dict:
        """从小说续写漫画"""
        ComicLogger.info(f"从小说生成漫画续集: {novel_file.name}", "步骤2")
        
        if pages is None:
            pages = self.config.get('manga.pages', 4)
        
        manga_config = self.config.manga_config
        
        # 1. 生成剧本
        result = execute_skill(
            "manga_script_writer",
            novel_file=str(novel_file),
            pages=pages
        )
        
        if not result or result.get('status') != 'success':
            ComicLogger.error("剧本生成失败", "步骤2")
            return {}
        
        script_path = result.get('output_path')
        ComicLogger.success(f"剧本: {script_path}", "步骤2")
        
        # 2. 生成图片
        result = execute_skill(
            "manga_generator",
            script_path=script_path,
            style=manga_config.get('style', 'manga'),
            pages=pages,
            steps=manga_config.get('steps', 30),
            strength=manga_config.get('strength', 0.65)
        )
        
        if not result or result.get('status') != 'success':
            ComicLogger.error("图片生成失败", "步骤2")
            return {}
        
        # 获取最新图片
        images = sorted(self.image_dir.glob("image_*.png"),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:pages]
        
        if not images:
            ComicLogger.error("没有找到生成的图片", "步骤2")
            return {}
        
        ComicLogger.success(f"生成了 {len(images)} 张图片", "步骤2")
        
        # 3. 添加气泡
        bubbled_paths = []
        for i, img_path in enumerate(images):
            dialogues = self.config.get_dialogues(i)
            positions = self.config.get_positions()
            
            result = execute_skill(
                "manga_bubble_adder",
                image_path=str(img_path),
                dialogues=dialogues,
                positions=positions[:len(dialogues)],
                bubble_style=self.config.get('bubbles.bubble_style', 'rounded')
            )
            
            if result and result.get('status') == 'success':
                output = result.get('output_path')
                if output:
                    bubbled_paths.append(output)
        
        ComicLogger.success(f"添加了 {len(bubbled_paths)} 个气泡", "步骤2")
        
        # 4. 导出
        if bubbled_paths:
            export_config = self.config.export_config
            formats = export_config.get('formats', ['pdf'])
            
            # 合并所有图片（原有 + 新生成的）
            all_images = get_image_paths("bubbled_*.png", self.bubble_dir)
            
            results = {}
            if 'pdf' in formats:
                result = execute_skill(
                    "manga_to_pdf",
                    image_paths=all_images,
                    title=f"{self.title} (续)",
                    page_size=export_config.get('page_size', 'A4')
                )
                if result and result.get('status') == 'success':
                    results['pdf'] = result.get('output_path')
                    ComicLogger.success(f"PDF: {results['pdf']}", "步骤2")
            
            if 'epub' in formats:
                result = execute_skill(
                    "manga_to_epub",
                    image_paths=all_images,
                    title=f"{self.title} (续)",
                    author=export_config.get('author', 'AI 生成')
                )
                if result and result.get('status') == 'success':
                    results['epub'] = result.get('output_path')
                    ComicLogger.success(f"EPUB: {results['epub']}", "步骤2")
            
            # 保存续集
            continued_dir = self._save_continued(results, bubbled_paths)
            
            return {
                "script": script_path,
                "images": images,
                "bubbled": bubbled_paths,
                "results": results,
                "output_dir": continued_dir
            }
        
        return {}
    
    def _save_continued(self, results: dict, bubbled_paths: list) -> Path:
        """保存续集"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        continued_dir = self.output_dir / f"续写_{timestamp}"
        continued_dir.mkdir(exist_ok=True)
        
        # 复制 PDF
        if results.get('pdf') and Path(results['pdf']).exists():
            shutil.copy(results['pdf'], continued_dir / "comic.pdf")
        
        # 复制 EPUB
        if results.get('epub') and Path(results['epub']).exists():
            shutil.copy(results['epub'], continued_dir / "comic.epub")
        
        # 复制图片
        img_dir = continued_dir / "images"
        img_dir.mkdir(exist_ok=True)
        for img in bubbled_paths:
            shutil.copy(img, img_dir / Path(img).name)
        
        # 保存状态
        state_path = continued_dir / "state.json"
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "pages": len(bubbled_paths),
                "title": self.title
            }, f, ensure_ascii=False, indent=2)
        
        ComicLogger.success(f"续集已保存: {continued_dir}", "输出")
        return continued_dir
    
    def run(self, chapters: int = None, pages: int = None):
        """运行续写流程"""
        if chapters is None:
            chapters = self.config.get('novel.chapters', 3)
        if pages is None:
            pages = self.config.get('manga.pages', 4)
        
        print("\n" + "=" * 60)
        print("   🔄 漫画续写器")
        print("=" * 60)
        print(f"📖 标题: {self.title}")
        print(f"📄 续写章节: {chapters}")
        print(f"🎨 生成页数: {pages}")
        print(f"📊 已处理: {len(self.state.get('processed_novels', []))} 部小说")
        print("=" * 60)
        
        # 1. 续写小说
        novel_file = self._continue_novel(chapters)
        if not novel_file:
            ComicLogger.error("续写失败，退出")
            return
        
        # 2. 生成漫画续集
        result = self._continue_comic(novel_file, pages)
        
        if result:
            self.state['processed_novels'].append(str(novel_file))
            self.state['total_pages'] += pages
            self._save_state()
        
        print("\n" + "=" * 60)
        print("   ✅ 续写完成!")
        print("=" * 60)
        if result.get('output_dir'):
            print(f"📂 输出: {result['output_dir']}")
        print("=" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="漫画续写器")
    parser.add_argument("--config", help="配置文件路径（可选）")  # 去掉 -c
    parser.add_argument("--chapters", "-n", type=int, help="续写章节数")  # 改为 -n
    parser.add_argument("--pages", "-p", type=int, help="生成页数")
    parser.add_argument("--status", "-s", action="store_true", help="显示当前状态")
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config:
        config = ComicConfig(Path(args.config))
    else:
        config = global_config
    
    continuer = ComicContinuer(config)
    
    if args.status:
        state = continuer.state
        print("\n📊 续写状态:")
        print(f"  标题: {state.get('title', '未知')}")
        print(f"  上次章节: {state.get('last_chapter', 0)}")
        print(f"  已处理小说: {len(state.get('processed_novels', []))}")
        print(f"  总页数: {state.get('total_pages', 0)}")
        return
    
    continuer.run(args.chapters, args.pages)


if __name__ == "__main__":
    main()