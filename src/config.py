"""
팜솔라 AI_Solarbot 설정 관리
모든 하드코딩된 값들을 중앙 집중식으로 관리
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class BotConfig:
    """봇 설정 클래스"""
    
    # API 설정
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # AI 엔진 설정
    GEMINI_DAILY_LIMIT = int(os.getenv('GEMINI_DAILY_LIMIT', '1400'))
    GEMINI_SWITCH_THRESHOLD = float(os.getenv('GEMINI_SWITCH_THRESHOLD', '0.95'))  # 95%
    DEFAULT_AI_MODEL = os.getenv('DEFAULT_AI_MODEL', 'gemini-2.0-flash-exp')
    
    # 성능 설정
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '3000'))
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '50'))
    CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '7200'))  # 2시간
    
    # 태양광 계산 설정
    DEFAULT_SOLAR_EFFICIENCY = float(os.getenv('DEFAULT_SOLAR_EFFICIENCY', '1300'))  # kWh/kW/year
    DEFAULT_ELECTRICITY_PRICE = float(os.getenv('DEFAULT_ELECTRICITY_PRICE', '150'))  # 원/kWh
    
    # 보안 설정
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    ADMIN_USER_ID = os.getenv('ADMIN_USER_ID')
    
    # 파일 경로 설정
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
    LOGS_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
    BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'backups')
    
    # Google Drive 설정
    DRIVE_FOLDER_NAME = "팜솔라_AI관리_시스템"
    USAGE_FILE_NAME = "usage_tracker.json"
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """모든 설정을 딕셔너리로 반환"""
        return {
            'gemini_daily_limit': cls.GEMINI_DAILY_LIMIT,
            'gemini_switch_threshold': cls.GEMINI_SWITCH_THRESHOLD,
            'max_content_length': cls.MAX_CONTENT_LENGTH,
            'max_file_size_mb': cls.MAX_FILE_SIZE_MB,
            'cache_ttl_seconds': cls.CACHE_TTL_SECONDS,
            'default_solar_efficiency': cls.DEFAULT_SOLAR_EFFICIENCY,
            'default_electricity_price': cls.DEFAULT_ELECTRICITY_PRICE,
            'log_level': cls.LOG_LEVEL,
            'data_dir': cls.DATA_DIR,
            'logs_dir': cls.LOGS_DIR,
            'backup_dir': cls.BACKUP_DIR
        }
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """설정 유효성 검사"""
        validation_results = {}
        
        # 필수 API 키 확인
        validation_results['telegram_token'] = bool(cls.TELEGRAM_BOT_TOKEN)
        validation_results['gemini_key'] = bool(cls.GEMINI_API_KEY)
        validation_results['openai_key'] = bool(cls.OPENAI_API_KEY)
        
        # 숫자 설정 범위 확인
        validation_results['gemini_limit_valid'] = 100 <= cls.GEMINI_DAILY_LIMIT <= 10000
        validation_results['threshold_valid'] = 0.1 <= cls.GEMINI_SWITCH_THRESHOLD <= 1.0
        validation_results['content_length_valid'] = 500 <= cls.MAX_CONTENT_LENGTH <= 50000
        
        return validation_results
