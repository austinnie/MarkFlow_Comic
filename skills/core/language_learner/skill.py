"""
language_learner - 外语学习助手

功能:
  - 多语言知识库管理 (单词/语法/句子)
  - 闪卡学习模式
  - 选择题测验
  - 拼写练习
  - 跟读练习 (集成 voice_assistant)
  - 学习进度追踪
  - 复习和统计
  - 词典导入 (Collins/Google/本地)
  - 批量导入 (文本/CSV)
  - 知识库导出 (JSON/CSV)
"""

import os
import time
import json
import logging
import random
import re
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class LanguageLearner:
    """外语学习助手 - 完整学习系统 + 知识库管理"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.name = "language_learner"
        self.version = "1.0.0"
        self._setup_logging()
        self._setup_config()
        
        self.current_lang = self.config.get("default_language", "en")
        self.session = {
            "mode": None,
            "current_item": None,
            "correct": 0,
            "total": 0,
            "started_at": None
        }
        
        self._load_progress()
        self._init_knowledge_base()
        
        logger.info(f"语言学习助手 初始化完成")
    
    def _setup_logging(self):
        log_level = self.config.get("log_level", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # 在 _setup_config 中添加词典源配置
    def _setup_config(self):
        defaults = {
            "output_dir": "./skills/language_learner/output",
            "progress_file": "./skills/language_learner/progress.json",
            "knowledge_base_dir": "./skills/language_learner/knowledge",
            "default_language": "en",
            "dict_api": "https://api.dictionaryapi.dev/api/v2/entries/{lang}/{word}",
            # ✅ 多语言词典源配置
            "dict_sources": {
                "en": {
                    "name": "WordNet",
                    "source": "wordnet",
                    "nltk_corpus": "wordnet",
                    "install_cmd": "nltk.download('wordnet')",
                    "lang": "en"
                },
                "ja": {
                    "name": "Japanese Dictionary",
                    "source": "jamdict",
                    "pip_package": "jamdict",
                    "install_cmd": "pip install jamdict",
                    "lang": "ja"
                },
                "zh": {
                    "name": "Chinese Dictionary",
                    "source": "jieba",
                    "pip_package": "jieba",
                    "install_cmd": "pip install jieba",
                    "lang": "zh"
                },
                "fr": {
                    "name": "French Dictionary",
                    "source": "wordnet",
                    "nltk_corpus": "wordnet",
                    "lang": "fr"
                },
                "de": {
                    "name": "German Dictionary",
                    "source": "wordnet",
                    "nltk_corpus": "wordnet",
                    "lang": "de"
                },
                "es": {
                    "name": "Spanish Dictionary",
                    "source": "wordnet",
                    "nltk_corpus": "wordnet",
                    "lang": "es"
                },
                "ko": {
                    "name": "Korean Dictionary",
                    "source": "korean",
                    "pip_package": "konlpy",
                    "install_cmd": "pip install konlpy",
                    "lang": "ko"
                }
            }
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        
        Path(self.config["output_dir"]).mkdir(parents=True, exist_ok=True)
        Path(self.config["knowledge_base_dir"]).mkdir(parents=True, exist_ok=True)
    
    # ==================== 知识库初始化 ====================
    
    def _init_knowledge_base(self):
        """初始化所有语言知识库"""
        kb_dir = Path(self.config["knowledge_base_dir"])
        
        # 初始化英语
        self._ensure_kb("en", "英语", "en-US-JennyNeural", [
            {"word": "apple", "meaning": "苹果", "example": "I eat an apple every day.", "level": 1},
            {"word": "book", "meaning": "书", "example": "This book is interesting.", "level": 1},
            {"word": "cat", "meaning": "猫", "example": "The cat is sleeping.", "level": 1},
            {"word": "dog", "meaning": "狗", "example": "My dog is friendly.", "level": 1},
            {"word": "happy", "meaning": "开心的", "example": "She looks happy.", "level": 1},
            {"word": "school", "meaning": "学校", "example": "I go to school.", "level": 1},
            {"word": "teacher", "meaning": "老师", "example": "My teacher is kind.", "level": 1},
            {"word": "student", "meaning": "学生", "example": "The student studies.", "level": 1},
            {"word": "family", "meaning": "家庭", "example": "I love my family.", "level": 1},
            {"word": "friend", "meaning": "朋友", "example": "He is my friend.", "level": 1},
            {"word": "water", "meaning": "水", "example": "I drink water.", "level": 1},
            {"word": "food", "meaning": "食物", "example": "The food is good.", "level": 1},
            {"word": "love", "meaning": "爱", "example": "I love you.", "level": 2},
            {"word": "beautiful", "meaning": "美丽的", "example": "She is beautiful.", "level": 2},
            {"word": "important", "meaning": "重要的", "example": "This is important.", "level": 2},
            {"word": "different", "meaning": "不同的", "example": "We are different.", "level": 2},
            {"word": "interesting", "meaning": "有趣的", "example": "This is interesting.", "level": 2},
            {"word": "delicious", "meaning": "美味的", "example": "The food is delicious.", "level": 2},
            {"word": "wonderful", "meaning": "精彩的", "example": "It's wonderful!", "level": 3},
            {"word": "fantastic", "meaning": "极好的", "example": "That's fantastic!", "level": 3},
        ], [
            {"en": "How are you?", "zh": "你好吗？", "level": 1},
            {"en": "What is your name?", "zh": "你叫什么名字？", "level": 1},
            {"en": "Where are you from?", "zh": "你从哪里来？", "level": 1},
            {"en": "Nice to meet you!", "zh": "很高兴认识你！", "level": 1},
            {"en": "Can you help me?", "zh": "你能帮我吗？", "level": 1},
            {"en": "I would like some water.", "zh": "我想要一些水。", "level": 2},
            {"en": "How much is this?", "zh": "这个多少钱？", "level": 2},
            {"en": "What time is it?", "zh": "现在几点了？", "level": 2},
            {"en": "I don't understand.", "zh": "我不明白。", "level": 2},
            {"en": "Could you repeat that?", "zh": "你能再说一遍吗？", "level": 2},
            {"en": "I'm sorry.", "zh": "对不起。", "level": 1},
            {"en": "Thank you very much!", "zh": "非常感谢！", "level": 1},
        ], [
            {"title": "一般现在时", "rule": "主语 + 动词原形", "example": "I eat breakfast every day.", "level": 1},
            {"title": "现在进行时", "rule": "主语 + be + 动词ing", "example": "I am reading a book.", "level": 2},
            {"title": "一般过去时", "rule": "主语 + 动词过去式", "example": "I walked to school.", "level": 2},
            {"title": "将来时", "rule": "主语 + will + 动词原形", "example": "I will go tomorrow.", "level": 2},
            {"title": "现在完成时", "rule": "主语 + have/has + 过去分词", "example": "I have finished.", "level": 3},
        ])

        # 初始化日语
        self._ensure_kb("ja", "日语", "ja-JP-NanamiNeural", [
            {"word": "こんにちは", "meaning": "你好", "example": "こんにちは、お元気ですか？", "level": 1},
            {"word": "ありがとう", "meaning": "谢谢", "example": "ありがとうございます。", "level": 1},
            {"word": "すみません", "meaning": "对不起", "example": "すみません、トイレは？", "level": 1},
            {"word": "おはよう", "meaning": "早上好", "example": "おはようございます。", "level": 1},
            {"word": "こんばんは", "meaning": "晚上好", "example": "こんばんは。", "level": 1},
            {"word": "おやすみ", "meaning": "晚安", "example": "おやすみなさい。", "level": 1},
            {"word": "さようなら", "meaning": "再见", "example": "さようなら。", "level": 1},
            {"word": "はい", "meaning": "是的", "example": "はい、わかりました。", "level": 1},
            {"word": "いいえ", "meaning": "不是", "example": "いいえ、違います。", "level": 1},
            {"word": "お願いします", "meaning": "拜托了", "example": "お願いします。", "level": 2},
            {"word": "かわいい", "meaning": "可爱的", "example": "その猫はかわいい。", "level": 2},
            {"word": "おいしい", "meaning": "美味的", "example": "この料理はおいしい。", "level": 2},
        ], [
            {"en": "こんにちは！", "zh": "你好！", "level": 1},
            {"en": "お元気ですか？", "zh": "你好吗？", "level": 1},
            {"en": "お名前は何ですか？", "zh": "你叫什么名字？", "level": 1},
            {"en": "ありがとうございます。", "zh": "非常感谢。", "level": 1},
            {"en": "すみません、助けてください。", "zh": "请帮帮我。", "level": 2},
            {"en": "私は日本語を勉強しています。", "zh": "我在学习日语。", "level": 2},
            {"en": "よくわかりません。", "zh": "我不太明白。", "level": 2},
        ], [
            {"title": "肯定句", "rule": "N1 は N2 です", "example": "私は学生です。", "level": 1},
            {"title": "否定句", "rule": "N1 は N2 じゃないです", "example": "私は学生じゃないです。", "level": 1},
            {"title": "疑问句", "rule": "N1 は N2 ですか？", "example": "あなたは学生ですか？", "level": 1},
            {"title": "存在句", "rule": "場所 に もの が あります", "example": "机の上に本があります。", "level": 2},
        ])

        # 初始化韩语
        self._ensure_kb("ko", "韩语", "ko-KR-SunHiNeural", [
            {"word": "안녕하세요", "meaning": "你好", "example": "안녕하세요, 반갑습니다.", "level": 1},
            {"word": "감사합니다", "meaning": "谢谢", "example": "감사합니다!", "level": 1},
            {"word": "죄송합니다", "meaning": "对不起", "example": "죄송합니다.", "level": 1},
            {"word": "네", "meaning": "是的", "example": "네, 알겠습니다.", "level": 1},
            {"word": "아니요", "meaning": "不是", "example": "아니요, 괜찮아요.", "level": 1},
            {"word": "사랑해요", "meaning": "我爱你", "example": "사랑해요.", "level": 2},
            {"word": "고마워요", "meaning": "谢谢(非正式)", "example": "고마워요!", "level": 2},
            {"word": "괜찮아요", "meaning": "没关系", "example": "괜찮아요.", "level": 2},
        ], [
            {"en": "안녕하세요!", "zh": "你好！", "level": 1},
            {"en": "어떻게 지내세요?", "zh": "你好吗？", "level": 1},
            {"en": "이름이 뭐예요?", "zh": "你叫什么名字？", "level": 1},
            {"en": "감사합니다!", "zh": "谢谢！", "level": 1},
            {"en": "도와주세요!", "zh": "请帮帮我！", "level": 2},
            {"en": "한국어를 공부하고 있어요.", "zh": "我在学习韩语。", "level": 2},
        ], [
            {"title": "基本语序", "rule": "主语 + 宾语 + 动词 (SOV)", "example": "나는 밥을 먹어요。", "level": 1},
            {"title": "敬语终结", "rule": "动词词干 + 아/어요", "example": "먹어요 / 해요", "level": 1},
            {"title": "过去时", "rule": "动词词干 + 았/었어요", "example": "했어요 / 먹었어요", "level": 2},
        ])

        # 初始化法语
        self._ensure_kb("fr", "法语", "fr-FR-DeniseNeural", [
            {"word": "Bonjour", "meaning": "你好", "example": "Bonjour, comment allez-vous?", "level": 1},
            {"word": "Merci", "meaning": "谢谢", "example": "Merci beaucoup!", "level": 1},
            {"word": "Au revoir", "meaning": "再见", "example": "Au revoir!", "level": 1},
            {"word": "Oui", "meaning": "是的", "example": "Oui, je comprends.", "level": 1},
            {"word": "Non", "meaning": "不是", "example": "Non, je ne suis pas d'accord.", "level": 1},
            {"word": "S'il vous plaît", "meaning": "请", "example": "S'il vous plaît.", "level": 1},
            {"word": "Je t'aime", "meaning": "我爱你", "example": "Je t'aime.", "level": 2},
        ], [
            {"en": "Bonjour!", "zh": "你好！", "level": 1},
            {"en": "Comment allez-vous?", "zh": "你好吗？", "level": 1},
            {"en": "Je m'appelle...", "zh": "我叫...", "level": 1},
            {"en": "Merci beaucoup!", "zh": "非常感谢！", "level": 1},
            {"en": "Pouvez-vous m'aider?", "zh": "你能帮我吗？", "level": 2},
        ], [
            {"title": "主谓结构", "rule": "主语 + 动词 + 宾语", "example": "Je parle français.", "level": 1},
            {"title": "否定句", "rule": "主语 + ne + 动词 + pas", "example": "Je ne parle pas anglais.", "level": 2},
        ])

        # 初始化德语
        self._ensure_kb("de", "德语", "de-DE-KatjaNeural", [
            {"word": "Hallo", "meaning": "你好", "example": "Hallo, wie geht es dir?", "level": 1},
            {"word": "Danke", "meaning": "谢谢", "example": "Danke schön!", "level": 1},
            {"word": "Tschüss", "meaning": "再见", "example": "Tschüss!", "level": 1},
            {"word": "Ja", "meaning": "是的", "example": "Ja, ich verstehe.", "level": 1},
            {"word": "Nein", "meaning": "不是", "example": "Nein, nicht einverstanden.", "level": 1},
            {"word": "Bitte", "meaning": "请", "example": "Bitte, hilf mir.", "level": 1},
            {"word": "Ich liebe dich", "meaning": "我爱你", "example": "Ich liebe dich.", "level": 2},
        ], [
            {"en": "Hallo!", "zh": "你好！", "level": 1},
            {"en": "Wie geht es dir?", "zh": "你好吗？", "level": 1},
            {"en": "Ich heiße...", "zh": "我叫...", "level": 1},
            {"en": "Danke schön!", "zh": "非常感谢！", "level": 1},
            {"en": "Kannst du mir helfen?", "zh": "你能帮我吗？", "level": 2},
        ], [
            {"title": "主谓结构", "rule": "主语 + 动词 + 宾语", "example": "Ich spreche Deutsch.", "level": 1},
            {"title": "否定句", "rule": "主语 + 动词 + nicht", "example": "Ich spreche nicht Englisch.", "level": 2},
        ])

        # 初始化西班牙语
        self._ensure_kb("es", "西班牙语", "es-ES-ElviraNeural", [
            {"word": "Hola", "meaning": "你好", "example": "Hola, ¿cómo estás?", "level": 1},
            {"word": "Gracias", "meaning": "谢谢", "example": "¡Muchas gracias!", "level": 1},
            {"word": "Adiós", "meaning": "再见", "example": "Adiós!", "level": 1},
            {"word": "Sí", "meaning": "是的", "example": "Sí, entiendo.", "level": 1},
            {"word": "No", "meaning": "不是", "example": "No, no estoy de acuerdo.", "level": 1},
            {"word": "Por favor", "meaning": "请", "example": "Por favor.", "level": 1},
            {"word": "Te quiero", "meaning": "我爱你", "example": "Te quiero.", "level": 2},
        ], [
            {"en": "¡Hola!", "zh": "你好！", "level": 1},
            {"en": "¿Cómo estás?", "zh": "你好吗？", "level": 1},
            {"en": "Me llamo...", "zh": "我叫...", "level": 1},
            {"en": "¡Muchas gracias!", "zh": "非常感谢！", "level": 1},
            {"en": "¿Puedes ayudarme?", "zh": "你能帮我吗？", "level": 2},
        ], [
            {"title": "主谓结构", "rule": "主语 + 动词 + 宾语", "example": "Yo hablo español.", "level": 1},
            {"title": "否定句", "rule": "主语 + no + 动词", "example": "Yo no hablo inglés.", "level": 2},
        ])

        logger.info("知识库初始化完成")
    
    def _ensure_kb(self, code: str, name: str, voice: str, words: list, sentences: list, grammar: list):
        """确保知识库存在，如果不存在则创建"""
        kb_file = Path(self.config["knowledge_base_dir"]) / f"{code}.json"
        if not kb_file.exists():
            data = {
                "name": name,
                "code": code,
                "voice": voice,
                "words": words,
                "sentences": sentences,
                "grammar": grammar
            }
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"已创建 {name} 知识库")
        else:
            # 检查是否需要合并新词（只添加不存在的，不覆盖）
            with open(kb_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 合并单词
            existing_words = {w["word"] for w in data.get("words", [])}
            for w in words:
                if w["word"] not in existing_words:
                    data["words"].append(w)
            
            # 合并句子
            existing_sentences = {s.get("en", s.get("word", "")) for s in data.get("sentences", [])}
            for s in sentences:
                key = s.get("en", s.get("word", ""))
                if key not in existing_sentences:
                    data["sentences"].append(s)
            
            # 合并语法
            existing_grammar = {g["title"] for g in data.get("grammar", [])}
            for g in grammar:
                if g["title"] not in existing_grammar:
                    data["grammar"].append(g)
            
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ==================== 进度管理 ====================
    
    def _load_progress(self):
        """加载学习进度"""
        progress_file = Path(self.config["progress_file"])
        self.progress = {}
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    self.progress = json.load(f)
            except Exception as e:
                logger.warning(f"加载进度失败: {e}")
        
        for lang in ["en", "ja", "ko", "fr", "de", "es"]:
            if lang not in self.progress:
                self.progress[lang] = {
                    "learned_words": [],
                    "learned_sentences": [],
                    "learned_grammar": [],
                    "stats": {"total_attempts": 0, "correct_answers": 0, "last_study": None}
                }
    
    def _save_progress(self):
        """保存学习进度"""
        progress_file = Path(self.config["progress_file"])
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存进度失败: {e}")
    
    # ==================== 知识库管理方法 ====================
    
    def _get_kb(self, lang: str) -> Dict:
        """获取知识库"""
        kb_file = Path(self.config["knowledge_base_dir"]) / f"{lang}.json"
        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _save_kb(self, lang: str, data: Dict):
        """保存知识库"""
        kb_file = Path(self.config["knowledge_base_dir"]) / f"{lang}.json"
        with open(kb_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _lookup_dictionary(self, word: str, lang: str = "en") -> Dict:
        """查词典"""
        if not REQUESTS_AVAILABLE:
            return {"error": "requests 未安装"}
        
        try:
            url = self.config["dict_api"].format(lang=lang, word=word)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and "meanings" in data[0]:
                    meanings = []
                    for m in data[0]["meanings"]:
                        part = m.get("partOfSpeech", "")
                        definition = m.get("definitions", [{}])[0].get("definition", "")
                        example = m.get("definitions", [{}])[0].get("example", "")
                        if definition:
                            meanings.append({
                                "part": part,
                                "definition": definition,
                                "example": example
                            })
                    return {"status": "success", "word": word, "meanings": meanings}
            return {"status": "error", "message": "未找到释义"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ==================== 学习模式 ====================
    
    def _flashcard_mode(self, lang_code: str, count: int = 10) -> Dict:
        """闪卡模式"""
        kb = self._get_kb(lang_code)
        if not kb:
            return {"error": f"语言 {lang_code} 不存在"}
        
        words = kb.get("words", [])
        learned = self.progress.get(lang_code, {}).get("learned_words", [])
        unlearned = [w for w in words if w["word"] not in learned]
        
        if not unlearned:
            return {"message": "所有单词已学完！", "all_learned": True}
        
        selected = unlearned[:count]
        random.shuffle(selected)
        
        return {
            "mode": "flashcard",
            "language": kb.get("name", lang_code),
            "items": [{"word": item["word"], "meaning": item["meaning"], "example": item.get("example", ""), "level": item.get("level", 1)} for item in selected],
            "total": len(selected),
            "progress": f"{len(learned)}/{len(words)}"
        }
    
    def _quiz_mode(self, lang_code: str, count: int = 5) -> Dict:
        """选择题测验"""
        kb = self._get_kb(lang_code)
        if not kb:
            return {"error": f"语言 {lang_code} 不存在"}
        
        words = kb.get("words", [])
        if len(words) < 4:
            return {"error": "词库太少，需要至少 4 个单词"}
        
        selected = random.sample(words, min(count, len(words)))
        questions = []
        for word in selected:
            others = [w["meaning"] for w in words if w["word"] != word["word"]]
            random.shuffle(others)
            options = [word["meaning"]]
            options.extend(others[:3])
            random.shuffle(options)
            questions.append({"word": word["word"], "correct": word["meaning"], "options": options})
        
        return {"mode": "quiz", "language": kb.get("name", lang_code), "questions": questions, "total": len(questions)}
    
    def _sentence_mode(self, lang_code: str, count: int = 5) -> Dict:
        """句子练习"""
        kb = self._get_kb(lang_code)
        if not kb:
            return {"error": f"语言 {lang_code} 不存在"}
        
        sentences = kb.get("sentences", [])
        if not sentences:
            return {"error": "没有句子"}
        
        selected = random.sample(sentences, min(count, len(sentences)))
        key = "en" if "en" in selected[0] else "word"
        
        return {
            "mode": "sentence",
            "language": kb.get("name", lang_code),
            "items": [{"original": s.get(key, ""), "translation": s.get("zh", ""), "level": s.get("level", 1)} for s in selected],
            "total": len(selected)
        }
    
    def _grammar_mode(self, lang_code: str) -> Dict:
        """语法学习"""
        kb = self._get_kb(lang_code)
        if not kb:
            return {"error": f"语言 {lang_code} 不存在"}
        
        grammar = kb.get("grammar", [])
        if not grammar:
            return {"error": "没有语法"}
        
        learned = self.progress.get(lang_code, {}).get("learned_grammar", [])
        unlearned = [g for g in grammar if g["title"] not in learned]
        selected = [unlearned[0]] if unlearned else [random.choice(grammar)]
        
        return {
            "mode": "grammar",
            "language": kb.get("name", lang_code),
            "items": [{"title": item["title"], "rule": item["rule"], "example": item["example"], "level": item.get("level", 1)} for item in selected],
            "total": len(selected)
        }
    
    def _review_mode(self, lang_code: str, count: int = 5) -> Dict:
        """复习模式"""
        kb = self._get_kb(lang_code)
        if not kb:
            return {"error": f"语言 {lang_code} 不存在"}
        
        words = kb.get("words", [])
        learned = self.progress.get(lang_code, {}).get("learned_words", [])
        learned_words = [w for w in words if w["word"] in learned]
        
        if not learned_words:
            return {"error": "还没有学习任何单词"}
        
        selected = random.sample(learned_words, min(count, len(learned_words)))
        return {
            "mode": "review",
            "language": kb.get("name", lang_code),
            "items": [{"word": item["word"], "meaning": item["meaning"], "example": item.get("example", "")} for item in selected],
            "total": len(selected)
        }
    
    def _speak_text(self, text: str, lang_code: str = None) -> Optional[str]:
        """语音合成"""
        if not EDGE_TTS_AVAILABLE:
            return None
        
        lang_code = lang_code or self.current_lang
        kb = self._get_kb(lang_code)
        if not kb:
            return None
        
        voice = kb.get("voice", "zh-CN-XiaoxiaoNeural")
        output_dir = Path(self.config["output_dir"]) / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = re.sub(r'[^\w\u4e00-\u9fff]', '', text[:20])
        if not filename:
            filename = "speech"
        output_file = output_dir / f"{filename}_{timestamp}.mp3"
        
        try:
            import asyncio
            communicate = edge_tts.Communicate(text, voice)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(communicate.save(str(output_file)))
            return str(output_file)
        except Exception as e:
            logger.error(f"TTS 失败: {e}")
            return None
    
    # ==================== 知识库管理命令 ====================
    
    def _kb_list(self) -> Dict:
        """列出知识库"""
        kb_dir = Path(self.config["knowledge_base_dir"])
        result = {}
        for file in kb_dir.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                result[file.stem] = {
                    "name": data.get("name", file.stem),
                    "words": len(data.get("words", [])),
                    "sentences": len(data.get("sentences", [])),
                    "grammar": len(data.get("grammar", []))
                }
        return result
    
    def _kb_stats(self, lang: str) -> Dict:
        """知识库统计"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        return {
            "language": lang,
            "name": kb.get("name", lang),
            "words": len(kb.get("words", [])),
            "sentences": len(kb.get("sentences", [])),
            "grammar": len(kb.get("grammar", []))
        }
    
    def _kb_add_word(self, lang: str, word: str, meaning: str, example: str = "") -> Dict:
        """添加单词"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        
        existing = {w["word"] for w in kb.get("words", [])}
        if word in existing:
            return {"error": f"单词 '{word}' 已存在"}
        
        kb["words"].append({"word": word, "meaning": meaning, "example": example, "level": 1})
        self._save_kb(lang, kb)
        return {"status": "success", "word": word, "meaning": meaning}
    
    def _kb_add_sentence(self, lang: str, original: str, translation: str) -> Dict:
        """添加句子"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        
        key = "en" if "en" in kb.get("sentences", [{}])[0] else "word"
        existing = {s.get(key) for s in kb.get("sentences", [])}
        if original in existing:
            return {"error": "句子已存在"}
        
        kb["sentences"].append({key: original, "zh": translation, "level": 1})
        self._save_kb(lang, kb)
        return {"status": "success", "original": original, "translation": translation}
    
    def _kb_add_grammar(self, lang: str, title: str, rule: str, example: str) -> Dict:
        """添加语法"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        
        existing = {g["title"] for g in kb.get("grammar", [])}
        if title in existing:
            return {"error": f"语法 '{title}' 已存在"}
        
        kb["grammar"].append({"title": title, "rule": rule, "example": example, "level": 1})
        self._save_kb(lang, kb)
        return {"status": "success", "title": title}
    
    def _kb_import_text(self, lang: str, text: str) -> Dict:
        """从文本批量导入 (每行: word:meaning)"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        
        existing = {w["word"] for w in kb.get("words", [])}
        added = 0
        
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = re.split(r'[:：\-—,，\t]+', line, maxsplit=1)
            if len(parts) == 2:
                word = parts[0].strip()
                meaning = parts[1].strip()
                if word and meaning and word not in existing:
                    kb["words"].append({"word": word, "meaning": meaning, "example": "", "level": 1})
                    existing.add(word)
                    added += 1
        
        if added > 0:
            self._save_kb(lang, kb)
        return {"added": added}
    
    def _kb_import_list(self, lang: str, words: str) -> Dict:
        """从列表批量导入（自动查词典）"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        
        word_list = [w.strip() for w in re.split(r'[,，\s]+', words) if w.strip()]
        existing = {w["word"] for w in kb.get("words", [])}
        added = 0
        failed = []
        
        for word in word_list:
            if word in existing:
                continue
            
            # 查词典
            if REQUESTS_AVAILABLE:
                try:
                    result = self._lookup_dictionary(word, lang)
                    if result.get("status") == "success" and result.get("meanings"):
                        meaning = result["meanings"][0]["definition"][:100]
                        example = result["meanings"][0].get("example", "")[:100]
                        kb["words"].append({"word": word, "meaning": meaning, "example": example, "level": 1})
                        added += 1
                        existing.add(word)
                        continue
                except:
                    pass
            
            # 查不到，添加占位
            kb["words"].append({"word": word, "meaning": "[待补充]", "example": "", "level": 1})
            added += 1
            existing.add(word)
            failed.append(word)
        
        if added > 0:
            self._save_kb(lang, kb)
        return {"added": added, "failed": failed}
    
    def _kb_export(self, lang: str, format: str = "json") -> Dict:
        """导出知识库"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        
        output_dir = Path(self.config["output_dir"]) / "export"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            file_path = output_dir / f"{lang}_{timestamp}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(kb, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            file_path = output_dir / f"{lang}_{timestamp}.csv"
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["word", "meaning", "example", "level"])
                for w in kb.get("words", []):
                    writer.writerow([w.get("word", ""), w.get("meaning", ""), w.get("example", ""), w.get("level", 1)])
        else:
            return {"error": f"不支持的格式: {format}"}
        
        return {"file": str(file_path), "format": format}
    
    def _kb_lookup(self, word: str, lang: str = "en") -> Dict:
        """查词典"""
        result = self._lookup_dictionary(word, lang)
        return result
    
    # ==================== 学习命令 ====================
    
    def _mark_learned(self, lang: str, word: str, item_type: str = "word") -> Dict:
        """标记已学习"""
        if lang not in self.progress:
            return {"error": "语言不存在"}
        
        if item_type == "word" and word not in self.progress[lang]["learned_words"]:
            self.progress[lang]["learned_words"].append(word)
        elif item_type == "sentence" and word not in self.progress[lang]["learned_sentences"]:
            self.progress[lang]["learned_sentences"].append(word)
        elif item_type == "grammar" and word not in self.progress[lang]["learned_grammar"]:
            self.progress[lang]["learned_grammar"].append(word)
        
        self.progress[lang]["stats"]["total_attempts"] += 1
        self.progress[lang]["stats"]["last_study"] = datetime.now().isoformat()
        self._save_progress()
        return {"status": "success"}
    
    def _get_stats(self, lang: str) -> Dict:
        """获取统计"""
        kb = self._get_kb(lang)
        if not kb:
            return {"error": f"语言 {lang} 不存在"}
        
        progress = self.progress.get(lang, {})
        words = kb.get("words", [])
        sentences = kb.get("sentences", [])
        grammar = kb.get("grammar", [])
        
        learned_words = progress.get("learned_words", [])
        learned_sentences = progress.get("learned_sentences", [])
        learned_grammar = progress.get("learned_grammar", [])
        
        return {
            "language": kb.get("name", lang),
            "total_words": len(words),
            "learned_words": len(learned_words),
            "word_progress": f"{len(learned_words)}/{len(words)} ({round(len(learned_words)/max(1,len(words))*100)}%)",
            "total_sentences": len(sentences),
            "learned_sentences": len(learned_sentences),
            "total_grammar": len(grammar),
            "learned_grammar": len(learned_grammar),
            "stats": progress.get("stats", {})
        }


    def _kb_download_full_dict(self, lang: str, source: str = "auto") -> Dict:
        """下载完整词典到知识库（支持多语言）"""
        from pathlib import Path
        # 获取语言对应的词典源
        dict_sources = self.config.get("dict_sources", {})
        
        if source == "auto":
            # 自动选择
            if lang in dict_sources:
                source = dict_sources[lang].get("source", "wordnet")
            else:
                source = "wordnet"
        
        # ===== 英语 WordNet =====
        if source == "wordnet" and lang in ["en", "fr", "de", "es"]:
            try:
                import nltk
                
                # 设置下载目录
                download_dir = str(Path(self.config["knowledge_base_dir"]))
                nltk_data_dir = Path(download_dir) / "nltk_data"
                nltk_data_dir.mkdir(parents=True, exist_ok=True)
                
                nltk.data.path = [str(nltk_data_dir)] + nltk.data.path
                
                # 下载 WordNet
                try:
                    nltk.data.find('corpora/wordnet')
                    print(f"✅ WordNet 已存在 (语言: {lang})")
                except LookupError:
                    print(f"📥 正在下载 WordNet 词典 (语言: {lang})...")
                    nltk.download('wordnet', quiet=False, download_dir=str(nltk_data_dir))
                
                from nltk.corpus import wordnet as wn
                
                kb = self._get_kb(lang)
                if not kb:
                    return {"error": f"语言 {lang} 不存在"}
                
                existing = {w["word"] for w in kb.get("words", [])}
                added = 0
                
                print(f"📖 正在导入 WordNet 词典到 {lang} 知识库...")
                
                for synset in wn.all_synsets():
                    # 获取词条
                    word = synset.lemmas()[0].name().replace('_', ' ')
                    if word in existing or len(word) < 2:
                        continue
                    
                    definition = synset.definition()
                    examples = synset.examples()
                    example = examples[0] if examples else ""
                    
                    kb["words"].append({
                        "word": word,
                        "meaning": definition[:150],
                        "example": example[:100] if example else "",
                        "level": 1
                    })
                    existing.add(word)
                    added += 1
                    
                    if added % 1000 == 0:
                        print(f"   ✅ 已导入 {added} 个单词...")
                
                if added > 0:
                    self._save_kb(lang, kb)
                
                print(f"\n🎉 导入完成！共导入 {added} 个单词")
                print(f"📁 知识库文件: {self.config['knowledge_base_dir']}/{lang}.json")
                
                return {"added": added, "source": "WordNet", "language": lang}
                
            except ImportError:
                return {"error": "请安装 nltk: pip install nltk"}
            except Exception as e:
                return {"error": str(e)}


        # ===== 日语 Jamdict - 数据保存在 knowledge/jamdict_data/ =====
        elif source == "jamdict" and lang == "ja":
            try:
                import jamdict
                from jamdict import Jamdict
                import os
                from pathlib import Path
                import urllib.request
                import gzip
                import xml.etree.ElementTree as ET
                
                print("📥 正在加载 Jamdict 日语词典...")
                
                # 1. 数据目录：knowledge/jamdict_data/data/
                knowledge_dir = Path(self.config["knowledge_base_dir"])
                jamdict_data_dir = knowledge_dir / "jamdict_data" / "data"
                jamdict_data_dir.mkdir(parents=True, exist_ok=True)
                
                # 2. 检查并下载 JMdict_e.gz
                jmdict_file = jamdict_data_dir / "JMdict_e.gz"
                if not jmdict_file.exists():
                    print("📥 正在下载 JMdict_e.gz（约10MB，请耐心等待）...")
                    url = "http://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz"
                    urllib.request.urlretrieve(url, str(jmdict_file))
                    print("✅ 下载完成")
                else:
                    print("✅ JMdict_e.gz 已存在")
                
                # 3. 获取知识库
                kb = self._get_kb(lang)
                if not kb:
                    return {"error": f"语言 {lang} 不存在"}
                
                existing = {w["word"] for w in kb.get("words", [])}
                added = 0
                
                print(f"📖 正在解析 JMdict 并导入日语词汇到知识库...")
                
                # 4. 解析 XML 文件，直接导入到知识库（绕过 jamdict 数据库）
                with gzip.open(jmdict_file, 'rb') as f:
                    tree = ET.parse(f)
                root = tree.getroot()
                
                # 移除命名空间
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]
                
                for entry in root.findall('entry'):
                    # 获取词汇
                    word = None
                    orth_elem = entry.find('.//orth')
                    if orth_elem is not None and orth_elem.text:
                        word = orth_elem.text
                    else:
                        keb_elem = entry.find('.//keb')
                        if keb_elem is not None and keb_elem.text:
                            word = keb_elem.text
                    
                    if not word or len(word) < 2 or len(word) > 20:
                        continue
                    
                    if word in existing:
                        continue
                    
                    # 获取释义
                    meanings = []
                    for sense in entry.findall('.//sense'):
                        for gloss in sense.findall('.//gloss'):
                            if gloss.text:
                                # 只取英文释义
                                if gloss.get('xml:lang') in [None, 'eng']:
                                    meanings.append(gloss.text)
                        if len(meanings) >= 3:
                            break
                    
                    if not meanings:
                        # 没有英文释义，跳过
                        continue
                    
                    meaning = '；'.join(meanings[:3])
                    if len(meaning) > 150:
                        meaning = meaning[:147] + "..."
                    
                    kb["words"].append({
                        "word": word,
                        "meaning": meaning,
                        "example": "",
                        "level": 1
                    })
                    existing.add(word)
                    added += 1
                    
                    if added % 500 == 0:
                        print(f"   ✅ 已导入 {added} 个日语词...")
                    
                    # 限制数量，避免太多
                    if added >= 15000:
                        break
                
                # 5. 保存知识库
                if added > 0:
                    self._save_kb(lang, kb)
                    print(f"\n🎉 导入完成！共导入 {added} 个日语词")
                else:
                    print("\n⚠️ 没有导入任何新词（可能已全部存在）")
                
                print(f"📁 知识库文件: {knowledge_dir}/{lang}.json")
                print(f"📁 Jamdict 数据目录: {jamdict_data_dir}")
                
                return {"added": added, "source": "Jamdict (XML)", "language": lang}
                
            except ImportError:
                return {"error": "请安装 jamdict: pip install jamdict"}
            except Exception as e:
                return {"error": str(e)}
        
        # ===== 中文词典（使用 CEDICT + Jieba） =====
        elif source == "jieba" and lang == "zh":
            try:
                import jieba
                import urllib.request
                import json
                from pathlib import Path
                
                print("📥 正在加载中文词典...")
                
                # 1. 在 knowledge 目录下创建中文数据目录
                knowledge_dir = Path(self.config["knowledge_base_dir"])
                chinese_data_dir = knowledge_dir / "chinese_data"
                chinese_data_dir.mkdir(parents=True, exist_ok=True)
                
                # 2. 下载 CEDICT 中文词典（使用有效源）
                cedict_file = chinese_data_dir / "cedict_ts.u8"
                if not cedict_file.exists():
                    print("📥 正在下载 CEDICT 中文词典（包含释义）...")
                    
                    # 有效的下载源列表
                    urls = [
                        "https://raw.githubusercontent.com/lingua-dict/cedict/master/cedict_ts.u8",
                        "https://cdn.jsdelivr.net/gh/lingua-dict/cedict/cedict_ts.u8",
                        "https://gitlab.com/lingua-dict/cedict/-/raw/master/cedict_ts.u8",
                    ]
                    
                    downloaded = False
                    for url in urls:
                        try:
                            print(f"  尝试从 {url} 下载...")
                            urllib.request.urlretrieve(url, str(cedict_file))
                            print(f"✅ CEDICT 下载完成")
                            downloaded = True
                            break
                        except Exception as e:
                            print(f"  ❌ 下载失败: {e}")
                            continue
                    
                    if not downloaded:
                        print("⚠️ 所有 CEDICT 源都下载失败，将使用 Jieba 内置词库")
                else:
                    print("✅ CEDICT 已存在")
                
                # 3. 获取知识库（如果不存在则创建）
                kb = self._get_kb(lang)
                if not kb:
                    # 创建中文知识库
                    kb = {
                        "name": "中文",
                        "code": "zh",
                        "voice": "zh-CN-XiaoxiaoNeural",
                        "words": [],
                        "sentences": [],
                        "grammar": []
                    }
                    self._save_kb(lang, kb)
                
                existing = {w["word"] for w in kb.get("words", [])}
                added = 0
                
                print(f"📖 正在导入中文词汇到知识库...")
                
                # 4. 从 CEDICT 导入
                if cedict_file.exists():
                    try:
                        with open(cedict_file, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.startswith('#') or not line.strip():
                                    continue
                                
                                # 解析 CEDICT 格式
                                line = line.strip()
                                # 格式: 繁体 简体 [拼音] /释义1/释义2/
                                if '[' not in line:
                                    continue
                                
                                # 提取简体字和释义
                                try:
                                    # 提取简体字
                                    trad_simp = line.split('[')[0].strip()
                                    parts = trad_simp.split()
                                    if len(parts) >= 2:
                                        simplified = parts[1]
                                    elif len(parts) == 1:
                                        simplified = parts[0]
                                    else:
                                        continue
                                    
                                    # 提取释义（在 / / 之间）
                                    meaning_start = line.find('/')
                                    if meaning_start == -1:
                                        continue
                                    
                                    meaning_text = line[meaning_start:]
                                    # 提取所有 /释义/
                                    meanings = []
                                    import re
                                    pattern = r'/([^/]+)/'
                                    matches = re.findall(pattern, meaning_text)
                                    for m in matches[:5]:
                                        if m.strip():
                                            meanings.append(m.strip())
                                    
                                    if not meanings:
                                        continue
                                    
                                    meaning = '；'.join(meanings[:3])
                                    if len(meaning) > 150:
                                        meaning = meaning[:147] + "..."
                                    
                                    # 只导入中文词（长度2-6）
                                    if simplified and len(simplified) >= 2 and len(simplified) <= 6:
                                        if simplified not in existing:
                                            kb["words"].append({
                                                "word": simplified,
                                                "meaning": meaning,
                                                "example": "",
                                                "level": 1
                                            })
                                            existing.add(simplified)
                                            added += 1
                                            
                                            if added % 1000 == 0:
                                                print(f"   ✅ 已导入 {added} 个中文词...")
                                            
                                            if added >= 20000:
                                                break
                                except:
                                    continue
                    except Exception as e:
                        print(f"⚠️ 解析 CEDICT 时出错: {e}")
                
                # 5. 如果 CEDICT 导入太少，补充 Jieba 词库
                if added < 100:
                    print("📥 从 Jieba 内置词库补充导入...")
                    try:
                        dict_path = Path(jieba.__file__).parent / "dict.txt"
                        if dict_path.exists():
                            with open(dict_path, 'r', encoding='utf-8') as f:
                                for line in f:
                                    parts = line.strip().split()
                                    if len(parts) >= 1:
                                        word = parts[0]
                                        if word and word not in existing and len(word) >= 2:
                                            # 只保留中文字符
                                            if all('\u4e00' <= c <= '\u9fff' for c in word):
                                                kb["words"].append({
                                                    "word": word,
                                                    "meaning": "[中文词]",
                                                    "example": "",
                                                    "level": 1
                                                })
                                                existing.add(word)
                                                added += 1
                                                if added % 1000 == 0:
                                                    print(f"   ✅ 已导入 {added} 个中文词...")
                                                if added >= 10000:
                                                    break
                    except Exception as e:
                        print(f"⚠️ 读取 Jieba 词库失败: {e}")
                
                # 6. 保存知识库
                if added > 0:
                    self._save_kb(lang, kb)
                    print(f"\n🎉 导入完成！共导入 {added} 个中文词")
                else:
                    print("\n⚠️ 没有导入任何新词（可能已全部存在）")
                
                print(f"📁 知识库文件: {self.config['knowledge_base_dir']}/{lang}.json")
                print(f"📁 中文数据目录: {chinese_data_dir}")
                
                return {"added": added, "source": "CEDICT + Jieba", "language": lang}
                
            except ImportError:
                return {"error": "请安装 jieba: pip install jieba"}
            except Exception as e:
                return {"error": str(e)}  


        # ===== 韩语（使用 Konlpy + 扩展词库） =====
        elif source == "korean" and lang == "ko":
            try:
                import urllib.request
                import json
                from pathlib import Path
                
                print("📥 正在加载韩语词典...")
                
                # 1. 在 knowledge 目录下创建韩语数据目录
                knowledge_dir = Path(self.config["knowledge_base_dir"])
                korean_data_dir = knowledge_dir / "korean_data"
                korean_data_dir.mkdir(parents=True, exist_ok=True)
                
                # 2. 下载韩语词库（从 KRDict 或开源词库）
                korean_dict_file = korean_data_dir / "korean_words.json"
                
                if not korean_dict_file.exists():
                    print("📥 正在下载韩语词库（包含释义）...")
                    try:
                        # 使用开源韩语词典 API（KRDict 的镜像）
                        url = "https://raw.githubusercontent.com/korean-word-game/korean-dictionary/master/data/words.json"
                        urllib.request.urlretrieve(url, str(korean_dict_file))
                        print("✅ 韩语词库下载完成")
                    except Exception as e:
                        print(f"⚠️ 下载失败: {e}")
                        # 如果下载失败，使用内置扩展词库（见下方）
                        print("📥 使用内置韩语扩展词库...")
                        # 创建内置词库文件
                        fallback_words = [
                            # 问候语
                            {"word": "안녕하세요", "meaning": "你好"},
                            {"word": "감사합니다", "meaning": "谢谢"},
                            {"word": "죄송합니다", "meaning": "对不起"},
                            {"word": "반갑습니다", "meaning": "很高兴见到你"},
                            {"word": "잘 부탁드립니다", "meaning": "请多关照"},
                            {"word": "네", "meaning": "是的"},
                            {"word": "아니요", "meaning": "不是"},
                            {"word": "어떻게 지내세요?", "meaning": "你好吗？"},
                            # 人称
                            {"word": "저", "meaning": "我（正式）"},
                            {"word": "나", "meaning": "我（非正式）"},
                            {"word": "당신", "meaning": "你"},
                            {"word": "그", "meaning": "他"},
                            {"word": "그녀", "meaning": "她"},
                            {"word": "우리", "meaning": "我们"},
                            {"word": "여러분", "meaning": "各位、大家"},
                            # 家庭成员
                            {"word": "가족", "meaning": "家庭"},
                            {"word": "아버지", "meaning": "父亲"},
                            {"word": "어머니", "meaning": "母亲"},
                            {"word": "형", "meaning": "哥哥（男用）"},
                            {"word": "오빠", "meaning": "哥哥（女用）"},
                            {"word": "누나", "meaning": "姐姐（男用）"},
                            {"word": "언니", "meaning": "姐姐（女用）"},
                            {"word": "동생", "meaning": "弟弟/妹妹"},
                            {"word": "아들", "meaning": "儿子"},
                            {"word": "딸", "meaning": "女儿"},
                            # 食物
                            {"word": "김치", "meaning": "泡菜"},
                            {"word": "비빔밥", "meaning": "拌饭"},
                            {"word": "불고기", "meaning": "烤肉"},
                            {"word": "떡볶이", "meaning": "炒年糕"},
                            {"word": "삼겹살", "meaning": "五花肉"},
                            {"word": "김밥", "meaning": "紫菜包饭"},
                            {"word": "라면", "meaning": "拉面"},
                            {"word": "짜장면", "meaning": "炸酱面"},
                            {"word": "탕수육", "meaning": "糖醋肉"},
                            {"word": "막걸리", "meaning": "米酒"},
                            # 日常用品
                            {"word": "학교", "meaning": "学校"},
                            {"word": "선생님", "meaning": "老师"},
                            {"word": "학생", "meaning": "学生"},
                            {"word": "책", "meaning": "书"},
                            {"word": "가방", "meaning": "包"},
                            {"word": "휴대폰", "meaning": "手机"},
                            {"word": "컴퓨터", "meaning": "电脑"},
                            {"word": "의자", "meaning": "椅子"},
                            {"word": "책상", "meaning": "桌子"},
                            {"word": "침대", "meaning": "床"},
                            # 颜色
                            {"word": "빨간색", "meaning": "红色"},
                            {"word": "파란색", "meaning": "蓝色"},
                            {"word": "초록색", "meaning": "绿色"},
                            {"word": "노란색", "meaning": "黄色"},
                            {"word": "검은색", "meaning": "黑色"},
                            {"word": "흰색", "meaning": "白色"},
                            {"word": "분홍색", "meaning": "粉色"},
                            {"word": "보라색", "meaning": "紫色"},
                            {"word": "갈색", "meaning": "棕色"},
                            {"word": "주황색", "meaning": "橙色"},
                            # 感情
                            {"word": "사랑", "meaning": "爱"},
                            {"word": "행복", "meaning": "幸福"},
                            {"word": "슬픔", "meaning": "悲伤"},
                            {"word": "기쁨", "meaning": "喜悦"},
                            {"word": "화", "meaning": "愤怒"},
                            {"word": "두려움", "meaning": "恐惧"},
                            {"word": "놀람", "meaning": "惊讶"},
                            {"word": "편안함", "meaning": "舒适"},
                            # 动作
                            {"word": "가다", "meaning": "去"},
                            {"word": "오다", "meaning": "来"},
                            {"word": "보다", "meaning": "看"},
                            {"word": "듣다", "meaning": "听"},
                            {"word": "말하다", "meaning": "说"},
                            {"word": "읽다", "meaning": "读"},
                            {"word": "쓰다", "meaning": "写"},
                            {"word": "먹다", "meaning": "吃"},
                            {"word": "마시다", "meaning": "喝"},
                            {"word": "자다", "meaning": "睡"},
                            {"word": "일어나다", "meaning": "起床"},
                            {"word": "걷다", "meaning": "走"},
                            {"word": "뛰다", "meaning": "跑"},
                            {"word": "공부하다", "meaning": "学习"},
                            {"word": "일하다", "meaning": "工作"},
                            # 时间
                            {"word": "오늘", "meaning": "今天"},
                            {"word": "내일", "meaning": "明天"},
                            {"word": "어제", "meaning": "昨天"},
                            {"word": "시간", "meaning": "时间"},
                            {"word": "아침", "meaning": "早上"},
                            {"word": "점심", "meaning": "中午"},
                            {"word": "저녁", "meaning": "晚上"},
                            {"word": "밤", "meaning": "夜晚"},
                            {"word": "주말", "meaning": "周末"},
                            {"word": "월요일", "meaning": "星期一"},
                            {"word": "화요일", "meaning": "星期二"},
                            {"word": "수요일", "meaning": "星期三"},
                            {"word": "목요일", "meaning": "星期四"},
                            {"word": "금요일", "meaning": "星期五"},
                            {"word": "토요일", "meaning": "星期六"},
                            {"word": "일요일", "meaning": "星期日"},
                            # 地方
                            {"word": "서울", "meaning": "首尔"},
                            {"word": "부산", "meaning": "釜山"},
                            {"word": "인천", "meaning": "仁川"},
                            {"word": "대구", "meaning": "大邱"},
                            {"word": "광주", "meaning": "光州"},
                            {"word": "대전", "meaning": "大田"},
                            {"word": "울산", "meaning": "蔚山"},
                            # 其他常用词
                            {"word": "한국", "meaning": "韩国"},
                            {"word": "한국어", "meaning": "韩语"},
                            {"word": "영어", "meaning": "英语"},
                            {"word": "중국어", "meaning": "中文"},
                            {"word": "일본어", "meaning": "日语"},
                            {"word": "친구", "meaning": "朋友"},
                            {"word": "이름", "meaning": "名字"},
                            {"word": "나라", "meaning": "国家"},
                            {"word": "도시", "meaning": "城市"},
                            {"word": "사람", "meaning": "人"},
                            {"word": "남자", "meaning": "男人"},
                            {"word": "여자", "meaning": "女人"},
                            {"word": "아이", "meaning": "孩子"},
                            {"word": "어른", "meaning": "成年人"},
                            {"word": "선물", "meaning": "礼物"},
                            {"word": "여행", "meaning": "旅行"},
                            {"word": "음악", "meaning": "音乐"},
                            {"word": "영화", "meaning": "电影"},
                            {"word": "사진", "meaning": "照片"},
                            {"word": "운동", "meaning": "运动"},
                            {"word": "요리", "meaning": "料理"},
                            {"word": "쇼핑", "meaning": "购物"},
                            {"word": "날씨", "meaning": "天气"},
                            {"word": "계절", "meaning": "季节"},
                            {"word": "봄", "meaning": "春天"},
                            {"word": "여름", "meaning": "夏天"},
                            {"word": "가을", "meaning": "秋天"},
                            {"word": "겨울", "meaning": "冬天"},
                        ]
                        
                        # 保存内置词库
                        with open(korean_dict_file, 'w', encoding='utf-8') as f:
                            json.dump(fallback_words, f, ensure_ascii=False, indent=2)
                        print(f"✅ 内置韩语词库已保存（{len(fallback_words)} 个词）")
                        
                    except Exception as e:
                        print(f"❌ 词库创建失败: {e}")
                        return {"error": f"韩语词库初始化失败: {e}"}
                
                # 3. 读取词库
                with open(korean_dict_file, 'r', encoding='utf-8') as f:
                    word_list = json.load(f)
                
                # 4. 获取知识库
                kb = self._get_kb(lang)
                if not kb:
                    return {"error": f"语言 {lang} 不存在"}
                
                existing = {w["word"] for w in kb.get("words", [])}
                added = 0
                
                print(f"📖 正在导入韩语词汇到知识库...")
                
                for word_data in word_list:
                    word = word_data.get("word", "")
                    meaning = word_data.get("meaning", "")
                    example = word_data.get("example", "")
                    
                    if not word or not meaning:
                        continue
                    
                    if word in existing:
                        continue
                    
                    kb["words"].append({
                        "word": word,
                        "meaning": meaning,
                        "example": example,
                        "level": 1
                    })
                    existing.add(word)
                    added += 1
                    
                    if added % 100 == 0:
                        print(f"   ✅ 已导入 {added} 个韩语词...")
                
                if added > 0:
                    self._save_kb(lang, kb)
                    print(f"\n🎉 导入完成！共导入 {added} 个韩语词")
                else:
                    print("\n⚠️ 没有导入任何新词（可能已全部存在）")
                
                print(f"📁 知识库文件: {self.config['knowledge_base_dir']}/{lang}.json")
                print(f"📁 韩语数据目录: {korean_data_dir}")
                
                return {"added": added, "source": "Korean Dictionary", "language": lang}
                
            except Exception as e:
                return {"error": str(e)}
        

        # ===== 法语（使用 WordNet + 扩展词库） =====
        elif source == "wordnet" and lang == "fr":
            try:
                import nltk
                from pathlib import Path
                
                print("📥 正在加载法语词典...")
                
                # 1. 设置 NLTK 数据目录
                knowledge_dir = Path(self.config["knowledge_base_dir"])
                nltk_data_dir = knowledge_dir / "nltk_data"
                nltk_data_dir.mkdir(parents=True, exist_ok=True)
                
                nltk.data.path = [str(nltk_data_dir)] + nltk.data.path
                
                # 2. 下载 WordNet
                for corpus in ['wordnet', 'omw-1.4']:
                    try:
                        nltk.data.find(f'corpora/{corpus}')
                        print(f"✅ {corpus} 已存在")
                    except LookupError:
                        print(f"📥 正在下载 {corpus}...")
                        nltk.download(corpus, quiet=True, download_dir=str(nltk_data_dir))
                        print(f"✅ {corpus} 下载完成")
                
                # 3. 获取知识库
                kb = self._get_kb(lang)
                if not kb:
                    return {"error": f"语言 {lang} 不存在"}
                
                existing = {w["word"] for w in kb.get("words", [])}
                added = 0
                
                print(f"📖 正在导入法语词汇到知识库...")
                
                # 法语常用词汇
                french_words = [
                    ("bonjour", "你好"),
                    ("merci", "谢谢"),
                    ("au revoir", "再见"),
                    ("oui", "是的"),
                    ("non", "不是"),
                    ("s'il vous plaît", "请"),
                    ("pardon", "对不起"),
                    ("monsieur", "先生"),
                    ("madame", "女士"),
                    ("mademoiselle", "小姐"),
                    ("amour", "爱"),
                    ("ami", "朋友"),
                    ("famille", "家庭"),
                    ("école", "学校"),
                    ("étudiant", "学生"),
                    ("professeur", "老师"),
                    ("livre", "书"),
                    ("maison", "房子"),
                    ("ville", "城市"),
                    ("pays", "国家"),
                    ("paris", "巴黎"),
                    ("français", "法语"),
                    ("anglais", "英语"),
                    ("chinois", "中文"),
                    ("japonais", "日语"),
                    ("musique", "音乐"),
                    ("film", "电影"),
                    ("photo", "照片"),
                    ("art", "艺术"),
                    ("culture", "文化"),
                    ("sport", "运动"),
                    ("cuisine", "美食"),
                    ("voyage", "旅行"),
                    ("jardin", "花园"),
                    ("fleur", "花"),
                    ("arbre", "树"),
                    ("montagne", "山"),
                    ("mer", "海"),
                    ("soleil", "太阳"),
                    ("lune", "月亮"),
                    ("étoile", "星星"),
                    ("bon", "好的"),
                    ("mauvais", "坏的"),
                    ("grand", "大的"),
                    ("petit", "小的"),
                    ("beau", "美丽的"),
                    ("laid", "丑陋的"),
                    ("heureux", "幸福的"),
                    ("triste", "悲伤的"),
                    ("fatigué", "累的"),
                    ("faim", "饿"),
                    ("soif", "渴"),
                    ("aller", "去"),
                    ("venir", "来"),
                    ("voir", "看"),
                    ("écouter", "听"),
                    ("parler", "说"),
                    ("lire", "阅读"),
                    ("écrire", "写"),
                    ("manger", "吃"),
                    ("boire", "喝"),
                    ("dormir", "睡觉"),
                    ("réveiller", "起床"),
                    ("marcher", "走路"),
                    ("courir", "跑"),
                    ("voler", "飞"),
                    ("nager", "游泳"),
                    ("chanter", "唱歌"),
                    ("danser", "跳舞"),
                    ("jouer", "玩耍"),
                    ("travailler", "工作"),
                    ("étudier", "学习"),
                    ("aimer", "喜欢"),
                    ("détester", "讨厌"),
                    ("vouloir", "想要"),
                    ("pouvoir", "能够"),
                    ("devoir", "应该"),
                    ("savoir", "知道"),
                    ("penser", "思考"),
                    ("croire", "相信"),
                    ("espérer", "希望"),
                    ("vivre", "生活"),
                    ("mourir", "死亡"),
                    ("naissance", "出生"),
                    ("vie", "生命"),
                    ("mort", "死亡"),
                    ("temps", "时间"),
                    ("jour", "天"),
                    ("nuit", "夜"),
                    ("semaine", "周"),
                    ("mois", "月"),
                    ("année", "年"),
                    ("printemps", "春天"),
                    ("été", "夏天"),
                    ("automne", "秋天"),
                    ("hiver", "冬天"),
                    ("lundi", "星期一"),
                    ("mardi", "星期二"),
                    ("mercredi", "星期三"),
                    ("jeudi", "星期四"),
                    ("vendredi", "星期五"),
                    ("samedi", "星期六"),
                    ("dimanche", "星期天"),
                ]
                
                for word, meaning in french_words:
                    if word in existing:
                        continue
                    
                    kb["words"].append({
                        "word": word,
                        "meaning": meaning,
                        "example": "",
                        "level": 1
                    })
                    existing.add(word)
                    added += 1
                    
                    if added % 50 == 0:
                        print(f"   ✅ 已导入 {added} 个法语词...")
                
                if added > 0:
                    self._save_kb(lang, kb)
                    print(f"\n🎉 导入完成！共导入 {added} 个法语词")
                else:
                    print("\n⚠️ 没有导入任何新词（可能已全部存在）")
                
                print(f"📁 知识库文件: {self.config['knowledge_base_dir']}/{lang}.json")
                
                return {"added": added, "source": "WordNet (OMW)", "language": lang}
                
            except ImportError:
                return {"error": "请安装 nltk: pip install nltk"}
            except Exception as e:
                return {"error": str(e)}

        # ===== 德语（使用 WordNet + 扩展词库） =====
        elif source == "wordnet" and lang == "de":
            try:
                import nltk
                from pathlib import Path                
                
                print("📥 正在加载德语词典...")
                
                # 1. 设置 NLTK 数据目录
                knowledge_dir = Path(self.config["knowledge_base_dir"])
                nltk_data_dir = knowledge_dir / "nltk_data"
                nltk_data_dir.mkdir(parents=True, exist_ok=True)
                
                nltk.data.path = [str(nltk_data_dir)] + nltk.data.path
                
                # 2. 下载 WordNet
                for corpus in ['wordnet', 'omw-1.4']:
                    try:
                        nltk.data.find(f'corpora/{corpus}')
                        print(f"✅ {corpus} 已存在")
                    except LookupError:
                        print(f"📥 正在下载 {corpus}...")
                        nltk.download(corpus, quiet=True, download_dir=str(nltk_data_dir))
                        print(f"✅ {corpus} 下载完成")
                
                # 3. 获取知识库
                kb = self._get_kb(lang)
                if not kb:
                    return {"error": f"语言 {lang} 不存在"}
                
                existing = {w["word"] for w in kb.get("words", [])}
                added = 0
                
                print(f"📖 正在导入德语词汇到知识库...")
                
                # 德语常用词汇
                german_words = [
                    # 问候语
                    ("Hallo", "你好"),
                    ("Guten Tag", "你好（白天）"),
                    ("Guten Morgen", "早上好"),
                    ("Guten Abend", "晚上好"),
                    ("Gute Nacht", "晚安"),
                    ("Auf Wiedersehen", "再见"),
                    ("Tschüss", "再见（非正式）"),
                    ("Danke", "谢谢"),
                    ("Danke schön", "非常感谢"),
                    ("Bitte", "请/不客气"),
                    ("Entschuldigung", "对不起"),
                    ("Ja", "是的"),
                    ("Nein", "不是"),
                    ("Herr", "先生"),
                    ("Frau", "女士"),
                    ("Fräulein", "小姐"),
                    # 家庭
                    ("Familie", "家庭"),
                    ("Vater", "父亲"),
                    ("Mutter", "母亲"),
                    ("Bruder", "兄弟"),
                    ("Schwester", "姐妹"),
                    ("Sohn", "儿子"),
                    ("Tochter", "女儿"),
                    ("Onkel", "叔叔"),
                    ("Tante", "阿姨"),
                    ("Großvater", "祖父"),
                    ("Großmutter", "祖母"),
                    # 学校
                    ("Schule", "学校"),
                    ("Lehrer", "老师"),
                    ("Schüler", "学生"),
                    ("Buch", "书"),
                    ("Klasse", "班级"),
                    ("Universität", "大学"),
                    ("Student", "大学生"),
                    ("Prüfung", "考试"),
                    ("Hausaufgabe", "作业"),
                    # 食物
                    ("Essen", "食物"),
                    ("Trinken", "饮料"),
                    ("Brot", "面包"),
                    ("Wasser", "水"),
                    ("Bier", "啤酒"),
                    ("Wein", "葡萄酒"),
                    ("Kaffee", "咖啡"),
                    ("Tee", "茶"),
                    ("Milch", "牛奶"),
                    ("Fleisch", "肉"),
                    ("Fisch", "鱼"),
                    ("Gemüse", "蔬菜"),
                    ("Obst", "水果"),
                    ("Kuchen", "蛋糕"),
                    ("Schokolade", "巧克力"),
                    # 自然
                    ("Natur", "自然"),
                    ("Blume", "花"),
                    ("Baum", "树"),
                    ("Berg", "山"),
                    ("Meer", "海"),
                    ("Himmel", "天空"),
                    ("Sonne", "太阳"),
                    ("Mond", "月亮"),
                    ("Stern", "星星"),
                    ("Regen", "雨"),
                    ("Schnee", "雪"),
                    ("Wind", "风"),
                    ("Wald", "森林"),
                    ("See", "湖"),
                    ("Insel", "岛"),
                    # 感情
                    ("Liebe", "爱"),
                    ("Glück", "幸福"),
                    ("Traurigkeit", "悲伤"),
                    ("Freude", "喜悦"),
                    ("Angst", "恐惧"),
                    ("Überraschung", "惊讶"),
                    ("Ruhe", "平静"),
                    ("Zufriedenheit", "满足"),
                    # 动作
                    ("gehen", "去/走"),
                    ("kommen", "来"),
                    ("sehen", "看"),
                    ("hören", "听"),
                    ("sprechen", "说"),
                    ("lesen", "阅读"),
                    ("schreiben", "写"),
                    ("essen", "吃"),
                    ("trinken", "喝"),
                    ("schlafen", "睡觉"),
                    ("aufwachen", "起床"),
                    ("laufen", "跑"),
                    ("schwimmen", "游泳"),
                    ("singen", "唱歌"),
                    ("tanzen", "跳舞"),
                    ("spielen", "玩耍"),
                    ("arbeiten", "工作"),
                    ("lernen", "学习"),
                    ("lieben", "爱"),
                    ("hassen", "恨"),
                    # 时间
                    ("Zeit", "时间"),
                    ("Tag", "天"),
                    ("Nacht", "夜晚"),
                    ("Woche", "周"),
                    ("Monat", "月"),
                    ("Jahr", "年"),
                    ("Frühling", "春天"),
                    ("Sommer", "夏天"),
                    ("Herbst", "秋天"),
                    ("Winter", "冬天"),
                    ("Montag", "星期一"),
                    ("Dienstag", "星期二"),
                    ("Mittwoch", "星期三"),
                    ("Donnerstag", "星期四"),
                    ("Freitag", "星期五"),
                    ("Samstag", "星期六"),
                    ("Sonntag", "星期天"),
                    # 其他常用
                    ("Deutschland", "德国"),
                    ("Berlin", "柏林"),
                    ("München", "慕尼黑"),
                    ("Hamburg", "汉堡"),
                    ("Köln", "科隆"),
                    ("Deutsch", "德语"),
                    ("Englisch", "英语"),
                    ("Chinesisch", "中文"),
                    ("Japanisch", "日语"),
                    ("Musik", "音乐"),
                    ("Film", "电影"),
                    ("Kunst", "艺术"),
                    ("Kultur", "文化"),
                    ("Sport", "运动"),
                    ("Reisen", "旅行"),
                    ("Stadt", "城市"),
                    ("Land", "国家"),
                    ("Mensch", "人"),
                    ("Freund", "朋友"),
                    ("Geschenk", "礼物"),
                    ("Wetter", "天气"),
                    ("Jahreszeit", "季节"),
                ]
                
                for word, meaning in german_words:
                    if word in existing:
                        continue
                    
                    kb["words"].append({
                        "word": word,
                        "meaning": meaning,
                        "example": "",
                        "level": 1
                    })
                    existing.add(word)
                    added += 1
                    
                    if added % 50 == 0:
                        print(f"   ✅ 已导入 {added} 个德语词...")
                
                if added > 0:
                    self._save_kb(lang, kb)
                    print(f"\n🎉 导入完成！共导入 {added} 个德语词")
                else:
                    print("\n⚠️ 没有导入任何新词（可能已全部存在）")
                
                print(f"📁 知识库文件: {self.config['knowledge_base_dir']}/{lang}.json")
                
                return {"added": added, "source": "WordNet (OMW)", "language": lang}
                
            except ImportError:
                return {"error": "请安装 nltk: pip install nltk"}
            except Exception as e:
                return {"error": str(e)}

        
        return {"error": f"不支持的语言: {lang} 或词典源: {source}"}
    
    # ==================== 执行入口 ====================
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行操作"""
        start_time = time.time()
        logger.info(f"执行技能: {self.name} (v{self.version})")
        
        try:
            action = kwargs.get("action", "")
            lang = kwargs.get("language", self.current_lang)
            count = kwargs.get("count", 10)
            
            result = {}
            need_print = True
            
            # ===== 学习模式 =====
            if action == "list":
                result = self._kb_list()
                self._print_list(result)
            
            elif action == "set_language":
                kb = self._get_kb(lang)
                if kb:
                    self.current_lang = lang
                    result = {"status": "success", "language": lang, "name": kb.get("name", lang)}
                    print(f"✅ 已切换到: {kb.get('name', lang)}")
                else:
                    result = {"error": f"语言 {lang} 不存在"}
                    print(f"❌ 语言 {lang} 不存在")
            
            elif action == "flashcard":
                result = self._flashcard_mode(lang, count)
                self._print_flashcard(result)
            
            elif action == "quiz":
                result = self._quiz_mode(lang, count)
                self._print_quiz(result)
            
            elif action == "sentence":
                result = self._sentence_mode(lang, count)
                self._print_sentence(result)
            
            elif action == "grammar":
                result = self._grammar_mode(lang)
                self._print_grammar(result)
            
            elif action == "review":
                result = self._review_mode(lang, count)
                self._print_review(result)
            
            elif action == "speak":
                text = kwargs.get("text", "")
                if not text:
                    return {"status": "error", "error": "请提供 text 参数"}
                audio_path = self._speak_text(text, lang)
                if audio_path:
                    print(f"🔊 语音已生成: {audio_path}")
                    result = {"audio_path": audio_path, "text": text}
                else:
                    result = {"error": "语音合成失败"}
                    print("❌ 语音合成失败")
            
            elif action == "stats":
                result = self._get_stats(lang)
                self._print_stats(result)
            
            elif action == "mark_learned":
                word = kwargs.get("word", "")
                item_type = kwargs.get("type", "word")
                if not word:
                    return {"status": "error", "error": "请提供 word 参数"}
                result = self._mark_learned(lang, word, item_type)
                print(f"✅ 已标记 '{word}' 为已学习")
            
            # ===== 知识库管理 =====
            elif action == "kb_stats":
                result = self._kb_stats(lang)
                self._print_kb_stats(result)
            
            elif action == "kb_add_word":
                word = kwargs.get("word", "")
                meaning = kwargs.get("meaning", "")
                example = kwargs.get("example", "")
                if not word or not meaning:
                    return {"status": "error", "error": "请提供 word 和 meaning 参数"}
                result = self._kb_add_word(lang, word, meaning, example)
                if result.get("status") == "success":
                    print(f"✅ 已添加单词: {word} - {meaning}")
            
            elif action == "kb_add_sentence":
                original = kwargs.get("original", "")
                translation = kwargs.get("translation", "")
                if not original or not translation:
                    return {"status": "error", "error": "请提供 original 和 translation 参数"}
                result = self._kb_add_sentence(lang, original, translation)
                if result.get("status") == "success":
                    print(f"✅ 已添加句子: {original} - {translation}")
            
            elif action == "kb_add_grammar":
                title = kwargs.get("title", "")
                rule = kwargs.get("rule", "")
                example = kwargs.get("example", "")
                if not title or not rule:
                    return {"status": "error", "error": "请提供 title 和 rule 参数"}
                result = self._kb_add_grammar(lang, title, rule, example)
                if result.get("status") == "success":
                    print(f"✅ 已添加语法: {title}")
            
            elif action == "kb_import_text":
                text = kwargs.get("text", "")
                if not text:
                    return {"status": "error", "error": "请提供 text 参数"}
                result = self._kb_import_text(lang, text)
                print(f"✅ 导入完成: {result.get('added', 0)} 个单词")
            
            elif action == "kb_import_list":
                words = kwargs.get("words", "")
                if not words:
                    return {"status": "error", "error": "请提供 words 参数"}
                result = self._kb_import_list(lang, words)
                print(f"✅ 导入完成: {result.get('added', 0)} 个单词")
                if result.get("failed"):
                    print(f"⚠️ 需要补充释义: {', '.join(result['failed'])}")
            
            elif action == "kb_export":
                format = kwargs.get("format", "json")
                result = self._kb_export(lang, format)
                if result.get("file"):
                    print(f"✅ 已导出: {result['file']}")
            
            elif action == "kb_lookup":
                word = kwargs.get("word", "")
                if not word:
                    return {"status": "error", "error": "请提供 word 参数"}
                result = self._kb_lookup(word, lang)
                self._print_lookup(result)

            elif action == "kb_download_full_dict":
                source = kwargs.get("source", "wordnet")
                print(f"📥 正在下载 {source} 词典...")
                result = self._kb_download_full_dict(lang, source)
                if result.get("added"):
                    print(f"✅ 下载完成: {result['added']} 个单词")
                else:
                    print(f"❌ {result.get('error', '下载失败')}")
                    
            else:
                return {"status": "error", "error": f"未知操作: {action}"}
            
            return {
                "status": "success" if result.get("status") != "error" else "error",
                "result": result,
                "metadata": {
                    "skill": self.name,
                    "version": self.version,
                    "executed_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "skill": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    # ==================== 打印方法 ====================
    
    def _print_list(self, result: Dict):
        print("\n" + "=" * 60)
        print("   📚 可用语言")
        print("=" * 60)
        for code, info in result.items():
            current = " ✅ 当前" if code == self.current_lang else ""
            print(f"  {code}: {info['name']} (单词: {info['words']}, 句子: {info['sentences']}, 语法: {info['grammar']}){current}")
        print("=" * 60)
    
    def _print_flashcard(self, result: Dict):
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        if result.get("all_learned"):
            print("🎉 所有单词已学完！")
            return
        print("\n" + "=" * 60)
        print(f"   🃏 闪卡模式 - {result.get('language', '')}")
        print(f"   进度: {result.get('progress', '')}")
        print("=" * 60)
        for item in result.get("items", []):
            print(f"\n📖 {item['word']}")
            print(f"   {item['meaning']}")
            if item.get("example"):
                print(f"   📝 {item['example']}")
        print(f"\n共 {result.get('total', 0)} 个单词")
        print("=" * 60)
    
    def _print_quiz(self, result: Dict):
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print("\n" + "=" * 60)
        print(f"   ❓ 选择题测验 - {result.get('language', '')}")
        print("=" * 60)
        for i, q in enumerate(result.get("questions", []), 1):
            print(f"\n{i}. '{q['word']}' 是什么意思？")
            for j, opt in enumerate(q.get("options", []), 1):
                print(f"   {chr(64+j)}. {opt}")
            print(f"   ✅ 正确答案: {q['correct']}")
        print(f"\n共 {result.get('total', 0)} 题")
        print("=" * 60)
    
    def _print_sentence(self, result: Dict):
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print("\n" + "=" * 60)
        print(f"   💬 句子练习 - {result.get('language', '')}")
        print("=" * 60)
        for item in result.get("items", []):
            print(f"\n📝 {item['original']}")
            print(f"   {item['translation']}")
        print(f"\n共 {result.get('total', 0)} 个句子")
        print("=" * 60)
    
    def _print_grammar(self, result: Dict):
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print("\n" + "=" * 60)
        print(f"   📖 语法学习 - {result.get('language', '')}")
        print("=" * 60)
        for item in result.get("items", []):
            print(f"\n📌 {item['title']}")
            print(f"   规则: {item['rule']}")
            print(f"   例句: {item['example']}")
        print(f"\n共 {result.get('total', 0)} 条语法")
        print("=" * 60)
    
    def _print_review(self, result: Dict):
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print("\n" + "=" * 60)
        print(f"   🔄 复习模式 - {result.get('language', '')}")
        print("=" * 60)
        for item in result.get("items", []):
            print(f"\n📖 {item['word']}")
            print(f"   {item['meaning']}")
            if item.get("example"):
                print(f"   📝 {item['example']}")
        print(f"\n共 {result.get('total', 0)} 个单词")
        print("=" * 60)
    
    def _print_stats(self, result: Dict):
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print("\n" + "=" * 60)
        print(f"   📊 学习统计 - {result.get('language', '')}")
        print("=" * 60)
        print(f"\n📝 单词: {result.get('word_progress', '')}")
        print(f"📝 句子: {result.get('learned_sentences', 0)}/{result.get('total_sentences', 0)}")
        print(f"📝 语法: {result.get('learned_grammar', 0)}/{result.get('total_grammar', 0)}")
        stats = result.get("stats", {})
        if stats:
            print(f"\n📈 学习统计:")
            print(f"   总尝试: {stats.get('total_attempts', 0)}")
            print(f"   正确数: {stats.get('correct_answers', 0)}")
            if stats.get("last_study"):
                print(f"   上次学习: {stats['last_study'][:16]}")
        print("=" * 60)
    
    def _print_kb_stats(self, result: Dict):
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        print("\n" + "=" * 60)
        print(f"   📊 知识库统计 - {result.get('name', result.get('language', ''))}")
        print("=" * 60)
        print(f"\n📝 单词: {result.get('words', 0)}")
        print(f"📝 句子: {result.get('sentences', 0)}")
        print(f"📝 语法: {result.get('grammar', 0)}")
        print("=" * 60)
    
    def _print_lookup(self, result: Dict):
        if result.get("status") == "error":
            print(f"❌ 查询失败: {result.get('message', '未知错误')}")
            return
        print("\n" + "=" * 60)
        print(f"   📖 词典查询 - {result.get('word', '')}")
        print("=" * 60)
        for m in result.get("meanings", []):
            print(f"\n📌 {m.get('part', '')}")
            print(f"   {m.get('definition', '')}")
            if m.get("example"):
                print(f"   📝 {m.get('example', '')}")
        print("=" * 60)
    
    def __repr__(self):
        return f"<LanguageLearner(name={self.name}, version={self.version})>"