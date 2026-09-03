#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
漫画全自动生成器 - 使用配置文件
从零开始生成完整漫画
"""

import sys
import time
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill
from comic_utils import ComicConfig, ComicLogger, get_image_paths, config as global_config


class ComicAutoGenerator:
    """漫画全自动生成器 - 使用配置文件"""
    
    def __init__(self, config: ComicConfig = None):
        self.config = config or global_config
        self.project_root = project_root
        
        # 目录配置
        self.novel_dir = self.project_root / "skills/content/novel_writer/output/novels"
        self.script_dir = self.project_root / "skills/comics/manga_script_writer/output"
        self.image_dir = self.project_root / "skills/image/sd_image_generator/output/images"
        self.bubble_dir = self.project_root / "skills/comics/manga_bubble_adder/output"
        self.pdf_dir = self.project_root / "skills/comics/manga_to_pdf/output"
        self.epub_dir = self.project_root / "skills/comics/manga_to_epub/output"
        self.output_dir = self.project_root / "output/comic"
        
        # 创建目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        for d in [self.bubble_dir, self.pdf_dir, self.epub_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.start_time = None
        self.title = self.config.get('project.name', '漫画')
    
    def step1_generate_novel(self):
        """步骤1: 生成小说"""
        ComicLogger.info("开始生成小说", "步骤1")
        
        novel_config = self.config.novel_config
        
        result = execute_skill(
            "novel_writer",
            genre=novel_config.get('genre', '科幻'),
            title=novel_config.get('title', self.title),
            outline=novel_config.get('outline', ''),
            characters=novel_config.get('characters', ''),
            chapter_count=novel_config.get('chapters', 3),
            language=novel_config.get('language', 'zh')
        )
        
        if result and result.get('status') == 'success':
            result_data = result.get('result', {})
            saved_to = result_data.get('saved_to')
            if saved_to and Path(saved_to).exists():
                ComicLogger.success(f"小说已生成: {saved_to}", "步骤1")
                return saved_to
            
            # 查找最新小说
            novels = sorted(self.novel_dir.glob("zh_*.txt"), 
                           key=lambda p: p.stat().st_mtime, reverse=True)
            if novels:
                ComicLogger.success(f"找到最新小说: {novels[0]}", "步骤1")
                return str(novels[0])
        
        ComicLogger.error("小说生成失败", "步骤1")
        return None
    
    def step2_generate_script(self, novel_file: str):
        """步骤2: 生成剧本"""
        ComicLogger.info(f"从小说生成剧本: {Path(novel_file).name}", "步骤2")
        
        result = execute_skill(
            "manga_script_writer",
            novel_file=novel_file
        )
        
        if result and result.get('status') == 'success':
            script_path = result.get('output_path')
            if script_path and Path(script_path).exists():
                ComicLogger.success(f"剧本已生成: {script_path}", "步骤2")
                return script_path
        
        ComicLogger.error("剧本生成失败", "步骤2")
        return None
    
    def step3_generate_images(self, script_path: str):
        """步骤3: 生成漫画图片"""
        ComicLogger.info(f"从剧本生成漫画图片", "步骤3")
        
        manga_config = self.config.manga_config
        
        result = execute_skill(
            "manga_generator",
            script_path=script_path,
            style=manga_config.get('style', 'manga'),
            pages=manga_config.get('pages', 4),
            steps=manga_config.get('steps', 30),
            strength=manga_config.get('strength', 0.65)
        )
        
        if result and result.get('status') == 'success':
            ComicLogger.info("等待图片生成完成...", "步骤3")
            time.sleep(5)
            
            images = sorted(self.image_dir.glob("image_*.png"), 
                           key=lambda p: p.stat().st_mtime, reverse=True)
            
            # 限制数量
            max_pages = manga_config.get('pages', 4)
            images = images[:max_pages]
            
            if images:
                ComicLogger.success(f"已生成 {len(images)} 张图片", "步骤3")
                return [str(img) for img in images]
        
        ComicLogger.error("图片生成失败", "步骤3")
        return None
    
    def step4_add_bubbles(self, image_paths: list):
        """步骤4: 添加对话气泡"""
        ComicLogger.info(f"为 {len(image_paths)} 张图片添加气泡", "步骤4")
        
        bubble_config = self.config.bubble_config
        bubble_style = bubble_config.get('bubble_style', 'rounded')
        
        bubbled_paths = []
        for i, img_path in enumerate(image_paths):
            dialogues = self.config.get_dialogues(i)
            positions = self.config.get_positions()
            
            result = execute_skill(
                "manga_bubble_adder",
                image_path=img_path,
                dialogues=dialogues,
                positions=positions[:len(dialogues)],
                bubble_style=bubble_style
            )
            
            if result and result.get('status') == 'success':
                output = result.get('output_path')
                if output:
                    bubbled_paths.append(output)
                    ComicLogger.success(f"第{i+1}张气泡添加成功", "步骤4")
            else:
                ComicLogger.warn(f"第{i+1}张气泡添加失败", "步骤4")
        
        return bubbled_paths
    
    def step5_export(self, bubbled_paths: list):
        """步骤5: 导出 PDF 和 EPUB"""
        ComicLogger.info(f"导出漫画", "步骤5")
        
        export_config = self.config.export_config
        formats = export_config.get('formats', ['pdf'])
        results = {}
        
        if 'pdf' in formats and bubbled_paths:
            result = execute_skill(
                "manga_to_pdf",
                image_paths=bubbled_paths,
                title=self.title,
                page_size=export_config.get('page_size', 'A4')
            )
            if result and result.get('status') == 'success':
                results['pdf'] = result.get('output_path')
                ComicLogger.success(f"PDF: {results['pdf']}", "步骤5")
        
        if 'epub' in formats and bubbled_paths:
            result = execute_skill(
                "manga_to_epub",
                image_paths=bubbled_paths,
                title=self.title,
                author=export_config.get('author', 'AI 生成')
            )
            if result and result.get('status') == 'success':
                results['epub'] = result.get('output_path')
                ComicLogger.success(f"EPUB: {results['epub']}", "步骤5")
        
        return results
    
    def _copy_outputs(self, results: dict, bubbled_paths: list):
        """整理输出文件"""
        ComicLogger.info("整理输出文件...", "输出")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comic_output = self.output_dir / f"{self.title}_{timestamp}"
        comic_output.mkdir(exist_ok=True)
        
        # 复制 PDF
        if results.get('pdf') and Path(results['pdf']).exists():
            shutil.copy(results['pdf'], comic_output / f"{self.title}.pdf")
            ComicLogger.info(f"复制 PDF: {comic_output / f'{self.title}.pdf'}", "输出")
        
        # 复制 EPUB
        if results.get('epub') and Path(results['epub']).exists():
            shutil.copy(results['epub'], comic_output / f"{self.title}.epub")
            ComicLogger.info(f"复制 EPUB: {comic_output / f'{self.title}.epub'}", "输出")
        
        # 复制图片
        img_dir = comic_output / "images"
        img_dir.mkdir(exist_ok=True)
        for img in bubbled_paths:
            shutil.copy(img, img_dir / Path(img).name)
        ComicLogger.info(f"复制 {len(bubbled_paths)} 张图片", "输出")
        
        ComicLogger.success(f"所有文件已保存到: {comic_output}", "输出")
        return comic_output
    
    def run(self):
        """运行完整流水线"""
        self.start_time = time.time()
        
        title = self.config.get('project.name', '漫画')
        genre = self.config.get('novel.genre', '科幻')
        pages = self.config.get('manga.pages', 4)
        
        print("\n" + "=" * 60)
        print("   🎬 漫画全自动生成流水线")
        print("=" * 60)
        print(f"📖 标题: {title}")
        print(f"📂 类型: {genre}")
        print(f"📄 页数: {pages}")
        print("=" * 60 + "\n")
        
        # 执行流程
        novel_file = self.step1_generate_novel()
        if not novel_file:
            print("❌ 流程终止: 小说生成失败")
            return
        
        script_path = self.step2_generate_script(novel_file)
        if not script_path:
            print("❌ 流程终止: 剧本生成失败")
            return
        
        image_paths = self.step3_generate_images(script_path)
        if not image_paths:
            print("❌ 流程终止: 图片生成失败")
            return
        
        bubbled_paths = self.step4_add_bubbles(image_paths)
        if not bubbled_paths:
            print("❌ 流程终止: 气泡添加失败")
            return
        
        results = self.step5_export(bubbled_paths)
        output_dir = self._copy_outputs(results, bubbled_paths)
        
        # 总结
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 60)
        print("   ✅ 漫画生成完成!")
        print("=" * 60)
        print(f"⏱️  总耗时: {elapsed / 60:.1f} 分钟")
        print(f"📖 标题: {self.title}")
        print(f"📄 页数: {len(image_paths)}")
        if results.get('pdf'):
            print(f"📄 PDF: {results['pdf']}")
        if results.get('epub'):
            print(f"📖 EPUB: {results['epub']}")
        print(f"📂 输出目录: {output_dir}")
        print("=" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="漫画全自动生成器")
    parser.add_argument("--config", "-c", help="配置文件路径（可选）")
    parser.add_argument("--title", "-t", help="漫画标题（覆盖配置）")
    parser.add_argument("--genre", "-g", help="题材（覆盖配置）")
    parser.add_argument("--pages", "-p", type=int, help="页数（覆盖配置）")
    
    args = parser.parse_args()
    
    # 加载配置
    if args.config:
        config = ComicConfig(Path(args.config))
    else:
        config = global_config
    
    # 命令行参数覆盖配置
    if args.title:
        config.set('project.name', args.title)
    if args.genre:
        config.set('novel.genre', args.genre)
    if args.pages:
        config.set('manga.pages', args.pages)
    
    generator = ComicAutoGenerator(config)
    generator.run()


if __name__ == "__main__":
    main()