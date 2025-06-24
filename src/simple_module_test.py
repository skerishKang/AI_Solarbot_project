#!/usr/bin/env python3
"""
간단한 모듈 임포트 테스트
"""

import sys
import os

print("🧪 모듈 임포트 테스트 시작")

try:
    # 현재 디렉토리를 경로에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    # 성능 벤치마크 모듈 임포트
    print("📊 performance_benchmark 모듈 임포트 중...")
    import performance_benchmark
    print("✅ performance_benchmark 모듈 로드 성공")
    
    # OnlineCodeExecutor 모듈 임포트
    print("🚀 online_code_executor 모듈 임포트 중...")
    import online_code_executor
    print("✅ online_code_executor 모듈 로드 성공")
    
    # CodeHistoryManager 모듈 임포트
    print("📈 code_history_manager 모듈 임포트 중...")
    import code_history_manager
    print("✅ code_history_manager 모듈 로드 성공")
    
    # EnhancedPerformanceExecutor 모듈 임포트
    print("⚡ enhanced_performance_executor 모듈 임포트 중...")
    import enhanced_performance_executor
    print("✅ enhanced_performance_executor 모듈 로드 성공")
    
    print("\n🎉 모든 모듈 임포트 성공!")
    
    # 기본 인스턴스 생성 테스트
    print("\n🔧 기본 인스턴스 생성 테스트...")
    
    benchmark = performance_benchmark.PerformanceBenchmark()
    print("✅ PerformanceBenchmark 인스턴스 생성 성공")
    
    print("\n🏆 모든 테스트 통과!")
    
except ImportError as e:
    print(f"❌ Import 오류: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    sys.exit(1) 