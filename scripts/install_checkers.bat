@echo off
echo 安装 Python 工具...
pip install pylint flake8 bandit radon

echo.
echo 安装 JavaScript 工具...
call npm install -g eslint

echo.
echo 安装 Go 工具...
go install golang.org/x/lint/golint@latest
go install honnef.co/go/tools/cmd/staticcheck@latest

echo.
echo 全部安装完成！
pause