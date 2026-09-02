# scripts/play_news_audio.py
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""播放最新的新闻音频 - 直接调用播放器"""

import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
audio_dir = project_root / "news_broadcast" / "audio"

# 获取最新 MP3
files = sorted(audio_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)

if not files:
    print("❌ 没有找到音频文件")
    sys.exit(1)

audio_path = str(files[0])
print(f"🎵 播放: {files[0].name}")

# 尝试用 VLC
vlc_paths = [
    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
]
vlc = None
for path in vlc_paths:
    if Path(path).exists():
        vlc = path
        break

if vlc:
    print(f"📺 使用 VLC 播放")
    subprocess.Popen([vlc, audio_path])
else:
    # 用系统默认播放器
    print(f"📺 使用系统播放器")
    os.startfile(audio_path)