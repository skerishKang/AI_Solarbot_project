"""
AI_Solarbot 프로젝트 설정
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent

# .env 파일 로드 (여러 위치에서 찾기)
env_files = [
    PROJECT_ROOT / "config" / ".env",
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "src" / ".env"
]

for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 환경 파일 로드: {env_file}")
        break

# 봇 설정
BOT_CONFIG = {
    'TOKEN': os.getenv('TELEGRAM_BOT_TOKEN'),
    'USERNAME': os.getenv('BOT_USERNAME', 'AI_Solarbot'),
    'ADMIN_USER_ID': os.getenv('ADMIN_USER_ID'),
}

# AI 엔진 설정
AI_CONFIG = {
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'GEMINI_DAILY_LIMIT': 1400,
    'GEMINI_WARNING_THRESHOLD': 0.95,  # 95% 도달시 경고
}

# 파일 경로 설정
PATHS = {
    'SRC_DIR': PROJECT_ROOT / 'src',
    'DATA_DIR': PROJECT_ROOT / 'data',
    'LOGS_DIR': PROJECT_ROOT / 'logs',
    'HOMEWORK_DATA': PROJECT_ROOT / 'src' / 'homework_data.json',
    'USAGE_TRACKER': PROJECT_ROOT / 'src' / 'usage_tracker.json',
}

# 교과서 경로 설정
TEXTBOOK_CONFIG = {
    'BASE_PATH': "G:\\Ddrive\\BatangD\\task\\workdiary\\36. 팜솔라\\수업",
    'WEEK_FORMAT': "{week}주차{lesson}번째",
    'MAX_WEEKS': 12,
    'LESSONS_PER_WEEK': 2,
}

# 태양광 계산 기본값
SOLAR_CONFIG = {
    'DEFAULT_ANGLE': 30,
    'DEFAULT_DIRECTION': '남향',
    'EFFICIENCY_RATE': 0.85,
    'ELECTRICITY_PRICE': 150,  # 원/kWh
    'INSTALLATION_COST_PER_KW': 1500000,  # 원/kW
}

# 로깅 설정
LOGGING_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'FILE_PATH': PATHS['LOGS_DIR'] / 'bot.log',
    'MAX_FILE_SIZE': 10 * 1024 * 1024,  # 10MB
    'BACKUP_COUNT': 5,
}

def validate_config():
    """설정 유효성 검사"""
    errors = []
    
    # 필수 환경변수 확인
    if not BOT_CONFIG['TOKEN']:
        errors.append("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
    
    if not AI_CONFIG['GEMINI_API_KEY']:
        errors.append("GEMINI_API_KEY가 설정되지 않았습니다.")
    
    if not AI_CONFIG['OPENAI_API_KEY']:
        errors.append("OPENAI_API_KEY가 설정되지 않았습니다.")
    
    # 디렉토리 생성
    for path_name, path in PATHS.items():
        if path_name.endswith('_DIR'):
            path.mkdir(exist_ok=True)
    
    return errors

if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("❌ 설정 오류:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✅ 모든 설정이 올바릅니다!") 