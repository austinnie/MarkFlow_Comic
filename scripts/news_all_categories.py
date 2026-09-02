#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新闻播报工具 - 生成和播放

用法：
  python scripts/news_all_categories.py                    # 生成所有分类（不播放）
  python scripts/news_all_categories.py --play             # 生成所有分类并播放
  python scripts/news_all_categories.py --play-only        # 只播放已生成的（不生成）
  python scripts/news_all_categories.py --top 50           # 每个分类取 50 条
"""

import sys
import argparse
from pathlib import Path
import subprocess

project_root = Path(__file__).parent.parent

CATEGORIES = ["tech", "business", "world", "china", "usa", "japan", "korea"]
TOP_N = 100


def get_latest_audio(category: str) -> Path:
    """获取指定分类最新的音频文件"""
    audio_dir = project_root / "news_broadcast" / "audio"
    if not audio_dir.exists():
        return None
    
    files = sorted(audio_dir.glob(f"*{category}*.mp3"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not files:
        all_files = sorted(audio_dir.glob("*.mp3"),
                          key=lambda p: p.stat().st_mtime, reverse=True)
        return all_files[0] if all_files else None
    
    return files[0]


def play_audio(audio_path: Path) -> bool:
    """使用 music_player 播放音频"""
    if not audio_path or not audio_path.exists():
        print(f"❌ 音频不存在: {audio_path}")
        return False

    print(f"▶️ 播放: {audio_path.name}")
    result = subprocess.run(
        [sys.executable, "-m", "markflow.cli.commands", "execute", "music_player",
         "action=play", f"path={audio_path}"],
        capture_output=False
    )
    return result.returncode == 0


def generate_category(category: str, top_n: int) -> bool:
    """生成单个分类的新闻播报"""
    script = project_root / "scripts" / "news_voice_broadcast.py"
    result = subprocess.run(
        [sys.executable, str(script), "--category", category, "--top", str(top_n)],
        capture_output=False
    )
    return result.returncode == 0


def play_category(category: str) -> bool:
    """播放指定分类的最新音频"""
    audio = get_latest_audio(category)
    if audio:
        return play_audio(audio)
    else:
        print(f"⚠️ 未找到 {category} 的音频")
        return False


def main():
    parser = argparse.ArgumentParser(description="新闻播报工具")
    parser.add_argument("--play", "-p", action="store_true",
                        help="生成后播放")
    parser.add_argument("--play-only", "-po", action="store_true",
                        help="只播放已生成的，不生成")
    parser.add_argument("--category", "-c", default=None,
                        help="指定分类 (不指定则处理所有)")
    parser.add_argument("--top", "-t", type=int, default=TOP_N,
                        help="每个分类取几条 (默认: 50)")

    args = parser.parse_args()

    categories = [args.category] if args.category else CATEGORIES

    # ========== 模式1: 只播放 ==========
    if args.play_only:
        print("=" * 60)
        print(f"🎵 只播放模式")
        print(f"📋 分类: {', '.join(categories)}")
        print("=" * 60)

        played = 0
        for category in categories:
            if play_category(category):
                played += 1
        print(f"\n✅ 播放完成: {played}/{len(categories)}")
        return

    # ========== 模式2: 生成（带或不带播放） ==========
    print("=" * 60)
    if args.play:
        print(f"📻 生成并播放")
    else:
        print(f"📻 生成模式（不播放）")
    print(f"📋 分类: {', '.join(categories)}")
    print(f"📊 每个分类 {args.top} 条")
    print("=" * 60)

    success = 0
    failed = 0
    audio_files = []

    for i, category in enumerate(categories, 1):
        print(f"\n[{i}/{len(categories)}] 📡 生成 {category}...")
        if generate_category(category, args.top):
            success += 1
            audio = get_latest_audio(category)
            if audio:
                audio_files.append((category, audio))
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"✅ 生成完成: 成功 {success}, 失败 {failed}")
    print(f"📁 报告: news_broadcast/reports/")
    print(f"🎵 音频: news_broadcast/audio/")
    print("=" * 60)

    # ========== 播放 ==========
    if args.play and audio_files:
        print("\n🎵 开始播放...")
        for category, audio in audio_files:
            play_audio(audio)


if __name__ == "__main__":
    main()