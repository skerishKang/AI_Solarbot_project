#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI_Solarbot 기본 테스트
핵심 모듈들이 올바르게 import되고 작동하는지 확인
"""

import sys
import os
import time
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(os.path.join(project_root, 'config'))
sys.path.append(os.path.join(project_root, 'commands'))

class BasicSystemTest:
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def test_imports(self):
        """모듈 import 테스트"""
        print("🔍 모듈 import 테스트 시작...")
        
        tests = [
            ("intelligent_content_analyzer", "IntelligentContentAnalyzer"),
            ("ai_integration_engine", "AIIntegrationEngine"),
            ("enhanced_ai_analyzer", "EnhancedAIAnalyzer"),
            ("user_auth_manager", "user_auth_manager"),
            ("ai_integration_commands", "AIIntegrationCommands"),
            ("sentiment_commands", "sentiment_only_command"),
        ]
        
        for module_name, class_or_func in tests:
            try:
                module = __import__(module_name)
                obj = getattr(module, class_or_func)
                self._pass_test(f"import {module_name}.{class_or_func}")
            except ImportError as e:
                self._fail_test(f"import {module_name}.{class_or_func}", f"ImportError: {e}")
            except AttributeError as e:
                self._fail_test(f"import {module_name}.{class_or_func}", f"AttributeError: {e}")
            except Exception as e:
                self._fail_test(f"import {module_name}.{class_or_func}", f"Error: {e}")
    
    def test_basic_functionality(self):
        """기본 기능 테스트"""
        print("🔧 기본 기능 테스트 시작...")
        
        try:
            # IntelligentContentAnalyzer 테스트
            from intelligent_content_analyzer import IntelligentContentAnalyzer
            analyzer = IntelligentContentAnalyzer()
            
            # 기본 메서드 존재 확인
            required_methods = [
                '_calculate_sentiment_score',
                '_calculate_advanced_sentiment_score',
                '_calculate_quality_score',
                '_calculate_advanced_quality_score'
            ]
            
            for method_name in required_methods:
                if hasattr(analyzer, method_name):
                    self._pass_test(f"analyzer.{method_name} exists")
                else:
                    self._fail_test(f"analyzer.{method_name} exists", "Method not found")
            
            # 간단한 분석 테스트
            test_text = "이것은 테스트용 텍스트입니다. 기본적인 감정 분석과 품질 평가를 테스트합니다."
            
            # 감정 분석 테스트
            try:
                sentiment_score, sentiment_label = analyzer._calculate_sentiment_score(test_text)
                if isinstance(sentiment_score, float) and isinstance(sentiment_label, str):
                    self._pass_test("basic sentiment analysis")
                else:
                    self._fail_test("basic sentiment analysis", f"Invalid return types: {type(sentiment_score)}, {type(sentiment_label)}")
            except Exception as e:
                self._fail_test("basic sentiment analysis", f"Error: {e}")
            
            # 품질 평가 테스트
            try:
                quality_score = analyzer._calculate_quality_score("테스트 제목", test_text, "https://test.com")
                if isinstance(quality_score, (int, float)):
                    self._pass_test("basic quality evaluation")
                else:
                    self._fail_test("basic quality evaluation", f"Invalid return type: {type(quality_score)}")
            except Exception as e:
                self._fail_test("basic quality evaluation", f"Error: {e}")
            
        except ImportError as e:
            self._fail_test("IntelligentContentAnalyzer import", f"ImportError: {e}")
        except Exception as e:
            self._fail_test("basic functionality", f"Error: {e}")
    
    def test_ai_integration(self):
        """AI 통합 모듈 테스트"""
        print("🤖 AI 통합 모듈 테스트 시작...")
        
        try:
            # AI 통합 엔진 테스트
            from ai_integration_engine import AIIntegrationEngine
            
            # 모킹된 AI 핸들러로 테스트
            class MockAIHandler:
                async def generate_response(self, prompt, **kwargs):
                    return "Mock AI response for testing"
            
            ai_engine = AIIntegrationEngine(MockAIHandler())
            
            if hasattr(ai_engine, 'perform_ai_sentiment_analysis'):
                self._pass_test("AIIntegrationEngine.perform_ai_sentiment_analysis exists")
            else:
                self._fail_test("AIIntegrationEngine.perform_ai_sentiment_analysis exists", "Method not found")
            
            if hasattr(ai_engine, 'perform_ai_quality_analysis'):
                self._pass_test("AIIntegrationEngine.perform_ai_quality_analysis exists")
            else:
                self._fail_test("AIIntegrationEngine.perform_ai_quality_analysis exists", "Method not found")
                
        except ImportError as e:
            self._fail_test("AIIntegrationEngine import", f"ImportError: {e}")
        except Exception as e:
            self._fail_test("AI integration", f"Error: {e}")
    
    def test_file_structure(self):
        """파일 구조 테스트"""
        print("📁 파일 구조 테스트 시작...")
        
        required_files = [
            "src/intelligent_content_analyzer.py",
            "src/ai_integration_engine.py", 
            "src/enhanced_ai_analyzer.py",
            "src/user_auth_manager.py",
            "src/ai_integration_commands.py",
            "src/sentiment_commands.py",
            "src/bot.py",
            "config/settings.py",
            "test/integration_test.py"
        ]
        
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            if os.path.exists(full_path):
                self._pass_test(f"file exists: {file_path}")
            else:
                self._fail_test(f"file exists: {file_path}", "File not found")
    
    def _pass_test(self, test_name):
        """테스트 통과 처리"""
        self.passed_tests += 1
        self.test_results.append((test_name, True, ""))
        print(f"✅ {test_name}")
    
    def _fail_test(self, test_name, error_msg):
        """테스트 실패 처리"""
        self.failed_tests += 1
        self.test_results.append((test_name, False, error_msg))
        print(f"❌ {test_name}: {error_msg}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 AI_Solarbot 기본 테스트 시작")
        print("=" * 60)
        
        start_time = time.time()
        
        self.test_file_structure()
        print()
        self.test_imports()
        print()
        self.test_basic_functionality()
        print()
        self.test_ai_integration()
        
        end_time = time.time()
        
        print("\n" + "=" * 60)
        print("🏁 AI_Solarbot 기본 테스트 완료")
        print(f"📊 총 테스트: {self.passed_tests + self.failed_tests}개")
        print(f"✅ 성공: {self.passed_tests}개")
        print(f"❌ 실패: {self.failed_tests}개")
        print(f"⏱️ 소요 시간: {end_time - start_time:.2f}초")
        
        if self.failed_tests > 0:
            print("\n❌ 실패한 테스트:")
            for test_name, passed, error_msg in self.test_results:
                if not passed:
                    print(f"  • {test_name}: {error_msg}")
        
        success_rate = (self.passed_tests / (self.passed_tests + self.failed_tests)) * 100
        print(f"\n📈 성공률: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 시스템이 정상적으로 작동하고 있습니다!")
            return True
        else:
            print("⚠️ 시스템에 문제가 있습니다. 수정이 필요합니다.")
            return False

if __name__ == "__main__":
    tester = BasicSystemTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1) 