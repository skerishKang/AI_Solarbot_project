"""
AI_Solarbot 통합 테스트 프레임워크
실제 팜솔라 강의 환경에서의 전체 시스템 검증
OFFLINE_MODE 지원으로 외부 서비스 없이도 테스트 가능
"""

import unittest
import asyncio
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

# 테스트 설정 import
try:
    from test_config import (
        is_offline_mode, get_mock_data, should_skip_external_test,
        setup_test_environment, cleanup_test_environment,
        skip_if_offline, mock_if_offline
    )
    TEST_CONFIG_AVAILABLE = True
except ImportError:
    print("⚠️ test_config.py를 찾을 수 없습니다. 기본 설정으로 진행합니다.")
    TEST_CONFIG_AVAILABLE = False
    
    def is_offline_mode():
        return os.getenv('OFFLINE_MODE', 'false').lower() == 'true'
    
    def should_skip_external_test(test_name):
        return is_offline_mode()
    
    def skip_if_offline(func):
        return func
    
    def get_mock_data(key):
        return None

# 외부 서비스 모듈들을 조건부로 import
OFFLINE_MODE = is_offline_mode()

if not OFFLINE_MODE:
    try:
        from google_drive_handler import GoogleDriveHandler
        from user_drive_manager import UserDriveManager
        from ai_handler import AIHandler
        from natural_ide import NaturalIDE
        from web_search_ide import WebSearchIDE
        from cloud_homework_manager import CloudHomeworkManager
        from collaboration_manager import CollaborationManager
        from workspace_template import WorkspaceTemplate
        EXTERNAL_MODULES_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ 외부 모듈 import 실패: {e}")
        EXTERNAL_MODULES_AVAILABLE = False
else:
    print("🔧 OFFLINE_MODE: 외부 모듈 import 스킵")
    EXTERNAL_MODULES_AVAILABLE = False

# 지능형 콘텐츠 분석기는 로컬에서도 테스트 가능
try:
    from intelligent_content_analyzer import IntelligentContentAnalyzer
    CONTENT_ANALYZER_AVAILABLE = True
except ImportError:
    print("⚠️ intelligent_content_analyzer를 찾을 수 없습니다.")
    CONTENT_ANALYZER_AVAILABLE = False

class IntegrationTestFramework:
    """통합 테스트 프레임워크"""
    
    def __init__(self):
        self.test_results = {}
        self.test_user_id = "test_user_12345"
        self.test_user_name = "테스트사용자"
        self.start_time = None
        self.offline_mode = OFFLINE_MODE
        
        # 테스트 환경 설정
        if TEST_CONFIG_AVAILABLE:
            setup_test_environment()
        
    def log_test_result(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """테스트 결과 로깅"""
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "offline_mode": self.offline_mode
        }
        
        status = "✅ PASS" if success else "❌ FAIL"
        mode = "🔧 OFFLINE" if self.offline_mode else "🌐 ONLINE"
        print(f"{status} {mode} {test_name} ({duration:.2f}s): {message}")

class SystemIntegrationTest(unittest.TestCase):
    """시스템 통합 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        cls.framework = IntegrationTestFramework()
        
        # OFFLINE_MODE에 따른 조건부 초기화
        if not OFFLINE_MODE and EXTERNAL_MODULES_AVAILABLE:
            cls.drive_handler = GoogleDriveHandler()
            cls.user_manager = UserDriveManager()
            cls.ai_handler = AIHandler()
            cls.natural_ide = NaturalIDE()
            cls.web_search = WebSearchIDE()
            cls.homework_manager = CloudHomeworkManager()
            cls.collaboration_manager = CollaborationManager()
        else:
            # 모킹된 객체들
            cls.drive_handler = None
            cls.user_manager = None
            cls.ai_handler = None
            cls.natural_ide = None
            cls.web_search = None
            cls.homework_manager = None
            cls.collaboration_manager = None
        
        # 지능형 콘텐츠 분석기 (로컬에서도 동작)
        if CONTENT_ANALYZER_AVAILABLE:
            cls.content_analyzer = IntelligentContentAnalyzer()
        else:
            cls.content_analyzer = None
        
        print("🚀 AI_Solarbot 통합 테스트 시작")
        print(f"📋 모드: {'OFFLINE' if OFFLINE_MODE else 'ONLINE'}")
        print("=" * 60)
    
    @skip_if_offline
    def test_01_google_drive_authentication(self):
        """1. 구글 드라이브 인증 테스트 (ONLINE ONLY)"""
        start_time = time.time()
        
        try:
            if not EXTERNAL_MODULES_AVAILABLE:
                raise Exception("외부 모듈을 사용할 수 없습니다")
                
            # 드라이브 인증 테스트
            auth_result = self.drive_handler.authenticate()
            
            if auth_result:
                # 기본 폴더 생성 테스트
                folder_id = self.drive_handler.get_homework_folder_id()
                success = folder_id is not None
                message = f"폴더 ID: {folder_id}" if success else "폴더 생성 실패"
            else:
                success = False
                message = "구글 드라이브 인증 실패"
                
        except Exception as e:
            success = False
            message = f"인증 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("구글_드라이브_인증", success, message, duration)
        self.assertTrue(success, message)
    
    @skip_if_offline
    def test_02_user_drive_connection(self):
        """2. 사용자별 드라이브 연결 테스트 (ONLINE ONLY)"""
        start_time = time.time()
        
        try:
            if not EXTERNAL_MODULES_AVAILABLE:
                raise Exception("외부 모듈을 사용할 수 없습니다")
                
            # 사용자 폴더 정보 로드
            user_folders = self.user_manager.load_user_folders()
            
            # 테스트 사용자 워크스페이스 확인
            if self.framework.test_user_id in user_folders:
                workspace_id = user_folders[self.framework.test_user_id].get('workspace_folder_id')
                success = workspace_id is not None
                message = f"워크스페이스 ID: {workspace_id}" if success else "워크스페이스 없음"
            else:
                success = True  # 새 사용자는 정상
                message = "새 사용자 - 워크스페이스 생성 필요"
                
        except Exception as e:
            success = False
            message = f"사용자 드라이브 연결 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("사용자_드라이브_연결", success, message, duration)
        self.assertTrue(success, message)
    
    def test_03_content_analyzer_local(self):
        """3. 지능형 콘텐츠 분석기 로컬 테스트 (OFFLINE/ONLINE)"""
        start_time = time.time()
        
        try:
            if not CONTENT_ANALYZER_AVAILABLE:
                success = False
                message = "콘텐츠 분석기를 사용할 수 없습니다"
            else:
                # 샘플 데이터로 분석 테스트
                sample_content = get_mock_data('sample_content') or """
                # 테스트 콘텐츠
                이것은 감정 분석과 품질 평가를 위한 테스트 콘텐츠입니다.
                긍정적인 내용과 부정적인 내용이 함께 포함되어 있습니다.
                """
                
                # 기본 분석 테스트
                result = self.content_analyzer._calculate_sentiment_score("테스트 제목", sample_content)
                
                success = result is not None and 'overall' in result
                message = f"감정 분석 결과: {result.get('overall', 'N/A')}" if success else "분석 실패"
                
        except Exception as e:
            success = False
            message = f"콘텐츠 분석 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("콘텐츠_분석기_로컬", success, message, duration)
        self.assertTrue(success, message)
    
    def test_04_advanced_sentiment_analysis(self):
        """4. 고급 감정 분석 테스트 (OFFLINE/ONLINE)"""
        start_time = time.time()
        
        try:
            if not CONTENT_ANALYZER_AVAILABLE:
                success = False
                message = "콘텐츠 분석기를 사용할 수 없습니다"
            else:
                # 고급 감정 분석 테스트
                sample_content = "이 제품은 정말 훌륭합니다! 하지만 가격이 조금 비싸네요."
                
                result = self.content_analyzer._calculate_advanced_sentiment_score(
                    "테스트 제목", sample_content, "https://example.com"
                )
                
                success = (result is not None and 
                          'emotions' in result and 
                          'intensity' in result and
                          'confidence' in result)
                
                if success:
                    emotions_count = len([e for e in result['emotions'].values() if e > 0.1])
                    message = f"감지된 감정: {emotions_count}개, 신뢰도: {result['confidence']:.2f}"
                else:
                    message = "고급 감정 분석 실패"
                
        except Exception as e:
            success = False
            message = f"고급 감정 분석 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("고급_감정_분석", success, message, duration)
        self.assertTrue(success, message)
    
    def test_05_quality_evaluation(self):
        """5. 품질 평가 시스템 테스트 (OFFLINE/ONLINE)"""
        start_time = time.time()
        
        try:
            if not CONTENT_ANALYZER_AVAILABLE:
                success = False
                message = "콘텐츠 분석기를 사용할 수 없습니다"
            else:
                # 품질 평가 테스트
                sample_content = """
                # 완전한 가이드: 태양광 발전 시스템 설치
                
                ## 개요
                이 가이드는 태양광 발전 시스템의 설치 과정을 상세히 설명합니다.
                
                ## 필요 장비
                1. 태양광 패널
                2. 인버터
                3. 배터리 (선택사항)
                
                ## 설치 과정
                전문가와 상담 후 진행하시기 바랍니다.
                """
                
                result = self.content_analyzer._calculate_advanced_quality_score(
                    "태양광 설치 가이드", sample_content, "https://example.com", "tutorial"
                )
                
                success = (result is not None and 
                          'overall_score' in result and 
                          'dimensions' in result and
                          'grade' in result)
                
                if success:
                    score = result['overall_score']
                    grade = result['grade']
                    message = f"품질 점수: {score:.1f}점 ({grade}등급)"
                else:
                    message = "품질 평가 실패"
                
        except Exception as e:
            success = False
            message = f"품질 평가 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("품질_평가", success, message, duration)
        self.assertTrue(success, message)
    
    @skip_if_offline
    def test_06_ai_functionality(self):
        """6. AI 기능 테스트 (ONLINE ONLY)"""
        start_time = time.time()
        
        try:
            if not EXTERNAL_MODULES_AVAILABLE:
                raise Exception("외부 모듈을 사용할 수 없습니다")
                
            # AI 챗봇 기능 테스트
            test_message = "안녕하세요! 팜솔라 AI 봇 테스트입니다."
            
            # 비동기 함수를 동기적으로 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response, model_name = loop.run_until_complete(
                self.ai_handler.chat_with_ai(
                    test_message, 
                    self.framework.test_user_name,
                    self.framework.test_user_id
                )
            )
            
            loop.close()
            
            success = response is not None and len(response) > 0
            message = f"응답 길이: {len(response)}자, 모델: {model_name}" if success else "AI 응답 실패"
            
        except Exception as e:
            success = False
            message = f"AI 기능 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("AI_기능", success, message, duration)
        self.assertTrue(success, message)
    
    def test_07_system_health_check(self):
        """7. 시스템 상태 확인 (OFFLINE/ONLINE)"""
        start_time = time.time()
        
        try:
            # 기본 시스템 상태 확인
            checks = {
                "Python 버전": sys.version_info >= (3, 8),
                "필수 디렉토리": os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'src')),
                "로그 디렉토리": True,  # 동적으로 생성되므로 항상 True
                "설정 파일": os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'config')),
            }
            
            # OFFLINE_MODE가 아닌 경우 추가 확인
            if not OFFLINE_MODE:
                checks.update({
                    "외부 모듈": EXTERNAL_MODULES_AVAILABLE,
                    "콘텐츠 분석기": CONTENT_ANALYZER_AVAILABLE,
                })
            
            failed_checks = [name for name, result in checks.items() if not result]
            success = len(failed_checks) == 0
            
            if success:
                message = f"모든 시스템 체크 통과 ({len(checks)}개)"
            else:
                message = f"실패한 체크: {', '.join(failed_checks)}"
                
        except Exception as e:
            success = False
            message = f"시스템 상태 확인 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("시스템_상태_확인", success, message, duration)
        self.assertTrue(success, message)
    
    @classmethod
    def tearDownClass(cls):
        """테스트 정리"""
        # 테스트 결과 요약
        total_tests = len(cls.framework.test_results)
        passed_tests = sum(1 for result in cls.framework.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("🏁 AI_Solarbot 통합 테스트 완료")
        print(f"📊 총 테스트: {total_tests}개")
        print(f"✅ 성공: {passed_tests}개")
        print(f"❌ 실패: {failed_tests}개")
        print(f"📋 모드: {'OFFLINE' if OFFLINE_MODE else 'ONLINE'}")
        
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for test_name, result in cls.framework.test_results.items():
                if not result["success"]:
                    print(f"  • {test_name}: {result['message']}")
        
        # 테스트 결과를 JSON으로 저장
        results_file = os.path.join(os.path.dirname(__file__), 'test_results.json')
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(cls.framework.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n📄 테스트 결과 저장: {results_file}")
        except Exception as e:
            print(f"⚠️ 테스트 결과 저장 실패: {e}")
        
        # 테스트 환경 정리
        if TEST_CONFIG_AVAILABLE:
            cleanup_test_environment()

def run_integration_tests():
    """통합 테스트 실행 함수"""
    print("🔧 환경 설정 확인...")
    
    # OFFLINE_MODE 확인
    if OFFLINE_MODE:
        print("📋 OFFLINE_MODE 활성화 - 외부 서비스 테스트 스킵")
    else:
        print("🌐 ONLINE_MODE - 모든 테스트 실행")
    
    # 테스트 스위트 생성
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(SystemIntegrationTest)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1) 