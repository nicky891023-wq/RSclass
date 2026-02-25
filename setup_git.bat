@echo off
echo Initializing Git repository...
git init

echo Adding files...
git add .

echo Creating initial commit...
git commit -m "Initial commit: AQI Analysis Project"

echo Creating GitHub repository...
gh repo create aqi-analysis --public --source=. --remote=origin --push

echo Done!
pause
