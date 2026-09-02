#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速添加新技能到 MarkFlow 框架

用法：
  python scripts/add_skill.py --list              # 列出所有待添加的技能
  python scripts/add_skill.py --id 8              # 添加技能 #8 (音乐播放器)
  python scripts/add_skill.py --all               # 添加所有待实现技能
  python scripts/add_skill.py --id 8 --force      # 强制覆盖已有技能
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class SkillAdder:
    """技能添加器 - 从技能清单生成技能文件"""

    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir).resolve()
        self.skills_dir = self.root / "skills"
        self.templates_dir = self.root / "markflow" / "templates" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.skills_data = self._load_skills_data()

    def _load_skills_data(self) -> Dict:
        return {
            "implemented": [1, 2, 3, 4, 5, 6, 7],
            "pending": {
                8: {
                    "name": "music_player",
                    "display_name": "音乐播放器",
                    "category": "AI 生成",
                    "description": "AI 智能歌单生成和音乐管理",
                    "difficulty": "⭐⭐",
                    "inputs": [
                        {"name": "action", "type": "string", "required": True,
                         "description": "操作 (play/search/playlist/lyrics)", "default": ""},
                        {"name": "query", "type": "string", "required": False,
                         "description": "搜索关键词", "default": ""},
                        {"name": "playlist_name", "type": "string", "required": False,
                         "description": "播放列表名", "default": ""},
                        {"name": "mood", "type": "string", "required": False,
                         "description": "情绪 (happy/sad/relax/energetic)", "default": "happy"},
                    ],
                    "outputs": [
                        {"name": "tracks", "description": "歌曲列表"},
                        {"name": "playlist", "description": "生成的播放列表"},
                        {"name": "lyrics", "description": "歌词内容"},
                    ],
                    "dependencies": ["spotipy", "yt-dlp", "mutagen", "pygame"],
                    "features": ["AI 歌单推荐", "音乐搜索", "歌词显示", "本地播放"]
                },
                9: {
                    "name": "code_reviewer",
                    "display_name": "代码审查助手",
                    "category": "开发工具",
                    "description": "AI 代码审查，发现问题和安全风险",
                    "difficulty": "⭐⭐⭐",
                    "inputs": [
                        {"name": "code_path", "type": "string", "required": True,
                         "description": "代码文件或目录路径", "default": ""},
                        {"name": "language", "type": "string", "required": False,
                         "description": "编程语言 (python/js/go)", "default": "python"},
                        {"name": "review_level", "type": "string", "required": False,
                         "description": "审查深度 (basic/deep)", "default": "basic"},
                        {"name": "focus", "type": "string", "required": False,
                         "description": "审查重点 (security/performance/style)", "default": "security"},
                    ],
                    "outputs": [
                        {"name": "issues", "description": "发现的问题列表"},
                        {"name": "suggestions", "description": "改进建议"},
                        {"name": "security_risks", "description": "安全风险警告"},
                        {"name": "code_score", "description": "代码质量评分"},
                    ],
                    "dependencies": ["pylint", "flake8", "radon", "ollama"],
                    "features": ["代码质量检查", "安全漏洞扫描", "性能分析", "AI 改进建议"]
                },
                10: {
                    "name": "markdown_to_ppt",
                    "display_name": "Markdown 转 PPT",
                    "category": "开发工具",
                    "description": "Markdown 文档自动转换为演示文稿",
                    "difficulty": "⭐⭐",
                    "inputs": [
                        {"name": "md_file", "type": "string", "required": True,
                         "description": "Markdown 文件路径", "default": ""},
                        {"name": "theme", "type": "string", "required": False,
                         "description": "主题 (default/modern/elegant)", "default": "default"},
                        {"name": "output_format", "type": "string", "required": False,
                         "description": "输出格式 (pptx/pdf)", "default": "pptx"},
                        {"name": "include_code", "type": "boolean", "required": False,
                         "description": "是否包含代码块", "default": True},
                    ],
                    "outputs": [
                        {"name": "ppt_path", "description": "生成的 PPT 路径"},
                        {"name": "slide_count", "description": "幻灯片数量"},
                    ],
                    "dependencies": ["python-pptx", "markdown", "beautifulsoup4"],
                    "features": ["Markdown 转 PPT", "多种主题", "代码高亮", "批量转换"]
                },
                11: {
                    "name": "web_scraper",
                    "display_name": "网页爬虫",
                    "category": "开发工具",
                    "description": "自动采集网页数据",
                    "difficulty": "⭐⭐⭐",
                    "inputs": [
                        {"name": "url", "type": "string", "required": True,
                         "description": "目标网址", "default": ""},
                        {"name": "selectors", "type": "json", "required": False,
                         "description": "CSS 选择器配置", "default": ""},
                        {"name": "action", "type": "string", "required": False,
                         "description": "操作 (scrape/download/screenshot)", "default": "scrape"},
                        {"name": "output_format", "type": "string", "required": False,
                         "description": "输出格式 (json/csv/html)", "default": "json"},
                    ],
                    "outputs": [
                        {"name": "data", "description": "采集的数据"},
                        {"name": "screenshot", "description": "截图路径"},
                        {"name": "stats", "description": "采集统计"},
                    ],
                    "dependencies": ["requests", "beautifulsoup4", "selenium", "playwright"],
                    "features": ["静态页面爬取", "动态页面渲染", "截图功能", "多种输出格式"]
                },
                12: {
                    "name": "data_analyst",
                    "display_name": "数据分析师",
                    "category": "数据处理",
                    "description": "CSV/Excel 自动分析生成报告",
                    "difficulty": "⭐⭐",
                    "inputs": [
                        {"name": "data_file", "type": "string", "required": True,
                         "description": "数据文件路径", "default": ""},
                        {"name": "analysis_type", "type": "string", "required": False,
                         "description": "分析类型 (summary/correlation/trend)", "default": "summary"},
                        {"name": "output_format", "type": "string", "required": False,
                         "description": "输出格式 (html/pdf/md)", "default": "html"},
                        {"name": "target_columns", "type": "string", "required": False,
                         "description": "要分析的列名", "default": ""},
                    ],
                    "outputs": [
                        {"name": "report", "description": "分析报告"},
                        {"name": "charts", "description": "图表路径"},
                        {"name": "insights", "description": "数据洞察"},
                    ],
                    "dependencies": ["pandas", "numpy", "matplotlib", "seaborn", "plotly"],
                    "features": ["数据统计分析", "可视化图表", "自动生成报告", "相关性分析"]
                },
                13: {
                    "name": "news_aggregator",
                    "display_name": "新闻聚合器",
                    "category": "数据处理",
                    "description": "RSS 新闻抓取 + AI 摘要生成",
                    "difficulty": "⭐⭐",
                    "inputs": [
                        {"name": "sources", "type": "string", "required": False,
                         "description": "RSS 源列表", "default": ""},
                        {"name": "category", "type": "string", "required": False,
                         "description": "新闻分类 (tech/business/world)", "default": "tech"},
                        {"name": "top_n", "type": "integer", "required": False,
                         "description": "提取 Top N 条新闻", "default": 10},
                        {"name": "summary_length", "type": "integer", "required": False,
                         "description": "摘要长度", "default": 100},
                    ],
                    "outputs": [
                        {"name": "news", "description": "新闻列表"},
                        {"name": "summaries", "description": "AI 摘要"},
                        {"name": "daily_report", "description": "每日简报"},
                    ],
                    "dependencies": ["feedparser", "requests", "ollama"],
                    "features": ["RSS 抓取", "AI 摘要", "分类聚合", "每日简报"]
                },
                14: {
                    "name": "stock_monitor",
                    "display_name": "股票数据监控",
                    "category": "数据处理",
                    "description": "股票价格监控和预警",
                    "difficulty": "⭐⭐",
                    "inputs": [
                        {"name": "symbols", "type": "string", "required": True,
                         "description": "股票代码列表", "default": ""},
                        {"name": "action", "type": "string", "required": False,
                         "description": "操作 (price/history/alert)", "default": "price"},
                        {"name": "start_date", "type": "string", "required": False,
                         "description": "开始日期", "default": ""},
                        {"name": "end_date", "type": "string", "required": False,
                         "description": "结束日期", "default": ""},
                        {"name": "alert_threshold", "type": "float", "required": False,
                         "description": "价格预警阈值", "default": 0.0},
                    ],
                    "outputs": [
                        {"name": "prices", "description": "股价数据"},
                        {"name": "history", "description": "历史数据"},
                        {"name": "alerts", "description": "预警列表"},
                    ],
                    "dependencies": ["yfinance", "pandas", "requests"],
                    "features": ["实时股价", "历史数据", "价格预警", "技术指标"]
                },
                15: {
                    "name": "email_assistant",
                    "display_name": "智能邮件助手",
                    "category": "自动化",
                    "description": "邮件自动撰写、分类、回复",
                    "difficulty": "⭐⭐⭐",
                    "inputs": [
                        {"name": "action", "type": "string", "required": True,
                         "description": "操作 (write/reply/summarize/classify)", "default": ""},
                        {"name": "recipient", "type": "string", "required": False,
                         "description": "收件人", "default": ""},
                        {"name": "subject", "type": "string", "required": False,
                         "description": "邮件主题", "default": ""},
                        {"name": "content", "type": "string", "required": False,
                         "description": "邮件内容", "default": ""},
                        {"name": "tone", "type": "string", "required": False,
                         "description": "语气 (formal/friendly/professional)", "default": "formal"},
                    ],
                    "outputs": [
                        {"name": "draft", "description": "邮件草稿"},
                        {"name": "category", "description": "邮件分类"},
                        {"name": "summary", "description": "邮件摘要"},
                    ],
                    "dependencies": ["smtplib", "email", "ollama"],
                    "features": ["邮件撰写", "智能回复", "邮件分类", "摘要生成"]
                },
                16: {
                    "name": "file_renamer",
                    "display_name": "文件批量重命名",
                    "category": "自动化",
                    "description": "智能批量重命名工具",
                    "difficulty": "⭐",
                    "inputs": [
                        {"name": "directory", "type": "string", "required": True,
                         "description": "目标目录", "default": ""},
                        {"name": "pattern", "type": "string", "required": False,
                         "description": "命名模式", "default": "{prefix}_{number}{suffix}"},
                        {"name": "prefix", "type": "string", "required": False,
                         "description": "前缀", "default": ""},
                        {"name": "suffix", "type": "string", "required": False,
                         "description": "后缀", "default": ""},
                        {"name": "start_number", "type": "integer", "required": False,
                         "description": "起始编号", "default": 1},
                        {"name": "dry_run", "type": "boolean", "required": False,
                         "description": "预览模式", "default": True},
                    ],
                    "outputs": [
                        {"name": "renamed", "description": "重命名的文件列表"},
                        {"name": "preview", "description": "预览结果"},
                    ],
                    "dependencies": ["os", "shutil"],
                    "features": ["批量重命名", "预览模式", "自定义模式", "编号排序"]
                },
                17: {
                    "name": "task_scheduler",
                    "display_name": "定时任务调度",
                    "category": "自动化",
                    "description": "定时执行自动化任务",
                    "difficulty": "⭐⭐",
                    "inputs": [
                        {"name": "task_type", "type": "string", "required": True,
                         "description": "任务类型 (backup/clean/update)", "default": ""},
                        {"name": "schedule", "type": "string", "required": False,
                         "description": "调度规则 (daily/weekly/monthly)", "default": "daily"},
                        {"name": "time", "type": "string", "required": False,
                         "description": "执行时间", "default": "00:00"},
                        {"name": "script_path", "type": "string", "required": False,
                         "description": "执行的脚本路径", "default": ""},
                    ],
                    "outputs": [
                        {"name": "task_id", "description": "任务 ID"},
                        {"name": "status", "description": "任务状态"},
                        {"name": "logs", "description": "执行日志"},
                    ],
                    "dependencies": ["schedule", "apscheduler"],
                    "features": ["定时执行", "多种调度", "任务管理", "日志记录"]
                },
                18: {
                    "name": "social_media",
                    "display_name": "社交媒体管理",
                    "category": "自动化",
                    "description": "多平台内容发布和管理",
                    "difficulty": "⭐⭐⭐",
                    "inputs": [
                        {"name": "platform", "type": "string", "required": True,
                         "description": "平台 (twitter/weibo/bilibili)", "default": ""},
                        {"name": "action", "type": "string", "required": False,
                         "description": "操作 (post/schedule/analytics)", "default": "post"},
                        {"name": "content", "type": "string", "required": False,
                         "description": "发布内容", "default": ""},
                        {"name": "media_path", "type": "string", "required": False,
                         "description": "媒体文件路径", "default": ""},
                        {"name": "schedule_time", "type": "string", "required": False,
                         "description": "定时发布时间", "default": ""},
                    ],
                    "outputs": [
                        {"name": "post_id", "description": "发布 ID"},
                        {"name": "url", "description": "发布链接"},
                        {"name": "analytics", "description": "数据分析"},
                    ],
                    "dependencies": ["tweepy", "requests"],
                    "features": ["多平台发布", "定时发布", "数据分析", "内容管理"]
                },
                19: {
                    "name": "youtube_assistant",
                    "display_name": "YouTube 视频助手",
                    "category": "知识管理",
                    "description": "视频信息、字幕下载、AI 摘要",
                    "difficulty": "⭐⭐⭐",
                    "inputs": [
                        {"name": "url", "type": "string", "required": True,
                         "description": "YouTube 视频链接", "default": ""},
                        {"name": "action", "type": "string", "required": False,
                         "description": "操作 (info/transcript/summary/download)", "default": "info"},
                        {"name": "language", "type": "string", "required": False,
                         "description": "字幕语言", "default": "zh-CN"},
                    ],
                    "outputs": [
                        {"name": "info", "description": "视频信息"},
                        {"name": "transcript", "description": "字幕内容"},
                        {"name": "summary", "description": "AI 摘要"},
                        {"name": "download_path", "description": "下载路径"},
                    ],
                    "dependencies": ["pytube", "youtube-transcript-api", "requests"],
                    "features": ["视频信息获取", "字幕下载", "AI 摘要", "视频下载"]
                },
                20: {
                    "name": "knowledge_base",
                    "display_name": "知识库助手",
                    "category": "知识管理",
                    "description": "文档构建问答知识库",
                    "difficulty": "⭐⭐⭐⭐",
                    "inputs": [
                        {"name": "doc_path", "type": "string", "required": True,
                         "description": "文档路径或目录", "default": ""},
                        {"name": "question", "type": "string", "required": False,
                         "description": "用户问题", "default": ""},
                        {"name": "action", "type": "string", "required": False,
                         "description": "操作 (index/query)", "default": "query"},
                        {"name": "context", "type": "string", "required": False,
                         "description": "额外上下文", "default": ""},
                    ],
                    "outputs": [
                        {"name": "answer", "description": "回答"},
                        {"name": "sources", "description": "引用来源"},
                        {"name": "indexed_docs", "description": "已索引文档"},
                    ],
                    "dependencies": ["langchain", "chromadb", "sentence-transformers", "ollama"],
                    "features": ["文档索引", "智能问答", "RAG 检索", "多文档支持"]
                }
            }
        }

    def get_pending_skills(self) -> List[Dict]:
        pending = []
        for sid, data in self.skills_data["pending"].items():
            pending.append({
                "id": sid,
                "name": data["name"],
                "display_name": data["display_name"],
                "category": data["category"],
                "description": data["description"],
                "difficulty": data["difficulty"],
            })
        return sorted(pending, key=lambda x: x["id"])

    def is_implemented(self, skill_id: int) -> bool:
        return skill_id in self.skills_data["implemented"]

    def generate_skill_files(self, skill_id: int, overwrite: bool = False) -> bool:
        if self.is_implemented(skill_id):
            print(f"跳过技能 #{skill_id}（已实现）")
            return False

        data = self.skills_data["pending"].get(skill_id)
        if not data:
            print(f"技能 ID {skill_id} 不存在")
            return False

        skill_name = data["name"]
        skill_dir = self.skills_dir / skill_name

        if skill_dir.exists() and not overwrite:
            print(f"技能 {skill_name} 已存在，使用 --force 覆盖")
            return False

        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "output").mkdir(exist_ok=True)

        # meta.json
        meta = {
            "name": data["display_name"],
            "description": data["description"],
            "version": "1.0.0",
            "inputs": data["inputs"],
            "outputs": data["outputs"],
            "dependencies": data["dependencies"],
            "tags": [data["category"], "pending"],
            "difficulty": data["difficulty"]
        }
        with open(skill_dir / "meta.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # skill.py
        with open(skill_dir / "skill.py", "w", encoding="utf-8") as f:
            f.write(self._generate_skill_py(data))

        # skill.md
        with open(skill_dir / "skill.md", "w", encoding="utf-8") as f:
            f.write(self._generate_skill_md(data))

        # README.md
        with open(skill_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(self._generate_readme(data))

        # 模板文件
        template_path = self.templates_dir / f"{skill_name}.md"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(self._generate_template_md(data))

        print(f"已创建技能: {skill_name} (ID: {skill_id})")
        return True

    def _generate_skill_py(self, data: Dict) -> str:
        skill_name = data["name"]
        display_name = data["display_name"]
        class_name = ''.join(word.capitalize() for word in skill_name.split('_'))
        features = data.get("features", [])
        features_str = "\n".join([f"  - {f}" for f in features])
        required = [inp["name"] for inp in data.get("inputs", []) if inp.get("required", False)]
        required_str = ', '.join([f'"{r}"' for r in required])

        lines = []
        lines.append('"""')
        lines.append(skill_name + ' - ' + display_name)
        lines.append('')
        lines.append(data["description"])
        lines.append('')
        lines.append('功能:')
        lines.append(features_str)
        lines.append('"""')
        lines.append('')
        lines.append('import os')
        lines.append('import time')
        lines.append('import json')
        lines.append('import logging')
        lines.append('from pathlib import Path')
        lines.append('from typing import Dict, Any, Optional, List')
        lines.append('from datetime import datetime')
        lines.append('')
        lines.append('logger = logging.getLogger(__name__)')
        lines.append('')
        lines.append('')
        lines.append('class ' + class_name + ':')
        lines.append('    """')
        lines.append('    ' + display_name)
        lines.append('    """')
        lines.append('    ')
        lines.append('    def __init__(self, config: Dict[str, Any] = None):')
        lines.append('        self.config = config or {}')
        lines.append('        self.name = "' + skill_name + '"')
        lines.append('        self.version = "1.0.0"')
        lines.append('        self._setup_logging()')
        lines.append('        self._setup_config()')
        lines.append('        logger.info(f"' + display_name + ' 初始化完成")')
        lines.append('    ')
        lines.append('    def _setup_logging(self):')
        lines.append('        log_level = self.config.get("log_level", "INFO")')
        lines.append('        logging.basicConfig(')
        lines.append('            level=getattr(logging, log_level.upper()),')
        lines.append('            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"')
        lines.append('        )')
        lines.append('    ')
        lines.append('    def _setup_config(self):')
        lines.append('        defaults = {')
        lines.append('            "output_dir": "./skills/' + skill_name + '/output",')
        lines.append('        }')
        lines.append('        for key, value in defaults.items():')
        lines.append('            if key not in self.config:')
        lines.append('                self.config[key] = value')
        lines.append('    ')
        lines.append('    def _validate_inputs(self, **kwargs) -> bool:')
        lines.append('        required = [' + required_str + ']')
        lines.append('        for param in required:')
        lines.append('            if param not in kwargs or not kwargs[param]:')
        lines.append('                raise ValueError(f"缺少必需参数: {param}")')
        lines.append('        return True')
        lines.append('    ')
        lines.append('    def execute(self, **kwargs) -> Dict[str, Any]:')
        lines.append('        start_time = time.time()')
        lines.append('        logger.info(f"执行技能: {self.name} (v{self.version})")')
        lines.append('        ')
        lines.append('        try:')
        lines.append('            self._validate_inputs(**kwargs)')
        lines.append('            result = {')
        lines.append('                "status": "success",')
        lines.append('                "message": f"' + display_name + ' 执行成功",')
        lines.append('                "params": kwargs')
        lines.append('            }')
        lines.append('            return {')
        lines.append('                "status": "success",')
        lines.append('                "result": result,')
        lines.append('                "metadata": {')
        lines.append('                    "skill": self.name,')
        lines.append('                    "version": self.version,')
        lines.append('                    "executed_at": datetime.now().isoformat()')
        lines.append('                }')
        lines.append('            }')
        lines.append('        except Exception as e:')
        lines.append('            logger.error(f"执行失败: {e}")')
        lines.append('            return {')
        lines.append('                "status": "error",')
        lines.append('                "error": str(e),')
        lines.append('                "skill": self.name,')
        lines.append('                "timestamp": datetime.now().isoformat()')
        lines.append('            }')
        lines.append('    ')
        lines.append('    def __repr__(self):')
        lines.append('        return f"<' + class_name + '(name={self.name}, version={self.version})>"')

        return "\n".join(lines)

    def _generate_skill_md(self, data: Dict) -> str:
        lines = []
        lines.append("# " + data["display_name"])
        lines.append("")
        lines.append("## 描述")
        lines.append(data["description"])
        lines.append("")
        lines.append("## 类别")
        lines.append(data.get("category", "未分类"))
        lines.append("")
        lines.append("## 难度")
        lines.append(data.get("difficulty", "⭐"))
        lines.append("")
        lines.append("## 输入")
        for inp in data.get("inputs", []):
            required = "必填" if inp.get("required", False) else "可选"
            line = "- **" + inp["name"] + "** (" + inp["type"] + "): " + inp["description"] + " (" + required + ")"
            lines.append(line)
            if inp.get("default") is not None:
                lines.append("  - 默认: " + str(inp["default"]))
        lines.append("")
        lines.append("## 输出")
        for out in data.get("outputs", []):
            lines.append("- **" + out["name"] + "**: " + out["description"])
        lines.append("")
        lines.append("## 依赖")
        for dep in data.get("dependencies", []):
            lines.append("- " + dep)
        lines.append("")
        lines.append("## 功能")
        for feature in data.get("features", []):
            lines.append("- " + feature)
        lines.append("")
        lines.append("## 状态")
        lines.append("待实现")
        return "\n".join(lines)

    def _generate_readme(self, data: Dict) -> str:
        skill_name = data["name"]
        display_name = data["display_name"]
        lines = []
        lines.append("# " + display_name)
        lines.append("")
        lines.append("> " + data["description"])
        lines.append("")
        lines.append("## 技能简介")
        lines.append("")
        lines.append(data["description"])
        lines.append("")
        lines.append("## 类别")
        lines.append("")
        lines.append(data.get("category", "未分类"))
        lines.append("")
        lines.append("## 难度")
        lines.append("")
        lines.append(data.get("difficulty", "⭐"))
        lines.append("")
        lines.append("## 功能")
        lines.append("")
        for f in data.get("features", []):
            lines.append("- " + f)
        lines.append("")
        lines.append("## 依赖")
        lines.append("")
        lines.append("```bash")
        for d in data.get("dependencies", []):
            lines.append("pip install " + d)
        lines.append("```")
        lines.append("")
        lines.append("## 使用方法")
        lines.append("")
        lines.append("```bash")
        lines.append("python -m markflow.cli.commands execute " + skill_name + " [参数]")
        lines.append("```")
        lines.append("")
        lines.append("## 状态")
        lines.append("")
        lines.append("待实现")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*文档自动生成于 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "*")
        return "\n".join(lines)

    def _generate_template_md(self, data: Dict) -> str:
        class_name = ''.join(word.capitalize() for word in data["name"].split('_'))
        lines = []
        lines.append("# " + class_name)
        lines.append("")
        lines.append("## 描述")
        lines.append(data["description"])
        lines.append("")
        lines.append("## 输入")
        for inp in data.get("inputs", []):
            required = " (必填)" if inp.get("required", False) else " (可选)"
            lines.append("- " + inp["name"] + ": " + inp["type"] + ": " + inp["description"] + required)
        lines.append("")
        lines.append("## 输出")
        for out in data.get("outputs", []):
            lines.append("- " + out["name"] + ": " + out["description"])
        lines.append("")
        lines.append("## 依赖")
        for dep in data.get("dependencies", []):
            lines.append("- " + dep)
        lines.append("")
        lines.append("## 状态")
        lines.append("待实现")
        return "\n".join(lines)

    def add_all(self, overwrite: bool = False) -> int:
        added = 0
        for sid in self.skills_data["pending"].keys():
            if self.generate_skill_files(sid, overwrite):
                added += 1
        return added


def main():
    parser = argparse.ArgumentParser(description="快速添加新技能")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有待添加技能")
    parser.add_argument("--id", "-i", type=int, help="添加指定 ID 的技能")
    parser.add_argument("--all", "-a", action="store_true", help="添加所有待实现技能")
    parser.add_argument("--force", "-f", action="store_true", help="强制覆盖已有技能")

    args = parser.parse_args()
    adder = SkillAdder()

    if args.list:
        print("\n待添加技能列表:")
        print("-" * 60)
        for skill in adder.get_pending_skills():
            print(f"#{skill['id']:2d} {skill['display_name']:15} [{skill['category']}] {skill['description']}")
        print("-" * 60)
        print(f"共 {len(adder.get_pending_skills())} 个")
        return

    if args.id:
        if adder.is_implemented(args.id):
            print(f"技能 #{args.id} 已实现，跳过")
            return
        adder.generate_skill_files(args.id, args.force)
        return

    if args.all:
        count = adder.add_all(args.force)
        print(f"已添加 {count} 个技能")
        return

    parser.print_help()


if __name__ == "__main__":
    main()