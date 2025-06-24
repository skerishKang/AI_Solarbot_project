# AI_Solarbot 실행 스크립트 (PowerShell)
# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   🤖 AI_Solarbot 시작 중..." -ForegroundColor Yellow
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리 확인
Write-Host "📁 현재 위치: $PWD" -ForegroundColor Green
Write-Host ""

# 가상환경 활성화
Write-Host "🔄 가상환경 활성화 중..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
    Write-Host "✅ 가상환경 활성화 완료!" -ForegroundColor Green
} else {
    Write-Host "❌ 가상환경을 찾을 수 없습니다!" -ForegroundColor Red
    Write-Host "💡 venv 폴더가 있는지 확인해주세요." -ForegroundColor Yellow
    Read-Host "계속하려면 Enter를 누르세요"
    exit 1
}
Write-Host ""

# Python 버전 확인
Write-Host "🐍 Python 버전:" -ForegroundColor Cyan
python --version
Write-Host ""

# 필요한 패키지 확인
Write-Host "📦 필요한 패키지 확인 중..." -ForegroundColor Yellow
$telegramCheck = pip list | Select-String "telegram"
if (-not $telegramCheck) {
    Write-Host "⚠️  텔레그램 패키지가 없습니다. 설치 중..." -ForegroundColor Yellow
    pip install -r requirements.txt
}
Write-Host "✅ 패키지 확인 완료!" -ForegroundColor Green
Write-Host ""

# 봇 실행
Write-Host "🚀 AI_Solarbot 실행 중..." -ForegroundColor Yellow
Write-Host "💡 봇을 종료하려면 Ctrl+C를 누르세요." -ForegroundColor Cyan
Write-Host ""
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   봇이 실행되었습니다!" -ForegroundColor Green
Write-Host "   텔레그램에서 @AI_Solarbot 검색" -ForegroundColor Yellow
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

try {
    python src/bot.py
}
catch {
    Write-Host "❌ 봇 실행 중 오류가 발생했습니다: $_" -ForegroundColor Red
}
finally {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Cyan
    Write-Host "   🛑 AI_Solarbot이 종료되었습니다." -ForegroundColor Red
    Write-Host "====================================" -ForegroundColor Cyan
    Read-Host "계속하려면 Enter를 누르세요"
}
