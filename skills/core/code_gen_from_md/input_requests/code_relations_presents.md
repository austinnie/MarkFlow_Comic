# 代码分析报告生成器

> 输入代码目录，自动生成代码结构分析报告，展示模块关系、函数调用链和架构概览


## 需求描述

当开发者接手一个新项目时，通常需要花费大量时间理解代码结构。本工具旨在解决这个问题：**输入一个代码目录，自动分析并生成结构化的代码关系文档**，帮助开发者快速理解代码架构。

### 核心功能

1. **目录结构可视化** - 以树形结构展示项目目录
2. **模块依赖分析** - 展示模块之间的 import/require 关系
3. **调用关系图** - 展示主要函数/方法之间的调用链
4. **类继承关系** - 展示类的继承结构
5. **核心模块识别** - 自动标记核心模块和入口文件


## 输入

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `code_path` | string | 是 | - | 要分析的代码目录或文件路径 |
| `language` | string | 否 | auto | 编程语言 (python/javascript/java/go/rust/auto) |
| `exclude_patterns` | string | 否 | __pycache__,node_modules,.git,*.pyc | 排除的文件/目录（逗号分隔） |
| `output_format` | string | 否 | md | 输出格式 (md/html/json) |
| `max_depth` | integer | 否 | 5 | 目录遍历最大深度 |
| `include_tests` | boolean | 否 | false | 是否包含测试目录 |
| `show_private` | boolean | 否 | false | 是否显示私有函数/方法 |


## 输出

| 字段 | 说明 |
|------|------|
| `tree` | 目录树结构 |
| `modules` | 模块列表及职责 |
| `dependencies` | 模块依赖关系矩阵 |
| `call_graph` | 主要函数调用关系 |
| `class_hierarchy` | 类继承关系 |
| `entry_points` | 入口文件识别 |
| `core_modules` | 核心模块标记 |
| `statistics` | 代码统计（文件数、代码行数等） |


## 使用示例

```bash
# 分析整个项目
python -m markflow.cli.commands execute code_analyzer code_path="./my_project"

# 只分析特定语言
python -m markflow.cli.commands execute code_analyzer code_path="./my_project" language="python"

# 生成 JSON 格式报告
python -m markflow.cli.commands execute code_analyzer code_path="./my_project" output_format="json"

# 排除测试目录
python -m markflow.cli.commands execute code_analyzer code_path="./my_project" include_tests=false
```

## 输出示例

### 目录结构树

```text
my_project/
├── core/
│   ├── models/
│   │   └── user.py          # 用户模型
│   ├── post.py              # 文章模型
│   ├── services/
│   │   ├── auth.py          # 认证服务
│   │   ├── database.py      # 数据库服务
│   │   └── utils/
│   │       └── logger.py    # 日志工具
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth_routes.py   # 认证路由
│   │   │   └── post_routes.py   # 文章路由
│   │   ├── middleware.py    # 中间件
│   │   ├── tests/
│   │   ├── docs/
│   │   └── main.py          # 入口文件
│   └── config.py            # 配置文件
```

### 模块依赖关系

```text
core/services/auth.py
    ├── import core/models/user.py
    ├── import core/utils/logger.py
    └── import config.py

core/services/database.py
    ├── import core/models/*.py
    └── import config.py

api/routes/auth_routes.py
    ├── import core/services/auth.py
    └── import core/models/user.py

main.py
    ├── import api/routes/*.py
    ├── import core/services/database.py
    └── import config.py
```

### 函数调用关系

```text
main()
    ├── init_database()
    │   └── Database.connect()
    ├── setup_routes()
    │   ├── AuthRoutes.register()
    │   │   └── AuthService.login()
    │   │       └── User.find_by_email()
    │   └── PostRoutes.register()
    │       └── PostService.get_posts()
    │           └── Post.find_all()
    └── start_server()
```

### 类继承关系

```text
BaseModel (core/models/base.py)
    ├── User (core/models/user.py)
    │   └── AdminUser (core/models/admin.py)
    └── Post (core/models/post.py)

BaseService (core/services/base.py)
    ├── AuthService (core/services/auth.py)
    └── PostService (core/services/post.py)
```

### 核心模块标记

| 模块 | 路径 | 原因 |
|------|------|------|
| 🚀 main.py | ./main.py | 包含 if __name__ == "__main__" |
| ⚙️ config.py | ./config.py | 被 5+ 个模块引用 |
| 🔧 core/services/database.py | ./core/services/database.py | 被 10+ 个模块引用 |
| 📦 core/models/user.py | ./core/models/user.py | 基础数据模型 |

### 代码统计

| 指标 | 数量 |
|------|------|
| 总文件数 | 47 |
| 总代码行数 | 8,234 |
| Python 文件 | 42 |
| 类数 | 15 |
| 函数数 | 68 |
| 注释行数 | 1,234 |


## 配置文件示例

```json
{
  "code_path": "./my_project",
  "language": "auto",
  "exclude_patterns": ["__pycache__", "node_modules", ".git", "*.pyc", ".DS_Store"],
  "output_format": "md",
  "max_depth": 5,
  "include_tests": false,
  "show_private": false
}
```

## 依赖安装

```bash
pip install ast radon pydeps
```

## 输出位置

生成的报告保存在 `skills/code_analyzer/output/` 目录下。

| 路径 | 说明 |
|------|------|
| `skills/code_analyzer/output/report.md` | Markdown 格式报告 |
| `skills/code_analyzer/output/report.json` | JSON 格式报告 |
| `skills/code_analyzer/output/graph.png` | 依赖关系图（可选） |

---

*文档版本: 1.0.0 | 生成于 2026-08-25*