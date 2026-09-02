# language_learner

> AI 驱动的多语言学习助手，支持单词、语法、句子学习，集成语音发音

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 39
- **函数数**: 1

## 支持的语言

| 语言 | 代码 | 词条数 | 数据源 |
|------|------|--------|--------|
| 英语 | en | 87,353 | WordNet (OMW) |
| 西班牙语 | es | 90,851 | WordNet (OMW) |
| 法语 | fr | 55,316 | WordNet (OMW) |
| 意大利语 | it | 41,829 | WordNet (OMW) |
| 葡萄牙语 | pt | 50,000 | WordNet (OMW) |
| 荷兰语 | nl | 43,066 | WordNet (OMW) |
| 波兰语 | pl | 45,342 | WordNet (OMW) |
| 芬兰语 | fi | 50,000 | WordNet (OMW) |
| 希腊语 | el | 18,216 | WordNet (OMW) |
| 阿拉伯语 | ar | 17,772 | WordNet (OMW) |
| 希伯来语 | he | 5,325 | WordNet (OMW) |
| 泰语 | th | 50,000 | WordNet (OMW) |
| 瑞典语 | sv | 5,823 | WordNet (OMW) |
| 日语 | ja | 15,012 | Jamdict |
| 中文 | zh | 10,000 | CEDICT + Jieba |
| 德语 | de | 230 | OpenThesaurus + 内置 |
| 韩语 | ko | 132 | 内置词库 |

**总计：~580,000+ 词汇量**

## 支持的功能

| 功能 | 说明 |
|------|------|
| 🃏 闪卡学习模式 | 高效的单词记忆方式 |
| ❓ 选择题测验 | 检验学习成果 |
| 💬 句子练习 | 学习实际应用场景 |
| 📖 语法学习 | 掌握语言规则 |
| 🔄 复习模式 | 巩固已学知识 |
| 🔊 语音合成 | 支持多语言发音 (Edge TTS) |
| 📊 学习进度追踪 | 记录学习统计 |
| 📥 完整词典下载 | 一键下载各语言词典 |
| 📚 知识库管理 | 添加/导入/导出单词和句子 |

## 词典数据源说明

| 语言 | 数据源 | 说明 |
|------|--------|------|
| en, es, fr, it, pt, nl, pl, fi, el, ar, he, th, sv | WordNet (OMW) | NLTK Open Multilingual WordNet |
| ja | Jamdict | JMdict 日语词典 |
| zh | CEDICT + Jieba | 中文-英语词典 + Jieba 词库 |
| de | OpenThesaurus + 内置 | 开源德语同义词词典 |
| ko | 内置词库 | 韩语常用词汇 |

## 技能描述

AI 驱动的多语言学习助手，支持单词、语法、句子学习，集成语音发音

## 依赖

```bash
pip install nltk
pip install edge-tts
pip install requests
pip install jamdict
pip install jieba
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `action` | string | `` | 操作类型 (learn_word/learn_grammar/practice/quiz/speak/stats/list_languages/set_language/translate/review) |
| `language` | string | `en` | 目标语言 (en/ja/ko/fr/de/es) |
| `text` | string | `` | 要发音或翻译的文本 |
| `word` | string | `` | 测验时的单词 |
| `answer` | string | `` | 用户的答案 |
| `count` | integer | `5` | 复习数量 |

## 输出

| 字段 | 说明 |
|------|------|
| `word` | 学习的单词 |
| `meaning` | 单词含义 |
| `example` | 例句 |
| `audio_path` | 语音文件路径 |
| `grammar` | 语法规则 |
| `sentence` | 练习句子 |
| `translation` | 翻译结果 |
| `stats` | 学习统计 |

## 使用方法

```bash
python -m markflow.cli.commands execute language_learner [参数]
```

### 示例

```bash
## 依赖安装

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

### NLTK 数据下载

```python
import nltk
nltk.download('wordnet')
nltk.download('omw-2.0')
```

### Jamdict 数据下载（日语）

```bash
# 下载 JMdict 词典文件
python -c "from jamdict import Jamdict; jmd=Jamdict(); jmd.import_data()"
```

```

查看完整参数说明：

```bash
python -m markflow.cli.commands info language_learner
```

```bash
# 查看所有可用语言
py -3.14 -m markflow.cli.commands execute language_learner action="list"

# 下载英语词典
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="en" source="wordnet"

# 下载日语词典
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="ja" source="jamdict"

# 下载中文词典
py -3.14 -m markflow.cli.commands execute language_learner action="kb_download_full_dict" language="zh" source="jieba"

# 闪卡模式 - 学习 10 个新单词
py -3.14 -m markflow.cli.commands execute language_learner action="flashcard" language="it" count=10

# 选择题测验 - 5 道题
py -3.14 -m markflow.cli.commands execute language_learner action="quiz" language="es" count=5

# 切换语言
py -3.14 -m markflow.cli.commands execute language_learner action="set_language" language="ja"

# 语音合成
py -3.14 -m markflow.cli.commands execute language_learner action="speak" language="ja" text="こんにちは"

# 查看学习统计
py -3.14 -m markflow.cli.commands execute language_learner action="stats" language="it"
```

### 知识库管理

```bash
# 添加单词
py -3.14 -m markflow.cli.commands execute language_learner action="kb_add_word" language="it" word="ciao" meaning="你好"

# 添加句子
py -3.14 -m markflow.cli.commands execute language_learner action="kb_add_sentence" language="it" original="Come stai?" translation="你好吗？"

# 批量导入
py -3.14 -m markflow.cli.commands execute language_learner action="kb_import_text" language="it" text="ciao:你好\ngrazie:谢谢"

# 导出知识库
py -3.14 -m markflow.cli.commands execute language_learner action="kb_export" language="it" format="json"
```

### 查看报告

```bash
# 查看知识库统计
py -3.14 -m markflow.cli.commands execute language_learner action="kb_stats" language="it"
```

## 输出位置

生成的输出保存在 `skills/language_learner/output/` 目录下。

---

*文档自动生成于 2026-08-24 16:20:30*