# news_aggregator

> RSS 新闻抓取 + AI 摘要生成

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 13
- **函数数**: 1

## 支持的功能

| 功能 | 说明 |
|------|------|
| 📡 RSS 抓取 | 自动抓取多个 RSS 源 |
| 🤖 AI 摘要 | 使用 Ollama 生成智能摘要 |
| 📂 分类聚合 | 科技/财经/国际/中国/美国/日本/韩国 |
| 📰 每日简报 | 生成格式化的新闻简报 |
| 🔗 来源去重 | 自动去重，减少重复内容 |
| 📁 报告保存 | 保存为 TXT 格式 |

## 支持的地区分类

| 分类 | 说明 | 源数量 |
|------|------|--------|
| `tech` | 科技新闻（国际 + 中日韩） | 20+ |
| `business` | 财经新闻（国际 + 中日韩） | 15+ |
| `world` | 国际新闻 | 20+ |
| `china` | 中国新闻 | 12 |
| `usa` | 美国新闻 | 14 |
| `japan` | 日本新闻 | 8 |
| `korea` | 韩国新闻 | 6 |

## 技能描述

RSS 新闻抓取 + AI 摘要生成

## 依赖

```bash
pip install feedparser
pip install requests
pip install ollama
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `sources` | string | `` | RSS 源列表 |
| `category` | string | `tech` | 新闻分类 (tech/business/world) |
| `top_n` | integer | `10` | 提取 Top N 条新闻 |
| `summary_length` | integer | `100` | 摘要长度 |

## 输出

| 字段 | 说明 |
|------|------|
| `news` | 新闻列表 |
| `summaries` | AI 摘要 |
| `daily_report` | 每日简报 |

## 使用方法

```bash
python -m markflow.cli.commands execute news_aggregator [参数]
```

### 示例

```bash
# 抓取科技新闻（5条）
python -m markflow.cli.commands execute news_aggregator category="tech" top_n=5

# 抓取中国新闻（10条）
python -m markflow.cli.commands execute news_aggregator category="china" top_n=10

# 抓取财经新闻
python -m markflow.cli.commands execute news_aggregator category="business" top_n=5

# 自定义源
python -m markflow.cli.commands execute news_aggregator sources="TechCrunch,BBC"

# 语音播报新闻（配合 voice_assistant）
python scripts/news_voice_broadcast.py --category tech --top 5 --play
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info news_aggregator
```

### 查看报告

```bash
cat skills/news_aggregator/output/news_*.txt
```

### 语音播报

```bash
# 科技新闻播报
python scripts/news_voice_broadcast.py --category tech --top 5 --play

# 中国新闻播报
python scripts/news_voice_broadcast.py --category china --top 5 --play
```

## 输出位置

生成的输出保存在 `skills/news_aggregator/output/` 目录下。

---

*文档自动生成于 2026-08-24 07:38:05*