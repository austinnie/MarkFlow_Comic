# code_reviewer 使用示例

以下是从代码中提取的使用示例：

## skill

### CodeReviewer

```python
# 创建实例
obj = CodeReviewer(config)
```

```python
result = obj._setup_logging()
result = obj._setup_config()
result = obj._load_checkers()
# 加载各语言检查器
```

## android_checker

### AndroidChecker

```python
result = obj.check(files, focus, review_level, max_files)
result = obj._check_android()
# 检查 Android SDK 是否可用
result = obj._run_android_lint(file_path)
# 运行 Android Lint
```

## base

### BaseChecker

```python
# 创建实例
obj = BaseChecker(config)
```

```python
result = obj.check(files, focus, review_level, max_files)
# 检查文件列表

Args:
    files: 文件路径列表
    focus: 审查重点 (security/pe
result = obj._limit_files(files, max_files)
# 限制文件数量
```

## cpp_checker

### CppChecker

```python
result = obj.check(files, focus, review_level, max_files)
result = obj._check_cppcheck()
# 检查 cppcheck 是否可用
result = obj._check_clang_tidy()
# 检查 clang-tidy 是否可用
```

## go_checker

### GoChecker

```python
result = obj.check(files, focus, review_level, max_files)
result = obj._check_go()
# 检查 Go 是否可用
result = obj._run_go_vet(file_path)
# 运行 go vet
```

## javascript_checker

### JavaScriptChecker

```python
result = obj.check(files, focus, review_level, max_files)
result = obj._check_eslint()
# 检查 eslint 是否可用
result = obj._run_eslint(file_path)
```

## java_checker

### JavaChecker

```python
result = obj.check(files, focus, review_level, max_files)
result = obj._check_checkstyle()
# 检查 checkstyle 是否可用
result = obj._check_spotbugs()
# 检查 spotbugs 是否可用
```

## python_checker

### PythonChecker

```python
result = obj.check(files, focus, review_level, max_files)
result = obj._run_pylint(file_path)
result = obj._run_flake8(file_path)
```

## rust_checker

### RustChecker

```python
result = obj.check(files, focus, review_level, max_files)
result = obj._check_cargo()
# 检查 Cargo 是否可用
result = obj._run_clippy(file_path)
# 运行 clippy
```

## tools

## __init__
