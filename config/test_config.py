"""
테스트 환경 설정 파일
OFFLINE_MODE 지원 및 외부 서비스 의존성 관리
"""

import os
from typing import Dict, Any

# 환경 변수에서 OFFLINE_MODE 읽기
OFFLINE_MODE = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'

# 테스트 설정
TEST_CONFIG = {
    'offline_mode': OFFLINE_MODE,
    'mock_external_services': OFFLINE_MODE,
    'skip_integration_tests': OFFLINE_MODE,
    'use_test_data': True,
    'test_timeout': 30,
    'max_test_duration': 300,  # 5분
}

# 모킹할 외부 서비스 목록
EXTERNAL_SERVICES = [
    'google.oauth2',
    'googleapiclient',
    'openai',
    'google.generativeai',
    'selenium',
    'playwright',
    'requests',
    'aiohttp'
]

# 오프라인 모드에서 사용할 더미 데이터
MOCK_DATA = {
    'sample_url': 'https://example.com/test-article',
    'sample_content': '''
    # 테스트 기사 제목
    
    이것은 테스트용 샘플 콘텐츠입니다. 
    감정 분석과 품질 평가를 위한 예시 텍스트가 포함되어 있습니다.
    
    ## 주요 내용
    - 긍정적인 내용: 이 제품은 정말 훌륭합니다!
    - 부정적인 내용: 하지만 몇 가지 문제점이 있습니다.
    - 중립적인 내용: 객관적인 정보를 제공합니다.
    
    ## 결론
    전반적으로 균형잡힌 시각을 제공하는 좋은 콘텐츠입니다.
    ''',
    'sample_analysis_result': {
        'sentiment': {
            'overall': 'positive',
            'score': 0.65,
            'confidence': 0.8,
            'emotions': {
                'joy': 0.4,
                'trust': 0.3,
                'surprise': 0.1,
                'fear': 0.05,
                'anger': 0.05,
                'sadness': 0.05,
                'disgust': 0.03,
                'anticipation': 0.02
            }
        },
        'quality': {
            'overall_score': 78.5,
            'grade': 'B',
            'dimensions': {
                'reliability': 75.0,
                'usefulness': 82.0,
                'accuracy': 80.0,
                'completeness': 77.0,
                'readability': 85.0,
                'originality': 72.0
            }
        }
    }
}

def get_test_config() -> Dict[str, Any]:
    """테스트 설정 반환"""
    return TEST_CONFIG.copy()

def is_offline_mode() -> bool:
    """오프라인 모드 여부 확인"""
    return OFFLINE_MODE

def get_mock_data(key: str) -> Any:
    """모킹 데이터 반환"""
    return MOCK_DATA.get(key)

def should_skip_external_test(test_name: str) -> bool:
    """외부 서비스 테스트 스킵 여부 결정"""
    if not OFFLINE_MODE:
        return False
    
    # 외부 서비스 관련 테스트 패턴
    external_patterns = [
        'google', 'drive', 'gmail', 'api',
        'openai', 'gemini', 'ai_model',
        'selenium', 'playwright', 'browser',
        'requests', 'http', 'web'
    ]
    
    test_name_lower = test_name.lower()
    return any(pattern in test_name_lower for pattern in external_patterns)

def setup_test_environment():
    """테스트 환경 초기 설정"""
    if OFFLINE_MODE:
        print("🔧 OFFLINE_MODE 활성화 - 외부 서비스 모킹 시작")
        _setup_mocks()
    else:
        print("🌐 ONLINE_MODE - 실제 외부 서비스 연결")

def _setup_mocks():
    """외부 서비스 모킹 설정"""
    try:
        import unittest.mock as mock
        
        # Google API 모킹
        mock.patch('googleapiclient.discovery.build').start()
        mock.patch('google.oauth2.service_account.Credentials.from_service_account_file').start()
        
        # AI 모델 모킹
        mock.patch('openai.ChatCompletion.create').start()
        mock.patch('google.generativeai.generate_text').start()
        
        # 웹 요청 모킹
        mock.patch('requests.get').start()
        mock.patch('requests.post').start()
        
        print("✅ 외부 서비스 모킹 완료")
        
    except ImportError:
        print("⚠️ unittest.mock을 사용할 수 없습니다")

def cleanup_test_environment():
    """테스트 환경 정리"""
    if OFFLINE_MODE:
        try:
            import unittest.mock as mock
            mock.patch.stopall()
            print("🧹 모킹 정리 완료")
        except ImportError:
            pass

# 테스트 데코레이터
def skip_if_offline(test_func):
    """오프라인 모드에서 테스트 스킵하는 데코레이터"""
    import unittest
    
    if OFFLINE_MODE:
        return unittest.skip("OFFLINE_MODE에서 스킵됨")(test_func)
    return test_func

def mock_if_offline(mock_return_value=None):
    """오프라인 모드에서 모킹하는 데코레이터"""
    def decorator(test_func):
        if OFFLINE_MODE:
            import unittest.mock as mock
            return mock.patch.object(test_func, '__call__', return_value=mock_return_value)
        return test_func
    return decorator 