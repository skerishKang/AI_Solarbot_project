@echo off
chcp 65001 > nul
title AI_Solarbot v2.0

echo.
echo 🤖 AI_Solarbot v2.0 시작
echo =====================================
echo.

REM 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    echo 📦 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo ❌ 가상환경을 찾을 수 없습니다!
    echo venv 폴더를 확인해주세요.
    pause
    exit /b 1
)

REM Python 스크립트 실행
echo 🚀 봇 시작 중...
python start_bot.py

echo.
echo 🛑 봇이 종료되었습니다.
pause 