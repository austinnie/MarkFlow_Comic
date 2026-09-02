# code_gen_from_md

> 代码生成器，从 Markdown 需求文档自动生成高质量代码。支持 Python、JavaScript、Java、Go、Rust 等多种语言，内置语法检查、代码优化、单元测试生成和 AI 代码审查。

## 描述

代码生成器，从 Markdown 需求文档自动生成高质量代码。支持 Python、JavaScript、Java、Go、Rust 等多种语言，内置语法检查、代码优化、单元测试生成和 AI 代码审查。

## 核心功能

1. 📝 **Markdown 解析** - 自动解析需求文档中的标题、描述、需求列表和代码示例
2. 🤖 **AI 代码生成** - 使用 Ollama 生成高质量代码
3. ✅ **语法检查** - 自动检查 Python 语法、导入语句、文档字符串、命名规范
4. 🔧 **代码优化** - 自动修复代码问题，格式化代码
5. 🧪 **单元测试生成** - 自动生成 Python 单元测试
6. 📊 **代码审查** - AI 多维度审查代码质量并评分
7. 🌐 **多语言支持** - Python、JavaScript、TypeScript、Java、Go、Rust、C++、HTML、CSS、Bash、SQL 等

## 输入参数

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `md_file` | string | 否 |  | Markdown 需求文件路径 |
| `md_content` | string | 否 |  | Markdown 需求内容（直接传入） |
| `language` | string | 否 | python | 目标语言（从 Markdown 自动检测） |
| `model` | string | 否 | qwen2.5:7b | Ollama 模型 |
| `mode` | string | 否 | full | 生成模式 (full/step) |

## 输出

| 字段 | 说明 |
|------|------|
| `title` | 项目名称 |
| `language` | 目标语言 |
| `saved_files` | 生成的文件列表 |
| `quality_score` | 质量评分 (0-100) |
| `validations_passed` | 是否通过校验 |
| `optimized` | 是否经过优化 |
| `generated_at` | 生成时间 |

## 使用方法

```bash
python -m markflow.cli.commands execute code_gen_from_md [参数]
```

## 依赖安装

```bash
pip install requests
pip install black
pip install pylint
```

---

*文档生成于 2026-08-28 17:33:40*