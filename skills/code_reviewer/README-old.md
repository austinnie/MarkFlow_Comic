# code_reviewer

> AI 代码审查，发现问题和安全风险

## 概览

- **文件数**: 1
- **类数**: 1
- **方法数**: 9
- **函数数**: 1

## 技能描述

AI 代码审查，发现问题和安全风险

## 依赖

```bash
pip install pylint
pip install flake8
pip install radon
pip install ollama
```

## 各语言依赖安装

### JAVASCRIPT

```bash
npm install -g eslint
```

### JAVA

```bash
# 下载 checkstyle.jar 放到 lib/ 目录
curl -L -o lib/checkstyle.jar https://github.com/checkstyle/checkstyle/releases/download/checkstyle-10.12.0/checkstyle-10.12.0-all.jar

# 下载 spotbugs.jar 放到 lib/ 目录
curl -L -o lib/spotbugs.jar https://github.com/spotbugs/spotbugs/releases/download/4.8.3/spotbugs-4.8.3.jar
```

### CPP

```bash
# Windows
choco install cppcheck

# Linux
sudo apt install cppcheck clang-tidy

# macOS
brew install cppcheck
```

### GO

```bash
go install golang.org/x/lint/golint@latest
go install honnef.co/go/tools/cmd/staticcheck@latest
```

### RUST

```bash
rustup component add clippy
```

### ANDROID

```bash
# 配置 ANDROID_HOME 环境变量
# 使用 Android Studio 自带的 lint 工具

# 安装 ktlint (macOS)
brew install ktlint
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `code_path` | string | `` | 代码文件或目录路径 |
| `language` | string | `python` | 编程语言 (python/js/go) |
| `review_level` | string | `basic` | 审查深度 (basic/deep) |
| `focus` | string | `security` | 审查重点 (security/performance/style) |

## 输出

| 字段 | 说明 |
|------|------|
| `issues` | 发现的问题列表 |
| `suggestions` | 改进建议 |
| `security_risks` | 安全风险警告 |
| `code_score` | 代码质量评分 |

## 使用方法

```bash
python -m markflow.cli.commands execute code_reviewer [参数]
```

### 示例

```bash
# 自动检测并审查所有代码
python -m markflow.cli.commands execute code_reviewer code_path="./project"

# 审查 Python 代码
python -m markflow.cli.commands execute code_reviewer code_path="./markflow"

# 只检查安全问题
python -m markflow.cli.commands execute code_reviewer code_path="./markflow" focus="security"

# 指定 JavaScript 语言
python -m markflow.cli.commands execute code_reviewer code_path="./project" language="javascript"

# 深度审查
python -m markflow.cli.commands execute code_reviewer code_path="./project" review_level="deep"
```

查看完整参数说明：

```bash
python -m markflow.cli.commands info code_reviewer
```

### 查看报告

```bash
python -c "
import json
from pathlib import Path
reports = list(Path('skills/code_reviewer/output').glob('review_*.json'))
if reports:
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    data = json.load(open(latest))
    result = data.get('result', data)
    print(f'评分: {result.get(\"overall_score\", 0)}/100')
    print(f'问题: {result.get(\"issues_count\", 0)} 个')
"
```

## 输出位置

生成的输出保存在 `skills/code_reviewer/output/` 目录下。

---

*文档自动生成于 2026-08-23 22:11:44*