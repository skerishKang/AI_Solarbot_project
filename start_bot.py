#!/usr/bin/env python3
"""
AI_Solarbot 시작 스크립트
- 환경 확인
- 필수 파일 체크
- 봇 실행
"""

import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인 중...")
    
    # .env 파일 확인
    env_files = [
        Path("config/.env"),
        Path(".env"),
        Path("src/.env")
    ]
    
    env_found = False
    for env_file in env_files:
        if env_file.exists():
            print(f"✅ 환경 파일 발견: {env_file}")
            env_found = True
            break
    
    if not env_found:
        print("❌ .env 파일을 찾을 수 없습니다!")
        print("다음 중 하나의 위치에 .env 파일을 생성해주세요:")
        for env_file in env_files:
            print(f"  - {env_file}")
        print("\n필요한 환경변수:")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token")
        print("  GEMINI_API_KEY=your_gemini_key")
        print("  OPENAI_API_KEY=your_openai_key")
        return False
    
    return True

def check_dependencies():
    """필수 패키지 확인"""
    print("📦 패키지 설치 확인 중...")
    
    required_packages = [
        'telegram',
        'openai', 
        'google.generativeai',
        'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            else:
                __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n누락된 패키지: {', '.join(missing_packages)}")
        print("다음 명령어로 설치하세요:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def start_bot():
    """봇 시작"""
    print("🚀 AI_Solarbot 시작 중...")
    
    # src 디렉토리로 이동
    src_path = Path("src")
    if not src_path.exists():
        print("❌ src 디렉토리를 찾을 수 없습니다!")
        return False
    
    # bot.py 실행
    bot_file = src_path / "bot.py"
    if not bot_file.exists():
        print("❌ bot.py 파일을 찾을 수 없습니다!")
        return False
    
    try:
        os.chdir(src_path)
        subprocess.run([sys.executable, "bot.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 봇 실행 중 오류 발생: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 봇 종료됨")
        return True
    
    return True

def main():
    """메인 함수"""
    print("🤖 AI_Solarbot v2.0 시작 스크립트")
    print("=" * 50)
    
    # 환경 확인
    if not check_environment():
        sys.exit(1)
    
    # 패키지 확인
    if not check_dependencies():
        sys.exit(1)
    
    print("\n✅ 모든 검사 완료!")
    print("🚀 봇을 시작합니다...\n")
    
    # 봇 시작
    if not start_bot():
        sys.exit(1)

if __name__ == "__main__":
    main() 