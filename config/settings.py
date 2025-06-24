"""
AI_Solarbot 프로젝트 설정
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

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

# 파일 경로 설정 (클라우드 기반)
PATHS = {
    'SRC_DIR': PROJECT_ROOT / 'src',
    'LOGS_DIR': PROJECT_ROOT / 'logs',
    # 로컬 데이터 파일 경로 제거됨 - 모든 데이터는 구글 드라이브에 저장
}

# 교과서 설정 (클라우드 기반)
TEXTBOOK_CONFIG = {
    'WEEK_FORMAT': "{week}주차{lesson}번째",
    'MAX_WEEKS': 12,
    'LESSONS_PER_WEEK': 2,
    # 로컬 BASE_PATH 제거됨 - 교과서는 구글 드라이브에서 관리
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

# 기본 설정
PROJECT_NAME = "AI_Solarbot"
VERSION = "2.0.0"
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')  # development, staging, production
OFFLINE_MODE = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, 'src')
DATA_DIR = os.path.join(BASE_DIR, 'data')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')

# 로그 설정
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# 텔레그램 봇 설정
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
BOT_USERNAME = os.getenv('BOT_USERNAME', 'AI_Solarbot')

# AI 모델 설정
AI_MODEL_CONFIG = {
    'gemini': {
        'api_key': os.getenv('GEMINI_API_KEY', ''),
        'model_name': 'gemini-pro',
        'max_tokens': 8192,
        'temperature': 0.7,
        'timeout': 30
    },
    'chatgpt': {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        'model_name': 'gpt-3.5-turbo',
        'max_tokens': 4096,
        'temperature': 0.7,
        'timeout': 30
    }
}

# 구글 서비스 설정
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH', '')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')

# 성능 최적화 설정
PERFORMANCE_CONFIG = {
    # 캐시 설정
    'cache': {
        'max_size': 1000,  # 최대 캐시 항목 수
        'ttl': 3600,  # TTL: 1시간 (초)
        'cleanup_interval': 300,  # 정리 주기: 5분
        'enable_memory_cache': True,
        'enable_disk_cache': False
    },
    
    # 메모리 관리
    'memory': {
        'max_memory_usage': 512 * 1024 * 1024,  # 512MB
        'gc_threshold': 0.8,  # 80% 사용 시 가비지 컬렉션
        'enable_memory_monitoring': True
    },
    
    # 처리 한계
    'limits': {
        'max_content_length': 100000,  # 최대 콘텐츠 길이 (문자)
        'max_concurrent_requests': 10,  # 최대 동시 요청
        'max_analysis_time': 30,  # 최대 분석 시간 (초)
        'max_batch_size': 5  # 일괄 처리 최대 크기
    },
    
    # 최적화 옵션
    'optimization': {
        'enable_parallel_processing': True,
        'enable_result_caching': True,
        'enable_precompiled_patterns': True,
        'enable_lazy_loading': True
    }
}

# 지능형 콘텐츠 분석 설정
CONTENT_ANALYSIS_CONFIG = {
    # 기본 분석 설정
    'default_language': 'ko',
    'enable_advanced_analysis': True,
    'enable_ai_enhancement': not OFFLINE_MODE,
    
    # 감정 분석 설정
    'sentiment': {
        'enable_plutchik_model': True,
        'enable_korean_keywords': True,
        'confidence_threshold': 0.5,
        'emotion_threshold': 0.1
    },
    
    # 품질 평가 설정
    'quality': {
        'dimensions': ['reliability', 'usefulness', 'accuracy', 'completeness', 'readability', 'originality'],
        'grading_scale': {
            'A+': 95, 'A': 90, 'A-': 85,
            'B+': 80, 'B': 75, 'B-': 70,
            'C+': 65, 'C': 60, 'C-': 55,
            'D+': 50, 'D': 45, 'F': 0
        },
        'min_score_threshold': 30
    },
    
    # AI 통합 설정
    'ai_integration': {
        'enable_ai_sentiment': not OFFLINE_MODE,
        'enable_ai_quality': not OFFLINE_MODE,
        'ai_cache_ttl': 7200,  # 2시간
        'fallback_to_rule_based': True,
        'merge_strategies': {
            'sentiment': 'weighted_average',  # weighted_average, max_confidence, consensus
            'quality': 'weighted_average'
        },
        'ai_weight': 0.6,  # AI 결과 가중치
        'rule_based_weight': 0.4  # Rule-based 결과 가중치
    }
}

# 보안 설정
SECURITY_CONFIG = {
    'enable_rate_limiting': True,
    'max_requests_per_minute': 60,
    'enable_input_validation': True,
    'max_input_length': 10000,
    'allowed_content_types': ['text/html', 'text/plain', 'application/json'],
    'blocked_domains': [],
    'enable_content_filtering': True
}

# 데이터베이스 설정 (SQLite 기본)
DATABASE_CONFIG = {
    'type': 'sqlite',
    'path': os.path.join(DATA_DIR, 'ai_solarbot.db'),
    'enable_foreign_keys': True,
    'enable_wal_mode': True,
    'connection_timeout': 30,
    'max_connections': 10
}

# 웹 검색 설정
WEB_SEARCH_CONFIG = {
    'timeout': 10,
    'max_retries': 3,
    'user_agent': 'AI_Solarbot/2.0 (+https://example.com/bot)',
    'max_content_size': 1024 * 1024,  # 1MB
    'enable_javascript': False,
    'follow_redirects': True,
    'max_redirects': 5
}

# 모니터링 설정
MONITORING_CONFIG = {
    'enable_performance_monitoring': True,
    'enable_error_tracking': True,
    'enable_usage_analytics': True,
    'metrics_retention_days': 30,
    'alert_thresholds': {
        'error_rate': 0.05,  # 5% 오류율
        'response_time': 5.0,  # 5초 응답 시간
        'memory_usage': 0.9   # 90% 메모리 사용
    }
}

# 기능 플래그
FEATURE_FLAGS = {
    'enable_advanced_sentiment': True,
    'enable_quality_evaluation': True,
    'enable_ai_integration': not OFFLINE_MODE,
    'enable_batch_processing': True,
    'enable_real_time_analysis': True,
    'enable_content_comparison': True,
    'enable_performance_optimization': True,
    'enable_auto_scaling': False,
    'enable_experimental_features': ENVIRONMENT == 'development'
}

def get_config(section: str, key: Optional[str] = None) -> Any:
    """설정 값 조회"""
    config_map = {
        'performance': PERFORMANCE_CONFIG,
        'content_analysis': CONTENT_ANALYSIS_CONFIG,
        'security': SECURITY_CONFIG,
        'database': DATABASE_CONFIG,
        'web_search': WEB_SEARCH_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'features': FEATURE_FLAGS,
        'ai_models': AI_MODEL_CONFIG
    }
    
    if section not in config_map:
        raise ValueError(f"Unknown config section: {section}")
    
    config = config_map[section]
    
    if key is None:
        return config
    
    if key not in config:
        raise ValueError(f"Unknown config key '{key}' in section '{section}'")
    
    return config[key]

def update_config(section: str, key: str, value: Any) -> None:
    """설정 값 업데이트 (런타임)"""
    config_map = {
        'performance': PERFORMANCE_CONFIG,
        'content_analysis': CONTENT_ANALYSIS_CONFIG,
        'security': SECURITY_CONFIG,
        'database': DATABASE_CONFIG,
        'web_search': WEB_SEARCH_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'features': FEATURE_FLAGS,
        'ai_models': AI_MODEL_CONFIG
    }
    
    if section not in config_map:
        raise ValueError(f"Unknown config section: {section}")
    
    config = config_map[section]
    
    if key not in config:
        raise ValueError(f"Unknown config key '{key}' in section '{section}'")
    
    config[key] = value

def is_feature_enabled(feature_name: str) -> bool:
    """기능 플래그 확인"""
    return FEATURE_FLAGS.get(feature_name, False)

def get_performance_config() -> Dict[str, Any]:
    """성능 설정 조회"""
    return PERFORMANCE_CONFIG.copy()

def get_analysis_config() -> Dict[str, Any]:
    """분석 설정 조회"""
    return CONTENT_ANALYSIS_CONFIG.copy()

# 환경별 설정 조정
if ENVIRONMENT == 'production':
    # 프로덕션 환경에서는 더 엄격한 설정
    PERFORMANCE_CONFIG['limits']['max_concurrent_requests'] = 20
    SECURITY_CONFIG['max_requests_per_minute'] = 120
    MONITORING_CONFIG['enable_performance_monitoring'] = True
    
elif ENVIRONMENT == 'development':
    # 개발 환경에서는 디버깅을 위한 설정
    LOG_LEVEL = 'DEBUG'
    FEATURE_FLAGS['enable_experimental_features'] = True
    PERFORMANCE_CONFIG['cache']['ttl'] = 60  # 1분으로 단축

# OFFLINE_MODE에서의 설정 조정
if OFFLINE_MODE:
    # 외부 서비스 관련 기능 비활성화
    CONTENT_ANALYSIS_CONFIG['ai_integration']['enable_ai_sentiment'] = False
    CONTENT_ANALYSIS_CONFIG['ai_integration']['enable_ai_quality'] = False
    FEATURE_FLAGS['enable_ai_integration'] = False
    
    # 캐시 의존도 증가
    PERFORMANCE_CONFIG['cache']['max_size'] = 2000
    PERFORMANCE_CONFIG['cache']['ttl'] = 7200  # 2시간

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
    
    # 필요한 디렉토리 생성 (로컬 로그 디렉토리만)
    for path_name, path in PATHS.items():
        if path_name.endswith('_DIR') and isinstance(path, Path):
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