#!/usr/bin/env python3
"""
팜솔라 AI_Solarbot 시작 스크립트
모든 시스템 모듈을 초기화하고 텔레그램 봇을 시작합니다.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

def setup_logging():
    """로깅 설정"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE", "logs/bot.log")
    
    # 로그 디렉토리 생성
    log_dir = Path(log_file).parent
    log_dir.mkdir(exist_ok=True)
    
    # 로깅 포맷 설정
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 파일과 콘솔 모두에 로깅
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

def check_environment():
    """환경 변수 및 설정 확인"""
    logger = logging.getLogger(__name__)
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "GEMINI_API_KEY", 
        "ADMIN_USER_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        logger.error("config/.env 파일을 확인하세요.")
        return False
    
    # 구글 드라이브 인증 파일 확인
    credentials_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "config/google_credentials.json")
    if not Path(credentials_file).exists():
        logger.warning(f"구글 드라이브 인증 파일이 없습니다: {credentials_file}")
        logger.warning("구글 드라이브 기능이 제한될 수 있습니다.")
    
    return True

def initialize_components():
    """시스템 컴포넌트 초기화"""
    logger = logging.getLogger(__name__)
    
    try:
        # 필요한 디렉토리 생성
        directories = ["logs", "data", "backups"]
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
        
        logger.info("✅ 시스템 디렉토리 초기화 완료")
        
        # 암호화 키 생성 (없는 경우)
        if not os.getenv("ENCRYPTION_KEY"):
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            logger.info("🔐 새로운 암호화 키가 생성되었습니다.")
            logger.info("이 키를 .env 파일의 ENCRYPTION_KEY에 저장하세요:")
            logger.info(f"ENCRYPTION_KEY={key.decode()}")
        
        logger.info("✅ 시스템 컴포넌트 초기화 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 시스템 초기화 실패: {e}")
        return False

async def start_bot():
    """AI_Solarbot 시작"""
    logger = logging.getLogger(__name__)
    
    try:
        # 봇 모듈 import
        from bot import main as bot_main
        
        logger.info("🚀 팜솔라 AI_Solarbot 시작")
        logger.info("=" * 50)
        logger.info(f"📅 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🐍 Python 버전: {sys.version}")
        logger.info(f"📁 작업 디렉토리: {os.getcwd()}")
        logger.info(f"🔧 환경: {os.getenv('ENVIRONMENT', 'development')}")
        logger.info(f"🤖 봇 이름: {os.getenv('BOT_NAME', 'AI_Solarbot')}")
        logger.info(f"📊 버전: {os.getenv('BOT_VERSION', '2.0.0')}")
        logger.info("=" * 50)
        
        # 봇 실행
        await bot_main()
        
    except KeyboardInterrupt:
        logger.info("🛑 사용자에 의해 봇이 중지되었습니다.")
    except Exception as e:
        logger.error(f"❌ 봇 실행 중 오류 발생: {e}")
        logger.exception("상세 오류 정보:")
        sys.exit(1)

def main():
    """메인 함수"""
    # 로깅 설정
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # 시작 메시지
        print("🚀 팜솔라 AI_Solarbot 시작 중...")
        print("=" * 50)
        
        # 환경 확인
        if not check_environment():
            sys.exit(1)
        
        # 시스템 초기화
        if not initialize_components():
            sys.exit(1)
        
        # 봇 시작
        logger.info("🤖 텔레그램 봇 연결 중...")
        asyncio.run(start_bot())
        
    except KeyboardInterrupt:
        print("\n🛑 봇이 중지되었습니다.")
        logger.info("봇이 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 치명적 오류: {e}")
        logger.error(f"치명적 오류로 봇이 종료됩니다: {e}")
        logger.exception("상세 오류 정보:")
        sys.exit(1)

if __name__ == "__main__":
    main() 