#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
漫画流水线 - 增量生成
检测新小说 → 生成漫画 → 导出PDF/EPUB
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


class ComicPipeline:
    """漫画流水线"""
    
    def __init__(self):
        self.novel_dir = project_root / "skills/content/novel_writer/output/novels"
        self.script_dir = project_root / "skills/comics/manga_script_writer/output"
        self.manga_dir = project_root / "skills/comics/manga_generator/output"
        self.output_dir = project_root / "output/comics"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 记录已处理的小说（增量检测）
        self.processed_file = self.output_dir / "processed_novels.json"
        self.processed = self._load_processed()
    
    def _load_processed(self) -> dict:
        if self.processed_file.exists():
            with open(self.processed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_processed(self):
        with open(self.processed_file, 'w', encoding='utf-8') as f:
            json.dump(self.processed, f, ensure_ascii=False, indent=2)
    
    def _get_novel_files(self) -> list:
        """获取所有小说文件"""
        if not self.novel_dir.exists():
            return []
        return sorted(
            [f for f in self.novel_dir.glob("*.txt") if f.stem.startswith('zh_')],
            key=lambda p: p.stat().st_mtime
        )
    
    def _is_processed(self, novel_file: Path) -> bool:
        """检查是否已处理"""
        return str(novel_file) in self.processed
    
    def _mark_processed(self, novel_file: Path, result: dict):
        """标记为已处理"""
        self.processed[str(novel_file)] = {
            "processed_at": datetime.now().isoformat(),
            "script_file": result.get('script_file'),
            "manga_dir": result.get('manga_dir'),
            "pdf_file": result.get('pdf_file')
        }
        self._save_processed()
    
    def run(self, auto_export: bool = True):
        """运行流水线"""
        print("\n" + "=" * 60)
        print("   🎬 漫画流水线 - 增量生成")
        print("=" * 60)
        
        novels = self._get_novel_files()
        if not novels:
            print("❌ 没有找到小说文件")
            return
        
        new_novels = [f for f in novels if not self._is_processed(f)]
        
        if not new_novels:
            print("✅ 所有小说已处理完成")
            return
        
        print(f"📖 发现 {len(new_novels)} 个新小说")
        print("-" * 60)
        
        for novel_file in new_novels:
            print(f"\n📄 处理: {novel_file.name}")
            
            # 步骤1: 生成剧本
            print("  📝 生成剧本...")
            script_result = execute_skill(
                "manga_script_writer",
                novel_file=str(novel_file)
            )
            
            if script_result.get('status') != 'success':
                print(f"  ❌ 剧本生成失败: {script_result.get('error')}")
                continue
            
            script_file = script_result.get('output_path')
            print(f"  ✅ 剧本: {script_file}")
            
            # 步骤2: 生成漫画
            print("  🎨 生成漫画...")
            manga_result = execute_skill(
                "manga_generator",
                script_path=script_file
            )
            
            if manga_result.get('status') != 'success':
                print(f"  ❌ 漫画生成失败: {manga_result.get('error')}")
                continue
            
            manga_dir = manga_result.get('output_dir')
            print(f"  ✅ 漫画: {manga_dir}")
            
            # 步骤3: 导出PDF（可选）
            pdf_file = None
            if auto_export:
                print("  📄 导出PDF...")
                pdf_result = execute_skill(
                    "manga_to_pdf",
                    manga_dir=manga_dir
                )
                if pdf_result.get('status') == 'success':
                    pdf_file = pdf_result.get('pdf_file')
                    print(f"  ✅ PDF: {pdf_file}")
                else:
                    print(f"  ⚠️ PDF导出失败: {pdf_result.get('error')}")
            
            # 标记已处理
            self._mark_processed(novel_file, {
                "script_file": script_file,
                "manga_dir": manga_dir,
                "pdf_file": pdf_file
            })
        
        print("\n" + "=" * 60)
        print(f"✅ 完成! 处理了 {len(new_novels)} 个小说")
        print("=" * 60)


if __name__ == "__main__":
    pipeline = ComicPipeline()
    pipeline.run(auto_export=True)