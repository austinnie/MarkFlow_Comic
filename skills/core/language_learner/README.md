# 🌍 Language Learner - 多语言学习助手

一个强大的多语言学习技能，支持 **17 种语言**，包含 **58 万+ 词汇量**的词典系统，提供闪卡、测验、句子练习等多种学习模式。

## ✨ 功能特性

- 📚 **多语言知识库管理** - 支持 17 种语言的单词/句子/语法管理
- 🃏 **闪卡学习模式** - 高效的单词记忆方式
- ❓ **选择题测验** - 检验学习成果
- 💬 **句子练习** - 学习实际应用场景
- 📖 **语法学习** - 掌握语言规则
- 🔄 **复习模式** - 巩固已学知识
- 🔊 **语音合成** - 支持多语言发音 (Edge TTS)
- 📊 **学习进度追踪** - 记录学习统计
- 📥 **完整词典下载** - 一键下载各语言词典

## 🌐 支持的语言

| 语言   | 代码  | 词条数    | 数据源                |
| ---- | --- | ------ | ------------------ |
| 英语   | en  | 87,353 | WordNet (OMW)      |
| 西班牙语 | es  | 90,851 | WordNet (OMW)      |
| 法语   | fr  | 55,316 | WordNet (OMW)      |
| 意大利语 | it  | 41,829 | WordNet (OMW)      |
| 葡萄牙语 | pt  | 50,000 | WordNet (OMW)      |
| 荷兰语  | nl  | 43,066 | WordNet (OMW)      |
| 波兰语  | pl  | 45,342 | WordNet (OMW)      |
| 芬兰语  | fi  | 50,000 | WordNet (OMW)      |
| 希腊语  | el  | 18,216 | WordNet (OMW)      |
| 阿拉伯语 | ar  | 17,772 | WordNet (OMW)      |
| 希伯来语 | he  | 5,325  | WordNet (OMW)      |
| 泰语   | th  | 50,000 | WordNet (OMW)      |
| 瑞典语  | sv  | 5,823  | WordNet (OMW)      |
| 日语   | ja  | 15,012 | Jamdict            |
| 中文   | zh  | 10,000 | CEDICT + Jieba     |
| 德语   | de  | 230    | OpenThesaurus + 内置 |
| 韩语   | ko  | 132    | 内置词库               |

**总计：~580,000+ 词汇量**

## 📁 目录结构

```text
skills/language_learner/
├── knowledge/                    # 知识库目录
│   ├── {lang}.json              # 各语言知识库文件
│   ├── nltk_data/               # NLTK 数据 (WordNet/OMW)
│   │   └── corpora/
│   │       ├── wordnet.zip
│   │       ├── omw-1.4.zip
│   │       └── omw-2.0.zip
│   ├── jamdict_data/            # Jamdict 数据 (日语)
│   │   └── data/
│   │       └── JMdict_e.gz
│   └── chinese_data/            # 中文数据 (可选)
│       └── cedict_ts.u8
├── output/                       # 输出目录
│   ├── audio/                    # 语音文件
│   └── export/                   # 导出文件
├── progress.json                 # 学习进度
├── skill.py                      # 主技能文件
└── README.md                     # 本文档
```

## 🚀 快速开始

### 1. 查看所有可用语言

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="list"
```

### 2. 下载语言词典

```bash
# 英语
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="en" source="wordnet"

# 日语
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="ja" source="jamdict"

# 中文
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="zh" source="jieba"

# 意大利语 (OMW)
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="it" source="wordnet"

# 西班牙语 (OMW)
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="es" source="wordnet"
```

### 3. 切换语言

```bash
# 切换到意大利语
py -3.14 -m markflow.cli.commands execute language_learner action="set_language" language="it"
```

### 4. 开始学习

```bash
# 闪卡模式 - 学习 10 个新单词
py -3.14 -m markflow.cli.commands execute language_learner action="flashcard" language="it" count=10

# 选择题测验 - 5 道题
py -3.14 -m markflow.cli.commands execute language_learner action="quiz" language="it" count=5

# 句子练习
py -3.14 -m markflow.cli.commands execute language_learner action="sentence" language="ja"

# 语法学习
py -3.14 -m markflow.cli.commands execute language_learner action="grammar" language="ja"

# 复习已学单词
py -3.14 -m markflow.cli.commands execute language_learner action="review" language="it" count=10

# 查看学习统计
py -3.14 -m markflow.cli.commands execute language_learner action="stats" language="it"
```

## 📖 学习模式详解

### 🃏 闪卡模式 (Flashcard)

显示单词和释义，帮助记忆新词汇。

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="flashcard" language="en" count=10
```

### ❓ 选择题测验 (Quiz)

从词库中随机出题，选择正确的释义。

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="quiz" language="es" count=5
```

### 💬 句子练习 (Sentence)

学习实际应用场景中的句子。

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="sentence" language="ja"
```

### 📖 语法学习 (Grammar)

学习语法规则和例句。

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="grammar" language="en"
```

### 🔄 复习模式 (Review)

复习已学习的单词。

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="review" language="it" count=10
```

## 🎤 语音合成

支持多语言语音合成 (Edge TTS)：

```bash
# 播放日语发音
py -3.14 -m markflow.cli.commands execute language_learner action="speak" language="ja" text="こんにちは"
```

## 📊 知识库管理

### 查看知识库统计

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="kb_stats" language="it"
```

### 添加单词

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="kb_add_word" language="it" word="ciao" meaning="你好"
```

### 添加句子

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="kb_add_sentence" language="it" original="Come stai?" translation="你好吗？"
```

### 批量导入

```bash
# 从文本导入 (每行: word:meaning)
py -3.14 -m markflow.cli.commands execute language_learner action="kb_import_text" language="it" text="ciao:你好\ngrazie:谢谢"
```

### 导出知识库

```bash
# 导出为 JSON
py -3.14 -m markflow.cli.commands execute language_learner action="kb_export" language="it" format="json"

# 导出为 CSV
py -3.14 -m markflow.cli.commands execute language_learner action="kb_export" language="it" format="csv"
```

### 标记已学习

```bash
py -3.14 -m markflow.cli.commands execute language_learner action="mark_learned" language="it" word="ciao" type="word"
```

## 🔧 词典数据源说明

| 语言                                                 | 数据源                | 说明                             |
| -------------------------------------------------- | ------------------ | ------------------------------ |
| en, es, fr, it, pt, nl, pl, fi, el, ar, he, th, sv | WordNet (OMW)      | NLTK Open Multilingual WordNet |
| ja                                                 | Jamdict            | JMdict 日语词典                    |
| zh                                                 | CEDICT + Jieba     | 中文-英语词典 + Jieba 词库             |
| de                                                 | OpenThesaurus + 内置 | 开源德语同义词词典                      |
| ko                                                 | 内置词库               | 韩语常用词汇                         |

## 📦 依赖安装

```bash
# 基础依赖
pip install nltk edge-tts requests

# 日语词典
pip install jamdict

# 中文分词
pip install jieba

# 韩语 (可选)
pip install konlpy
```

## 📝 学习进度文件

进度保存在 `progress.json`：

```json
{
  "en": {
    "learned_words": ["apple", "book"],
    "learned_sentences": ["How are you?"],
    "learned_grammar": ["一般现在时"],
    "stats": {
      "total_attempts": 100,
      "correct_answers": 85,
      "last_study": "2026-08-24T15:45:00"
    }
  }
}
```

## 🤝 贡献

欢迎添加更多语言的词典支持或新的学习模式！

## 📄 许可证

MIT License

---

**享受学习 17 种语言的乐趣！**