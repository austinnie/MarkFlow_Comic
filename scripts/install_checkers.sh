#!/bin/bash
# 安装所有代码审查工具

echo "安装 Python 工具..."
pip install pylint flake8 bandit radon

echo ""
echo "安装 JavaScript 工具..."
npm install -g eslint

echo ""
echo "安装 C/C++ 工具..."
# Windows 使用 choco
choco install cppcheck
# Linux 使用 apt
# sudo apt install cppcheck clang-tidy

echo ""
echo "安装 Go 工具..."
go install golang.org/x/lint/golint@latest
go install honnef.co/go/tools/cmd/staticcheck@latest

echo ""
echo "安装 Rust 工具..."
rustup component add clippy

echo ""
echo "全部安装完成！"