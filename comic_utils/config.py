import json
from pathlib import Path
from typing import Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_FILE = PROJECT_ROOT / "comic_config.json"

DEFAULT_CONFIG = {
    "project": {
        "name": "星际冒险",
        "version": "1.0.0",
        "description": "科幻冒险漫画系列"
    },
    "novel": {
        "genre": "科幻",
        "title": "星际冒险",
        "language": "zh",
        "chapters": 3,
        "outline": "少年意外获得星际航行能力，在宇宙中探索未知文明",
        "characters": "主角阿星，16岁，好奇心强；AI助手小智，幽默风趣"
    },
    "manga": {
        "title": "星际冒险",
        "pages": 4,
        "style": "manga",
        "strength": 0.65,
        "steps": 30,
        "negative": "ugly, deformed, bad anatomy, extra limbs, blurry, low quality",
        "size": {"width": 512, "height": 768}
    },
    "bubbles": {
        "default_dialogues": [
            "欢迎来到星际冒险！",
            "我是艾琳，一起出发吧！",
            "前方有未知的星球！",
            "我们一定会成功的！"
        ],
        "positions": [[50, 50], [200, 200]],
        "bubble_style": "rounded"
    },
    "export": {
        "formats": ["pdf", "epub"],
        "page_size": "A4",
        "author": "AI 生成"
    },
    "continue": {
        "enabled": True,
        "auto_detect": True,
        "max_chapters": 50
    }
}


class ComicConfig:
    """漫画配置管理器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self._config = None
        self._load()
    
    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                print(f"✅ 已加载配置: {self.config_path}")
                return
            except Exception as e:
                print(f"⚠️ 加载配置失败: {e}，使用默认配置")
        
        self._config = DEFAULT_CONFIG.copy()
        self._save()
        print(f"✅ 使用默认配置，已创建: {self.config_path}")
    
    def _save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save()
    
    def get_dialogues(self, page_index: int = 0) -> List[str]:
        dialogues = self.get('bubbles.default_dialogues', [])
        if not dialogues:
            return ["你好", "世界"]
        if page_index < len(dialogues):
            return [dialogues[page_index]]
        return [dialogues[page_index % len(dialogues)]]
    
    def get_positions(self) -> List[List[int]]:
        return self.get('bubbles.positions', [[50, 50]])
    
    @property
    def config(self):
        return self._config
    
    @property
    def novel_config(self):
        return self._config.get('novel', {})
    
    @property
    def manga_config(self):
        return self._config.get('manga', {})
    
    @property
    def bubble_config(self):
        return self._config.get('bubbles', {})
    
    @property
    def export_config(self):
        return self._config.get('export', {})
    
    @property
    def project_config(self):
        return self._config.get('project', {})


config = ComicConfig()