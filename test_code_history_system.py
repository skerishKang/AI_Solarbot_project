"""
코드 히스토리 관리 및 성장 추적 시스템 통합 테스트
EnhancedCodeExecutor + CodeHistoryManager 전체 기능 검증
"""

import os
import sys
import json
import asyncio
import time
from typing import Dict, List, Any

# 현재 디렉토리를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, current_dir)

print("🧪 === 코드 히스토리 관리 및 성장 추적 시스템 통합 테스트 ===")

def print_separator(title: str):
    """테스트 섹션 구분선"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)

def print_result(test_name: str, success: bool, details: str = ""):
    """테스트 결과 출력"""
    status = "✅ 성공" if success else "❌ 실패"
    print(f"{status} | {test_name}")
    if details:
        print(f"    📝 {details}")

async def test_enhanced_code_executor():
    """향상된 코드 실행기 테스트"""
    try:
        # 모듈 import 시도
        try:
            from enhanced_code_executor import EnhancedCodeExecutor
            print_result("향상된 코드 실행기 import", True, "EnhancedCodeExecutor 모듈 로드 성공")
        except ImportError as e:
            print_result("향상된 코드 실행기 import", False, f"모듈 로드 실패: {e}")
            return False
        
        # 실행기 초기화
        try:
            executor = EnhancedCodeExecutor()
            print_result("실행기 초기화", True, "EnhancedCodeExecutor 인스턴스 생성 성공")
        except Exception as e:
            print_result("실행기 초기화", False, f"초기화 실패: {e}")
            return False
        
        # 샘플 코드 실행 (Python)
        test_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""
        
        try:
            result = await executor.execute_code_with_history(test_code, "python", "test_user")
            if result.success:
                print_result("코드 실행 (Python)", True, f"실행 시간: {result.execution_time:.3f}초")
            else:
                print_result("코드 실행 (Python)", False, f"실행 오류: {result.error}")
        except Exception as e:
            print_result("코드 실행 (Python)", False, f"실행 중 예외: {e}")
        
        # 히스토리 조회 테스트
        try:
            history = executor.get_user_execution_history("test_user")
            print_result("사용자 히스토리 조회", True, f"기록 수: {len(history)}개")
        except Exception as e:
            print_result("사용자 히스토리 조회", False, f"조회 실패: {e}")
        
        # 성장 리포트 테스트
        try:
            report = executor.get_user_growth_report("test_user")
            if "summary" in report:
                summary = report["summary"]
                print_result("성장 리포트 생성", True, 
                           f"총 실행: {summary.get('total_executions', 0)}회, 성공률: {summary.get('success_rate', 0):.1f}%")
            else:
                print_result("성장 리포트 생성", False, "리포트 생성 실패")
        except Exception as e:
            print_result("성장 리포트 생성", False, f"리포트 생성 중 예외: {e}")
        
        return True
        
    except Exception as e:
        print_result("전체 테스트", False, f"치명적 오류: {e}")
        return False

def test_code_history_manager():
    """코드 히스토리 매니저 단독 테스트"""
    try:
        # 모듈 import
        try:
            from code_history_manager import CodeHistoryManager
            print_result("히스토리 매니저 import", True, "CodeHistoryManager 모듈 로드 성공")
        except ImportError as e:
            print_result("히스토리 매니저 import", False, f"모듈 로드 실패: {e}")
            return False
        
        # 매니저 인스턴스 생성
        try:
            manager = CodeHistoryManager()
            print_result("히스토리 매니저 초기화", True, "인스턴스 생성 성공")
        except Exception as e:
            print_result("히스토리 매니저 초기화", False, f"초기화 실패: {e}")
            return False
        
        print("\n📊 시스템 통계 테스트")
        try:
            stats = manager.get_system_statistics()
            print_result("시스템 통계 조회", True, 
                        f"총 실행: {stats.get('total_executions', 0)}회, 활성 사용자: {stats.get('active_users', 0)}명, 지원 언어: {stats.get('supported_languages', 0)}개")
        except Exception as e:
            print_result("시스템 통계 조회", False, f"통계 조회 실패: {e}")
        
        print("\n🏆 리더보드 테스트")
        try:
            leaderboard = manager.get_global_leaderboard(limit=5)
            print_result("리더보드 조회", True, f"상위 {len(leaderboard)}명 조회")
        except Exception as e:
            print_result("리더보드 조회", False, f"리더보드 조회 실패: {e}")
        
        print("\n⭐ 우수 코드 큐레이션 테스트")
        try:
            excellent_codes = manager.get_curated_excellent_codes(limit=5)
            print_result("우수 코드 조회", True, f"{len(excellent_codes)}개 우수 코드 발견")
        except Exception as e:
            print_result("우수 코드 조회", False, f"우수 코드 조회 실패: {e}")
        
        return True
        
    except Exception as e:
        print_result("코드 히스토리 매니저 테스트", False, f"치명적 오류: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    print("🚀 코드 히스토리 관리 및 성장 추적 시스템 통합 테스트를 시작합니다...\n")
    
    # 테스트 실행
    results = []
    
    print_separator("향상된 코드 실행기 테스트")
    try:
        enhanced_result = await test_enhanced_code_executor()
        results.append(enhanced_result)
    except Exception as e:
        print_result("향상된 코드 실행기 테스트", False, f"테스트 실행 중 오류: {e}")
        results.append(False)
    
    print_separator("코드 히스토리 매니저 단독 테스트")
    try:
        history_result = test_code_history_manager()
        results.append(history_result)
    except Exception as e:
        print_result("코드 히스토리 매니저 테스트", False, f"테스트 실행 중 오류: {e}")
        results.append(False)
    
    # 결과 요약
    print_separator("테스트 결과 요약")
    
    success_count = sum(results)
    total_count = len(results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"📊 전체 테스트 결과: {success_count}/{total_count} 통과")
    print(f"✅ 성공률: {success_rate:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
        print("🚀 코드 히스토리 관리 및 성장 추적 시스템이 정상 작동합니다.")
        exit_code = 0
    else:
        print(f"\n⚠️ {total_count - success_count}개 테스트가 실패했습니다.")
        print("🔧 시스템 설정을 확인해주세요.")
        exit_code = 1
    
    print(f"\n🏁 테스트 종료 (코드: {exit_code})")
    if exit_code == 1:
        print("🔥 일부 테스트에서 문제가 발견되었습니다. 로그를 확인해주세요.")
    
    return exit_code

if __name__ == "__main__":
    import sys
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)