@echo off
chcp 65001 > nul
title AI_Solarbot 실행기

echo.
echo ====================================
echo    🤖 AI_Solarbot 시작 중...
echo ====================================
echo.

:: 현재 디렉토리 확인
echo 📁 현재 위치: %CD%
echo.

:: 가상환경 활성화
echo 🔄 가상환경 활성화 중...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패!
    echo 💡 venv 폴더가 있는지 확인해주세요.
    pause
    exit /b 1
)
echo ✅ 가상환경 활성화 완료!
echo.

:: Python 버전 확인
echo 🐍 Python 버전:
python --version
echo.

:: 필요한 패키지 설치 확인
echo 📦 필요한 패키지 확인 중...
pip list | findstr "telegram" > nul
if errorlevel 1 (
    echo ⚠️  텔레그램 패키지가 없습니다. 설치 중...
    pip install -r requirements.txt
)
echo ✅ 패키지 확인 완료!
echo.

:: 봇 실행
echo 🚀 AI_Solarbot 실행 중...
echo 💡 봇을 종료하려면 Ctrl+C를 누르세요.
echo.
echo ====================================
echo    봇이 실행되었습니다!
echo    텔레그램에서 @AI_Solarbot 검색
echo ====================================
echo.

python src/bot.py

:: 봇 종료 시 메시지
echo.
echo ====================================
echo    🛑 AI_Solarbot이 종료되었습니다.
echo ====================================
pause 