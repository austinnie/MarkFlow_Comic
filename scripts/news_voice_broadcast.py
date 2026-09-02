#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新闻语音播报脚本 - 使用 news_aggregator + voice_assistant

用法：
  python scripts/news_voice_broadcast.py                    # 默认科技新闻
  python scripts/news_voice_broadcast.py --category china   # 中国新闻
  python scripts/news_voice_broadcast.py --top 3            # 只播报3条
  python scripts/news_voice_broadcast.py --play             # 合成后播放
  python scripts/news_voice_broadcast.py --output daily.mp3 # 指定输出文件
  python scripts/news_voice_broadcast.py --chunk-size 10000 # 指定每段最大字符数
"""

import sys
import argparse
import re
import shutil
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from markflow.cli.commands import execute_skill


class NewsVoiceBroadcast:
    """新闻语音播报器 - 使用 news_aggregator + voice_assistant"""
    
    def __init__(self):
        # 统一输出目录
        self.news_dir = project_root / "news_broadcast"
        self.report_dir = self.news_dir / "reports"
        self.audio_dir = self.news_dir / "audio"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.category_names = {
            "tech": "科技",
            "business": "财经",
            "world": "国际",
            "china": "中国",
            "usa": "美国",
            "japan": "日本",
            "korea": "韩国",
        }
    
    def _fetch_news(self, category: str, top_n: int) -> list:
        """通过 news_aggregator 技能抓取新闻"""
        print(f"📡 调用 news_aggregator 抓取 {category} 新闻...")
        
        try:
            result = execute_skill(
                "news_aggregator",
                category=category,
                top_n=top_n
            )
            
            if result and result.get("status") == "success":
                result_data = result.get("result", {})
                articles = result_data.get("articles", [])
                total = result_data.get("unique_count", 0)
                print(f"✅ 抓取到 {total} 条新闻，取前 {len(articles)} 条播报")
                return articles
            else:
                print(f"❌ 抓取失败: {result}")
                return []
                
        except Exception as e:
            print(f"❌ 抓取异常: {e}")
            return []
    
    def _format_news_text(self, news_list: list, category: str) -> str:
        """格式化新闻为播报文本"""
        category_name = self.category_names.get(category, category)
        lines = []
        
        lines.append(f"欢迎收听 {category_name} 新闻简报。")
        lines.append(f"共 {len(news_list)} 条新闻。")
        lines.append("")
        
        for i, news in enumerate(news_list, 1):
            title = news.get("title", "")
            summary = news.get("summary", "")
            source = news.get("source", "未知来源")
            
            title = re.sub(r'[\[\]]', '', title)
            summary = re.sub(r'[\[\]]', '', summary)
            
            lines.append(f"新闻 {i}：{title}")
            if summary and len(summary) > 20:
                # 语音播报摘要截取 200 字符（太长会影响体验）
                summary_text = summary[:200] + "..." if len(summary) > 200 else summary
                lines.append(f"摘要：{summary_text}")
            lines.append(f"来源：{source}")
            lines.append("")
        
        lines.append("新闻播报结束。感谢收听。")
        
        return "\n".join(lines)
    
    def _save_report(self, text: str, category: str) -> Path:
        """保存新闻报告到统一目录"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f"news_{category}_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(text)
        return report_file
        
    def _text_to_speech(self, text: str, category: str, output_file: str = None, chunk_size: int = None) -> str:
        """调用 voice_assistant 合成语音，输出到统一目录"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"news_{category}_{timestamp}.mp3"
        
        output_path = self.audio_dir / output_file
        
        print(f"🔊 正在合成语音: {output_path.name}")
        
        try:
            # 构建参数
            kwargs = {
                "action": "tts",
                "text": text,
                "voice": "zh-CN-XiaoxiaoNeural",
                "speed": 1.0,
                "output_file": str(output_path)
            }
            
            # 如果指定了 chunk_size，传递给 voice_assistant
            if chunk_size is not None:
                kwargs["chunk_size"] = chunk_size
                kwargs["auto_split"] = False
                print(f"   📏 使用自定义 chunk_size: {chunk_size}")
            
            result = execute_skill("voice_assistant", **kwargs)
            
            if result and result.get("status") == "success":
                result_data = result.get("result", {})
                audio_path = result_data.get("audio_path", str(output_path))
                print(f"✅ 语音合成完成: {audio_path}")
                return str(audio_path)
            else:
                print(f"❌ 语音合成失败")
                return None
                
        except Exception as e:
            print(f"❌ 语音合成异常: {e}")
            return None
        
    def _play_audio(self, audio_path: str):
        """使用 music_player 播放音频"""
        if not audio_path or not Path(audio_path).exists():
            print(f"❌ 音频文件不存在: {audio_path}")
            return
        
        print(f"▶️ 使用 music_player 播放: {audio_path}")
        
        try:
            result = execute_skill(
                "music_player",
                action="play",
                path=audio_path
            )
            
            if result and result.get("status") == "success":
                print(f"✅ 播放成功")
            else:
                print(f"❌ 播放失败: {result}")
                
        except Exception as e:
            print(f"❌ 播放异常: {e}")
    
    def run(self, category: str = "tech", top_n: int = 50, 
            output_file: str = None, play: bool = False, 
            save_text: bool = False, chunk_size: int = None):
        """运行新闻语音播报"""
        print("\n" + "=" * 60)
        print("   📻 新闻语音播报器")
        print("=" * 60)
        
        # 1. 抓取新闻
        news_list = self._fetch_news(category, top_n)
        
        if not news_list:
            print("❌ 未抓取到新闻")
            return
        
        # 2. 格式化文本
        text = self._format_news_text(news_list, category)
        
        # 3. 保存报告
        report_file = self._save_report(text, category)
        print(f"📄 新闻报告已保存: {report_file}")
        
        # 4. 显示预览
        print("\n" + "-" * 60)
        print("📝 播报内容预览:")
        print("-" * 60)
        lines = text.split("\n")
        for line in lines[:15]:
            print(line)
        if len(lines) > 15:
            print("... (共 {} 行)".format(len(lines)))
        print("-" * 60)
        
        # 5. 合成语音
        audio_path = self._text_to_speech(text, category, output_file, chunk_size)
        
        # 6. 播放
        if play and audio_path:
            self._play_audio(audio_path)
        
        print("\n" + "=" * 60)
        print("✅ 播报完成!")
        print(f"📄 报告: {report_file}")
        print(f"🎵 音频: {audio_path}")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="新闻语音播报器 - 抓取新闻 + 语音合成",
        epilog="示例:\n"
               "  python scripts/news_voice_broadcast.py                    # 默认科技新闻\n"
               "  python scripts/news_voice_broadcast.py --category china   # 中国新闻\n"
               "  python scripts/news_voice_broadcast.py --top 3            # 只播报3条\n"
               "  python scripts/news_voice_broadcast.py --play             # 合成后播放\n"
               "  python scripts/news_voice_broadcast.py --output daily.mp3 # 指定文件名\n"
               "  python scripts/news_voice_broadcast.py --chunk-size 10000 # 指定每段最大字符数"
    )
    parser.add_argument("--category", "-c", default="tech",
                        help="新闻分类 (tech/business/world/china/usa/japan/korea)")
    parser.add_argument("--top", "-t", type=int, default=50,
                        help="播报新闻条数 (默认: 50)")
    parser.add_argument("--output", "-o", default=None,
                        help="输出音频文件名 (默认: 自动生成)")
    parser.add_argument("--play", "-p", action="store_true",
                        help="合成后播放音频")
    parser.add_argument("--chunk-size", type=int, default=None,
                        help="每段最大字符数 (覆盖 voice_assistant 默认配置，默认 5000)")
    parser.add_argument("--save-text", "-s", action="store_true",
                        help="保存播报文本")
    
    args = parser.parse_args()
    
    broadcaster = NewsVoiceBroadcast()
    broadcaster.run(
        category=args.category,
        top_n=args.top,
        output_file=args.output,
        play=args.play,
        save_text=args.save_text,
        chunk_size=args.chunk_size
    )


if __name__ == "__main__":
    main()