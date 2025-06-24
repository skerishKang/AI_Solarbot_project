#!/usr/bin/env python3
"""
환경변수 로딩 테스트 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent
print(f"🔍 프로젝트 루트: {project_root}")
print(f"📁 현재 작업 디렉토리: {os.getcwd()}")

# .env 파일 존재 확인
env_file = project_root / ".env"
print(f"📄 .env 파일 위치: {env_file}")
print(f"📄 .env 파일 존재: {env_file.exists()}")

if env_file.exists():
    print(f"📏 .env 파일 크기: {env_file.stat().st_size} bytes")

# python-dotenv 패키지 확인
try:
    from dotenv import load_dotenv
    print("✅ python-dotenv 패키지 로딩 성공")
    
    # .env 파일 로딩
    print("\n🔄 .env 파일 로딩 중...")
    result = load_dotenv(env_file)
    print(f"📥 로딩 결과: {result}")
    
    # 환경변수 확인
    print("\n🧪 환경변수 테스트:")
    
    # 필수 환경변수들
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "ADMIN_USER_ID", 
        "BOT_USERNAME",
        "OFFLINE_MODE"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 토큰은 앞부분만 표시
            if "TOKEN" in var or "KEY" in var:
                display_value = f"{value[:10]}..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: 없음")
    
    # 선택적 환경변수들
    optional_vars = [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "ENCRYPTION_KEY"
    ]
    
    print("\n🔧 선택적 환경변수:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if value.startswith("your_") or value.startswith("sk-"):
                display_value = f"{value[:15]}..." if len(value) > 15 else value
            else:
                display_value = value
            print(f"⚙️ {var}: {display_value}")
        else:
            print(f"⚠️ {var}: 기본값 사용")
    
    print("\n" + "="*50)
    
    # TELEGRAM_BOT_TOKEN 상세 확인
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if bot_token:
        print("🤖 텔레그램 봇 토큰 상세 정보:")
        print(f"   길이: {len(bot_token)} 문자")
        
        # 토큰 형식 검증
        if ':' in bot_token:
            bot_id, token_part = bot_token.split(':', 1)
            print(f"   봇 ID: {bot_id}")
            print(f"   토큰 부분 길이: {len(token_part)} 문자")
            
            # 간단한 API 테스트
            print("\n🌐 텔레그램 API 연결 테스트:")
            try:
                import requests
                url = f"https://api.telegram.org/bot{bot_token}/getMe"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    bot_info = response.json()
                    if bot_info.get('ok'):
                        result = bot_info.get('result', {})
                        print(f"✅ API 연결 성공!")
                        print(f"   봇 이름: {result.get('first_name', 'N/A')}")
                        print(f"   봇 사용자명: @{result.get('username', 'N/A')}")
                        print(f"   봇 ID: {result.get('id', 'N/A')}")
                    else:
                        print(f"❌ API 응답 오류: {bot_info}")
                else:
                    print(f"❌ HTTP 오류: {response.status_code}")
                    print(f"   응답: {response.text}")
                    
            except ImportError:
                print("⚠️ requests 모듈 없음 - API 테스트 스킵")
            except Exception as e:
                print(f"❌ API 테스트 실패: {e}")
        else:
            print("❌ 토큰 형식이 올바르지 않습니다 (':' 없음)")
    else:
        print("❌ 텔레그램 봇 토큰이 없습니다!")
    
    print("\n" + "="*50)
    print("🎯 결론:")
    
    # 시작 가능 여부 판단
    can_start_online = bool(bot_token and os.getenv('ADMIN_USER_ID'))
    can_start_offline = True  # 오프라인은 항상 가능
    
    if can_start_online:
        print("✅ 온라인 모드로 봇 시작 가능")
    else:
        print("⚠️ 온라인 모드 시작 불가 - 필수 환경변수 부족")
    
    if can_start_offline:
        print("✅ 오프라인 모드로 시스템 테스트 가능")
    
    # 권장사항
    print("\n💡 권장사항:")
    if not bot_token or bot_token.startswith("your_"):
        print("   1. 유효한 텔레그램 봇 토큰 설정 필요")
    if not os.getenv('ADMIN_USER_ID') or os.getenv('ADMIN_USER_ID') == "your_admin_id":
        print("   2. 관리자 사용자 ID 설정 필요")
    if os.getenv('OFFLINE_MODE', 'false').lower() == 'true':
        print("   3. 현재 OFFLINE_MODE 활성화됨")
    
except ImportError:
    print("❌ python-dotenv 패키지를 찾을 수 없습니다")
    print("💡 설치: pip install python-dotenv")
    sys.exit(1)
except Exception as e:
    print(f"❌ 환경변수 로딩 오류: {e}")
    sys.exit(1)
