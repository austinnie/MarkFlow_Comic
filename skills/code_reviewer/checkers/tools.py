"""
工具检测模块 - 检测各语言检查工具是否已安装
"""

import subprocess
import shutil
from typing import Dict, List


def check_tool_installed(tool_name: str, check_cmd: List[str] = None) -> bool:
    """检查工具是否已安装"""
    # 先检查是否在 PATH 中
    if shutil.which(tool_name):
        return True
    
    # 如果指定了检查命令，尝试执行
    if check_cmd:
        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            pass
    
    return False


def check_python_tools() -> Dict[str, bool]:
    """检查 Python 工具"""
    return {
        "pylint": check_tool_installed("pylint", ["python", "-m", "pylint", "--version"]),
        "flake8": check_tool_installed("flake8", ["python", "-m", "flake8", "--version"]),
        "bandit": check_tool_installed("bandit", ["python", "-m", "bandit", "--version"]),
        "radon": check_tool_installed("radon", ["python", "-m", "radon", "--version"]),
    }


def check_javascript_tools() -> Dict[str, bool]:
    """检查 JavaScript 工具"""
    return {
        "eslint": check_tool_installed("eslint", ["npx", "eslint", "--version"]),
    }


def check_java_tools() -> Dict[str, bool]:
    """检查 Java 工具"""
    return {
        "checkstyle": check_tool_installed("checkstyle"),
        "spotbugs": check_tool_installed("spotbugs"),
        "javac": check_tool_installed("javac"),
    }


def check_cpp_tools() -> Dict[str, bool]:
    """检查 C/C++ 工具"""
    return {
        "cppcheck": check_tool_installed("cppcheck"),
        "clang-tidy": check_tool_installed("clang-tidy"),
    }


def check_go_tools() -> Dict[str, bool]:
    """检查 Go 工具"""
    return {
        "go": check_tool_installed("go"),
        "golint": check_tool_installed("golint"),
        "staticcheck": check_tool_installed("staticcheck"),
    }


def check_rust_tools() -> Dict[str, bool]:
    """检查 Rust 工具"""
    return {
        "cargo": check_tool_installed("cargo"),
        "clippy": check_tool_installed("cargo-clippy"),
    }


def check_android_tools() -> Dict[str, bool]:
    """检查 Android 工具"""
    import os
    android_home = os.environ.get("ANDROID_HOME", "")
    lint_paths = [
        f"{android_home}/tools/bin/lint",
        f"{android_home}/cmdline-tools/latest/bin/lint",
    ]
    lint_exists = any(os.path.exists(p) for p in lint_paths)
    return {
        "android-lint": lint_exists,
        "ktlint": check_tool_installed("ktlint"),
    }


def check_all_tools() -> Dict[str, Dict[str, bool]]:
    """检查所有语言的工具"""
    return {
        "python": check_python_tools(),
        "javascript": check_javascript_tools(),
        "java": check_java_tools(),
        "cpp": check_cpp_tools(),
        "go": check_go_tools(),
        "rust": check_rust_tools(),
        "android": check_android_tools(),
    }


def get_missing_tools() -> Dict[str, List[str]]:
    """获取缺失的工具列表"""
    missing = {}
    all_tools = check_all_tools()
    
    for lang, tools in all_tools.items():
        missing_list = [name for name, installed in tools.items() if not installed]
        if missing_list:
            missing[lang] = missing_list
    
    return missing