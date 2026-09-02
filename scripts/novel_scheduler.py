#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
小说生成器 - 定时自动执行版（多语言）
用法：python novel_scheduler.py
      python novel_scheduler.py --lang ja
      python novel_scheduler.py --lang en --now
      python novel_scheduler.py --lang ja --time "20:00"
"""

import time
import schedule
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# ✅ 从共享配置导入
from novel_config import DEFAULT_CHAPTERS, LANG_NAMES


class NovelScheduler:
    def __init__(self, lang: str = "zh", chapters: int = None):
        self.base_dir = Path(__file__).parent.parent
        self.lang = lang
        self.chapters = chapters if chapters is not None else DEFAULT_CHAPTERS
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)

    def log(self, message):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}\n"
        print(log_line.strip())

        log_file = self.log_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def run_daily(self):
        """每日执行任务"""
        lang_name = LANG_NAMES.get(self.lang, self.lang)
        self.log("=" * 50)
        self.log(f"📖 开始执行每日小说生成任务 (语言: {lang_name})")

        try:
            cmd = [
                "python",
                str(self.base_dir / "scripts" / "novel_generator.py"),
                str(self.chapters),
                "--lang",
                self.lang
            ]
            self.log(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=self.base_dir
            )

            if result.returncode == 0:
                self.log("✅ 任务执行成功")
            else:
                self.log(f"❌ 任务执行失败，返回码: {result.returncode}")
        except Exception as e:
            self.log(f"❌ 异常: {e}")

        self.log("=" * 50)

    def run_now(self):
        """立即执行一次"""
        self.log("🚀 手动触发执行")
        self.run_daily()

    def start_schedule(self, time_str="23:00"):
        """启动定时任务"""
        schedule.every().day.at(time_str).do(self.run_daily)

        lang_name = LANG_NAMES.get(self.lang, self.lang)
        self.log(f"⏰ 定时任务已启动，每天 {time_str} 执行 (语言: {lang_name})")
        self.log("💡 按 Ctrl+C 停止")

        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(
        description="小说生成器 - 定时执行（多语言）"
    )
    parser.add_argument(
        "--lang", "-l",
        type=str,
        default="zh",
        help="语言代码 (zh/en/ja/es/fr/de/it/pt/ko/ar/th/nl/pl/sv/fi/el/he/hi)"
    )
    parser.add_argument(
        "--chapters", "-c",
        type=int,
        default=None,
        help="每次续写章节数 (默认: 3)"
    )
    parser.add_argument(
        "--time", "-t",
        type=str,
        default="23:00",
        help="执行时间 (例如: 23:00)"
    )
    parser.add_argument(
        "--now",
        action="store_true",
        help="立即执行一次"
    )

    args = parser.parse_args()

    scheduler = NovelScheduler(lang=args.lang, chapters=args.chapters)

    if args.now:
        scheduler.run_now()
    else:
        scheduler.start_schedule(args.time)


if __name__ == "__main__":
    main()