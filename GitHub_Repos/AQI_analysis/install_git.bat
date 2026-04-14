@echo off
echo 正在安裝 Git...

echo 下載 Git 安裝程式...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.39.0.windows.2/Git-2.39.0.2-64-bit.exe' -OutFile 'git-installer.exe'"

echo 執行 Git 安裝...
start /wait git-installer.exe /VERYSILENT /NORESTART

echo 正在安裝 GitHub CLI...
powershell -Command "winget install GitHub.cli"

echo 安裝完成！請重新啟動命令提示字元。
pause
