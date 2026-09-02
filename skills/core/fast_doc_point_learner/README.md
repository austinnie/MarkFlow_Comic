# fast_doc_point_learner

> 输入 Word、PDF、PPT、Excel、TXT 等文档，自动提取核心内容，生成结构化摘要，理清文档之间的关系


## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 18
- **函数数**: 0


## 技能描述

文档快速学习助手，自动解析多种格式文档，提取核心内容，生成 AI 摘要，分析文档之间的关系。

### 核心功能

- 📄 **多格式支持** - Word (.docx)、PDF (.pdf)、PPT (.pptx)、Excel (.xlsx)、TXT (.txt)
- 📝 **内容提取** - 自动提取标题、段落、表格等关键信息
- 🤖 **智能摘要** - 使用 AI 生成文档核心内容摘要
- 🔗 **关系分析** - 分析文档之间的引用、依赖、补充等关系
- 📊 **结构化展示** - 以清晰的结构展示文档内容和关系图谱
- 🌐 **多语言支持** - 支持中文、英语、日语、韩语、西班牙语、法语、德语


## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `doc_path` | string | 是 | - | 文档路径（文件或目录） |
| `recursive` | boolean | 否 | true | 是否递归处理子目录 |
| `max_chars` | integer | 否 | 5000 | 每个文档最大提取字符数 |
| `summary_length` | integer | 否 | 300 | 摘要长度（字数） |
| `output_format` | string | 否 | md | 输出格式 (md/json) |
| `extract_images` | boolean | 否 | false | 是否提取图片中的文字 (OCR) |
| `extract_tables` | boolean | 否 | true | 是否提取表格内容 |
| `relationship_depth` | integer | 否 | 2 | 关系分析深度 |
| `language` | string | 否 | zh | 输出语言 (zh/en/ja/ko/es/fr/de) |


## 输出

| 字段 | 说明 |
|------|------|
| `report_path` | 报告文件路径 |
| `total_docs` | 文档总数 |
| `docs` | 文档列表及摘要 |
| `relationships` | 文档关系图谱 |
| `generated_at` | 生成时间 |


## 使用示例

```bash
# 分析单个文档
python -m markflow.cli.commands execute fast_doc_point_learner doc_path="./report.docx"

# 分析整个目录
python -m markflow.cli.commands execute fast_doc_point_learner doc_path="./docs/"

# 指定摘要长度
python -m markflow.cli.commands execute fast_doc_point_learner doc_path="./docs/" summary_length=200

# 指定输出语言（日语）
python -m markflow.cli.commands execute fast_doc_point_learner doc_path="./docs/" language="ja"

# 生成 JSON 格式报告
python -m markflow.cli.commands execute fast_doc_point_learner doc_path="./docs/" output_format="json"

# 查看完整参数说明：
python -m markflow.cli.commands info fast_doc_point_learner
```


## 输出示例

### 目录结构树

```text
docs/
├── 项目需求文档.docx
├── 系统架构设计.pdf
├── 接口文档.docx
├── 开发计划.xlsx
└── 会议纪要.pptx
```

### 文档列表及摘要

| 文档 | 类型 | 摘要 | 关键词 |
|------|------|------|--------|
| 项目需求文档.docx | Word | 描述了项目背景、目标用户、核心功能模块和验收标准 | 需求、功能、验收 |
| 系统架构设计.pdf | PDF | 介绍了系统整体架构、技术选型、数据流和部署方案 | 架构、技术栈、部署 |
| 接口文档.docx | Word | 定义了 REST API 的端点、请求/响应格式和认证方式 | API、接口、认证 |

### 整体摘要

本次分析共处理 5 份文档，涵盖项目从需求到实施的全流程：

- 需求阶段：项目需求文档.docx 明确了业务目标
- 设计阶段：系统架构设计.pdf 提供了技术方案
- 开发阶段：接口文档.docx 和 开发计划.xlsx 指导具体实施
- 管理阶段：会议纪要.pptx 记录了过程决策

核心主题：项目交付、技术架构、进度管理

### 文档关系图谱

```text
项目需求文档.docx → 系统架构设计.pdf [引用]
  需求驱动架构设计
项目需求文档.docx → 开发计划.xlsx [引用]
  需求决定任务范围
系统架构设计.pdf → 接口文档.docx [引用]
  架构定义接口规范
```

### 关系图（Mermaid）  
```Mermaid
graph TD
    A[项目需求文档.docx] --> B[系统架构设计.pdf]
    A --> C[开发计划.xlsx]
    B --> E[接口文档.docx]
```
	
### 依赖安装
```bash
pip install python-docx PyPDF2 python-pptx openpyxl requests
```

## 输出位置

生成的报告保存在 `skills/fast_doc_point_learner/output/` 目录下。

| 路径 | 说明 |
|------|------|
| `skills/fast_doc_point_learner/output/doc_learning_report_{timestamp}.md` | Markdown 格式报告 |
| `skills/fast_doc_point_learner/output/doc_learning_report_{timestamp}.json` | JSON 格式报告 |


## 适用场景

- **大量文档快速浏览** - 快速了解多份文档的核心内容
- **项目文档梳理** - 理清项目文档之间的关联关系
- **知识库管理** - 自动生成文档摘要和关键词
- **文档归档** - 为文档生成结构化的学习报告


