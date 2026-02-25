@echo off
echo 正在上傳到 nicky891023-wq/AQI_analysis...

echo 設定 Git 使用者身份...
git config user.email "nicky891023@gmail.com"
git config user.name "nicky891023-wq"

echo 初始化 Git 倉庫...
git init

echo 設定遠端倉庫...
git remote add origin https://github.com/nicky891023-wq/AQI_analysis.git

echo 添加所有檔案...
git add .

echo 提交變更...
git commit -m "Initial commit: AQI Analysis Project with real-time air quality monitoring"

echo 推送到 GitHub...
git push -u origin main

echo 上傳完成！
pause
