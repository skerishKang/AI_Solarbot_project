#!/usr/bin/env python3
"""
상세한 디버그 테스트
"""

import sys
import os
import traceback

print("🔍 상세 디버그 테스트 시작")

try:
    # 현재 디렉토리를 경로에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    print("📊 performance_benchmark 모듈 임포트 중...")
    import performance_benchmark
    print("✅ performance_benchmark 모듈 로드 성공")
    
    print("🚀 online_code_executor 모듈 임포트 중...")
    try:
        import online_code_executor
        print("✅ online_code_executor 모듈 로드 성공")
    except Exception as e:
        print(f"❌ online_code_executor 오류: {e}")
        print("📝 상세 오류 정보:")
        traceback.print_exc()
        
        # 개별 임포트 테스트
        print("\n🔬 개별 구성 요소 테스트:")
        
        try:
            print("  - os 모듈 테스트...")
            import os as test_os
            print("  ✅ os 모듈 정상")
        except Exception as e2:
            print(f"  ❌ os 모듈 오류: {e2}")
        
        try:
            print("  - re 모듈 테스트...")
            import re as test_re
            print("  ✅ re 모듈 정상")
        except Exception as e2:
            print(f"  ❌ re 모듈 오류: {e2}")
            
        try:
            print("  - json 모듈 테스트...")
            import json as test_json
            print("  ✅ json 모듈 정상")
        except Exception as e2:
            print(f"  ❌ json 모듈 오류: {e2}")
            
        try:
            print("  - timeout_decorator 조건부 임포트 테스트...")
            try:
                import timeout_decorator as test_timeout
                print("  ✅ timeout_decorator 사용 가능")
            except ImportError:
                print("  ⚠️ timeout_decorator 없음 (정상)")
                
        except Exception as e2:
            print(f"  ❌ timeout_decorator 테스트 오류: {e2}")
        
        sys.exit(1)
    
    print("📈 code_history_manager 모듈 임포트 중...")
    try:
        import code_history_manager
        print("✅ code_history_manager 모듈 로드 성공")
    except Exception as e:
        print(f"⚠️ code_history_manager 오류: {e}")
    
    print("⚡ enhanced_performance_executor 모듈 임포트 중...")
    try:
        import enhanced_performance_executor
        print("✅ enhanced_performance_executor 모듈 로드 성공")
    except Exception as e:
        print(f"❌ enhanced_performance_executor 오류: {e}")
        traceback.print_exc()
    
    print("\n🎉 디버그 테스트 완료!")
    
except Exception as e:
    print(f"❌ 전체 테스트 실패: {e}")
    traceback.print_exc()
    sys.exit(1) 