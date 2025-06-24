#!/usr/bin/env python3
"""
간단한 환경변수 확인 스크립트
"""

import os
from pathlib import Path

# 현재 디렉토리 확인
print("=" * 50)
print("환경변수 확인 스크립트")
print("=" * 50)

# .env 파일 위치
env_file = Path(".env")
print(f".env 파일 위치: {env_file.absolute()}")
print(f".env 파일 존재: {env_file.exists()}")

# python-dotenv 로딩
try:
    from dotenv import load_dotenv
    print("python-dotenv 모듈: 설치됨")
    
    # .env 파일 로딩
    result = load_dotenv()
    print(f".env 로딩 결과: {result}")
    
    # 핵심 환경변수 확인
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_id = os.getenv('ADMIN_USER_ID')
    offline_mode = os.getenv('OFFLINE_MODE')
    
    print("\n핵심 환경변수:")
    print(f"TELEGRAM_BOT_TOKEN: {'있음' if bot_token else '없음'}")
    print(f"ADMIN_USER_ID: {admin_id}")
    print(f"OFFLINE_MODE: {offline_mode}")
    
    if bot_token:
        print(f"봇 토큰 길이: {len(bot_token)} 문자")
        print(f"봇 토큰 시작: {bot_token[:20]}...")
        
        # 간단한 API 테스트
        try:
            import requests
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    print(f"\nAPI 테스트: 성공")
                    print(f"봇 이름: {bot_info.get('first_name')}")
                    print(f"사용자명: @{bot_info.get('username')}")
                else:
                    print(f"\nAPI 테스트: 실패 - {data}")
            else:
                print(f"\nAPI 테스트: HTTP {response.status_code}")
        except Exception as e:
            print(f"\nAPI 테스트: 오류 - {e}")
    
    print("\n결론:")
    if bot_token and admin_id:
        print("온라인 모드 시작 가능")
    else:
        print("환경변수 설정 필요")
        
except ImportError:
    print("python-dotenv 모듈: 없음")
    print("pip install python-dotenv 필요")
except Exception as e:
    print(f"오류: {e}")

print("=" * 50)
