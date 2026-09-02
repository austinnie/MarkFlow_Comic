# 新闻聚合器

## 描述
RSS 新闻抓取 + AI 摘要生成

## 类别
数据处理

## 难度
⭐⭐

## 输入
- **sources** (string): RSS 源列表 (可选)
  - 默认: 
- **category** (string): 新闻分类 (tech/business/world) (可选)
  - 默认: tech
- **top_n** (integer): 提取 Top N 条新闻 (可选)
  - 默认: 10
- **summary_length** (integer): 摘要长度 (可选)
  - 默认: 100

## 输出
- **news**: 新闻列表
- **summaries**: AI 摘要
- **daily_report**: 每日简报

## 依赖
- feedparser
- requests
- ollama

## 功能
- RSS 抓取
- AI 摘要
- 分类聚合
- 每日简报

## 状态
待实现