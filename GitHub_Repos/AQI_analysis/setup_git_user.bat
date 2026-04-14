@echo off
echo Setting up Git user configuration...

REM 設定全域 Git 配置
git config --global user.email "nicky891023@gmail.com"
git config --global user.name "nicky891023-wq"

echo Configuration set. Testing...
git config --global user.email
git config --global user.name

echo Done!
pause
