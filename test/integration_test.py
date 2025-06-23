"""
AI_Solarbot 통합 테스트 프레임워크
실제 팜솔라 강의 환경에서의 전체 시스템 검증
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

from google_drive_handler import GoogleDriveHandler
from user_drive_manager import UserDriveManager
from ai_handler import AIHandler
from natural_ide import NaturalIDE
from web_search_ide import WebSearchIDE
from cloud_homework_manager import CloudHomeworkManager
from collaboration_manager import CollaborationManager
from workspace_template import WorkspaceTemplate

class IntegrationTestFramework:
    """통합 테스트 프레임워크"""
    
    def __init__(self):
        self.test_results = {}
        self.test_user_id = "test_user_12345"
        self.test_user_name = "테스트사용자"
        self.start_time = None
        
    def log_test_result(self, test_name: str, success: bool, message: str = "", duration: float = 0):
        """테스트 결과 로깅"""
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s): {message}")

class SystemIntegrationTest(unittest.TestCase):
    """시스템 통합 테스트"""
    
    @classmethod
    def setUpClass(cls):
        """테스트 클래스 초기화"""
        cls.framework = IntegrationTestFramework()
        cls.drive_handler = GoogleDriveHandler()
        cls.user_manager = UserDriveManager()
        cls.ai_handler = AIHandler()
        cls.natural_ide = NaturalIDE()
        cls.web_search = WebSearchIDE()
        cls.homework_manager = CloudHomeworkManager()
        cls.collaboration_manager = CollaborationManager()
        
        print("🚀 AI_Solarbot 통합 테스트 시작")
        print("=" * 60)
    
    def test_01_google_drive_authentication(self):
        """1. 구글 드라이브 인증 테스트"""
        start_time = time.time()
        
        try:
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
    
    def test_02_user_drive_connection(self):
        """2. 사용자별 드라이브 연결 테스트"""
        start_time = time.time()
        
        try:
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
    
    def test_03_workspace_creation(self):
        """3. 워크스페이스 자동 생성 테스트"""
        start_time = time.time()
        
        try:
            # 워크스페이스 템플릿 생성
            template = WorkspaceTemplate()
            
            # 12주 코스 워크스페이스 생성 테스트
            result = self.user_manager.create_user_workspace(
                self.framework.test_user_id,
                self.framework.test_user_name,
                "12주"
            )
            
            success = result.get("success", False)
            message = result.get("message", "워크스페이스 생성 실패")
            
        except Exception as e:
            success = False
            message = f"워크스페이스 생성 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("워크스페이스_생성", success, message, duration)
        self.assertTrue(success, message)
    
    def test_04_ai_functionality(self):
        """4. AI 기능 테스트"""
        start_time = time.time()
        
        try:
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
    
    def test_05_natural_ide_functionality(self):
        """5. 자연어 IDE 기능 테스트"""
        start_time = time.time()
        
        try:
            # 자연어 파일 생성 테스트
            test_command = "test.py 파일을 만들어줘"
            
            response = self.natural_ide.process_natural_command(
                test_command,
                self.framework.test_user_id
            )
            
            success = response.get("success", False)
            message = response.get("message", "자연어 IDE 실패")
            
        except Exception as e:
            success = False
            message = f"자연어 IDE 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("자연어_IDE", success, message, duration)
        self.assertTrue(success, message)
    
    def test_06_web_search_functionality(self):
        """6. 웹 검색 기능 테스트"""
        start_time = time.time()
        
        try:
            # 웹 검색 기능 테스트
            search_result = self.web_search.search_development_content(
                "python tutorial",
                self.framework.test_user_id
            )
            
            success = search_result.get("success", False)
            message = f"검색 결과: {len(search_result.get('results', []))}개" if success else "웹 검색 실패"
            
        except Exception as e:
            success = False
            message = f"웹 검색 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("웹_검색", success, message, duration)
        self.assertTrue(success, message)
    
    def test_07_homework_management(self):
        """7. 과제 관리 시스템 테스트"""
        start_time = time.time()
        
        try:
            # 과제 진도 확인 테스트
            progress = self.homework_manager.get_user_progress(self.framework.test_user_id)
            
            success = progress is not None
            message = f"진도 데이터 로드 성공" if success else "과제 관리 실패"
            
        except Exception as e:
            success = False
            message = f"과제 관리 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("과제_관리", success, message, duration)
        self.assertTrue(success, message)
    
    def test_08_collaboration_features(self):
        """8. 협업 기능 테스트"""
        start_time = time.time()
        
        try:
            # 팀 목록 조회 테스트
            teams = self.collaboration_manager.get_team_list(self.framework.test_user_id)
            
            success = teams is not None
            message = f"팀 목록 조회 성공" if success else "협업 기능 실패"
            
        except Exception as e:
            success = False
            message = f"협업 기능 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("협업_기능", success, message, duration)
        self.assertTrue(success, message)
    
    def test_09_performance_check(self):
        """9. 성능 체크"""
        start_time = time.time()
        
        try:
            # 메모리 사용량 체크
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # 성능 기준: 메모리 사용량 500MB 미만
            success = memory_mb < 500
            message = f"메모리 사용량: {memory_mb:.1f}MB"
            
        except ImportError:
            success = True
            message = "psutil 없음 - 성능 체크 스킵"
        except Exception as e:
            success = False
            message = f"성능 체크 오류: {str(e)}"
        
        duration = time.time() - start_time
        self.framework.log_test_result("성능_체크", success, message, duration)
        self.assertTrue(success, message)
    
    @classmethod
    def tearDownClass(cls):
        """테스트 결과 요약"""
        print("\n" + "=" * 60)
        print("📊 통합 테스트 결과 요약")
        print("=" * 60)
        
        total_tests = len(cls.framework.test_results)
        passed_tests = sum(1 for result in cls.framework.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {passed_tests}")
        print(f"실패: {failed_tests}")
        print(f"성공률: {(passed_tests/total_tests*100):.1f}%")
        
        # 실패한 테스트 상세 정보
        if failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for test_name, result in cls.framework.test_results.items():
                if not result["success"]:
                    print(f"  - {test_name}: {result['message']}")
        
        # 테스트 결과를 JSON 파일로 저장
        try:
            with open("test_results.json", "w", encoding="utf-8") as f:
                json.dump(cls.framework.test_results, f, ensure_ascii=False, indent=2)
            print(f"\n📁 테스트 결과가 test_results.json에 저장되었습니다.")
        except Exception as e:
            print(f"결과 저장 실패: {e}")

def run_integration_tests():
    """통합 테스트 실행"""
    unittest.main(verbosity=2)

if __name__ == "__main__":
    run_integration_tests() 