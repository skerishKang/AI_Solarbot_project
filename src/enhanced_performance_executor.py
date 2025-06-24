"""
성능 벤치마크 통합 코드 실행기
OnlineCodeExecutor + PerformanceBenchmark + CodeHistoryManager 통합
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict

# 필요한 모듈들 import
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, current_dir)
    sys.path.insert(0, parent_dir)
    
    from online_code_executor import OnlineCodeExecutor, ExecutionResult
    from performance_benchmark import PerformanceBenchmark, BenchmarkResult, OptimizationSuggestion, get_performance_benchmark
    from code_history_manager import CodeHistoryManager, history_manager
    
    MODULES_AVAILABLE = True
    print("✅ 모든 성능 벤치마크 모듈이 성공적으로 로드되었습니다.")
except ImportError as e:
    print(f"⚠️ 모듈 로딩 실패: {e}")
    MODULES_AVAILABLE = False

class EnhancedPerformanceExecutor(OnlineCodeExecutor):
    """성능 벤치마크 및 최적화 제안이 통합된 향상된 코드 실행기"""
    
    def __init__(self, ai_handler=None, 
                 performance_benchmark_instance: Optional[PerformanceBenchmark] = None,
                 history_manager_instance: Optional[CodeHistoryManager] = None):
        # 부모 클래스 초기화
        super().__init__(ai_handler)
        
        # 성능 벤치마크 인스턴스 설정
        self.performance_benchmark = performance_benchmark_instance or get_performance_benchmark()
        self.benchmark_enabled = performance_benchmark_instance is not None or MODULES_AVAILABLE
        
        # 히스토리 매니저 설정
        self.history_manager = history_manager_instance or history_manager
        self.history_enabled = history_manager_instance is not None or MODULES_AVAILABLE
        
        # 성능 분석 옵션
        self.enable_detailed_analysis = True
        self.enable_optimization_suggestions = True
        self.enable_comparative_analysis = True
        
        print(f"🚀 EnhancedPerformanceExecutor 초기화 완료")
        print(f"   📊 성능 벤치마크: {'활성화' if self.benchmark_enabled else '비활성화'}")
        print(f"   📈 히스토리 관리: {'활성화' if self.history_enabled else '비활성화'}")
    
    async def execute_code_with_performance_analysis(self, code: str, language: str, 
                                                   user_id: str = "default_user",
                                                   use_online_api: bool = False,
                                                   enable_ai_review: bool = True) -> Tuple[ExecutionResult, Optional[BenchmarkResult], List[OptimizationSuggestion]]:
        """성능 분석이 포함된 종합 코드 실행"""
        
        print(f"🔬 성능 분석 포함 코드 실행 시작: {language}")
        
        # 1. 기본 코드 실행
        execution_result = await self.execute_code(code, language, use_online_api)
        
        benchmark_result = None
        optimization_suggestions = []
        
        # 2. 성능 벤치마크 분석 (성공적으로 실행된 경우에만)
        if self.benchmark_enabled and execution_result.success:
            try:
                print("📊 성능 벤치마크 분석 중...")
                
                # CPU 사용량 추정 (실행 시간 기반)
                cpu_usage = min(execution_result.execution_time * 10, 100.0)
                
                benchmark_result = self.performance_benchmark.analyze_performance(
                    code=code,
                    language=language,
                    execution_time=execution_result.execution_time,
                    memory_usage=execution_result.memory_usage,
                    cpu_usage=cpu_usage
                )
                
                print(f"   🎯 성능 점수: {benchmark_result.performance_score:.1f}/100")
                print(f"   🧮 알고리즘 복잡도: {benchmark_result.algorithm_complexity}")
                print(f"   📈 최적화 레벨: {benchmark_result.optimization_level}")
                
            except Exception as e:
                print(f"⚠️ 성능 벤치마크 분석 실패: {e}")
        
        # 3. 최적화 제안 생성
        if self.enable_optimization_suggestions and benchmark_result:
            try:
                print("💡 최적화 제안 생성 중...")
                optimization_suggestions = self.performance_benchmark.generate_optimization_suggestions(
                    code, language, benchmark_result
                )
                print(f"   ✨ {len(optimization_suggestions)}개의 최적화 제안 생성됨")
                
            except Exception as e:
                print(f"⚠️ 최적화 제안 생성 실패: {e}")
        
        # 4. 히스토리에 기록 (가능한 경우)
        if self.history_enabled:
            try:
                # 벤치마크 결과를 히스토리 데이터에 추가
                history_data = {
                    "success": execution_result.success,
                    "execution_time": execution_result.execution_time,
                    "memory_usage": execution_result.memory_usage,
                    "performance_score": execution_result.performance_score,
                    "output": execution_result.output,
                    "error": execution_result.error,
                    "optimization_suggestions": [asdict(s) for s in optimization_suggestions],
                }
                
                if benchmark_result:
                    history_data.update({
                        "benchmark_result": asdict(benchmark_result),
                        "algorithm_complexity": benchmark_result.algorithm_complexity,
                        "optimization_level": benchmark_result.optimization_level,
                        "comparative_ranking": benchmark_result.comparative_ranking
                    })
                
                await self.history_manager.add_execution_record(
                    user_id=user_id,
                    code=code,
                    language=language,
                    execution_data=history_data
                )
                
            except Exception as e:
                print(f"⚠️ 히스토리 기록 실패: {e}")
        
        return execution_result, benchmark_result, optimization_suggestions
    
    def get_performance_insights(self, code: str, language: str, 
                               benchmark_result: BenchmarkResult) -> Dict[str, Any]:
        """성능 인사이트 종합 분석"""
        
        insights = {
            "performance_summary": {
                "score": benchmark_result.performance_score,
                "level": benchmark_result.optimization_level,
                "complexity": benchmark_result.algorithm_complexity,
                "category": benchmark_result.benchmark_category,
                "ranking": benchmark_result.comparative_ranking
            }
        }
        
        # 기준선과 비교
        if self.enable_comparative_analysis:
            try:
                comparison = self.performance_benchmark.compare_with_baseline(benchmark_result)
                insights["baseline_comparison"] = comparison
            except Exception as e:
                print(f"⚠️ 기준선 비교 실패: {e}")
        
        # 언어별 통계
        try:
            language_stats = self.performance_benchmark.get_benchmark_statistics(
                language=language,
                category=benchmark_result.benchmark_category
            )
            insights["language_statistics"] = language_stats
        except Exception as e:
            print(f"⚠️ 언어별 통계 조회 실패: {e}")
        
        # 성능 개선 추천
        insights["improvement_recommendations"] = self._generate_improvement_recommendations(
            benchmark_result
        )
        
        return insights
    
    def _generate_improvement_recommendations(self, benchmark_result: BenchmarkResult) -> List[str]:
        """성능 개선 추천사항 생성"""
        recommendations = []
        
        # 성능 점수 기반 추천
        if benchmark_result.performance_score < 50:
            recommendations.append("🔧 전체적인 알고리즘 재설계를 고려하세요")
            recommendations.append("📚 해당 문제에 특화된 자료구조나 알고리즘을 연구해보세요")
        elif benchmark_result.performance_score < 70:
            recommendations.append("⚡ 일부 병목 지점을 최적화하면 성능이 크게 개선될 수 있습니다")
            recommendations.append("🔍 프로파일링을 통해 가장 시간이 오래 걸리는 부분을 찾아보세요")
        elif benchmark_result.performance_score < 90:
            recommendations.append("✨ 이미 좋은 성능입니다. 미세한 최적화로 더 개선할 수 있습니다")
        else:
            recommendations.append("🌟 우수한 성능입니다! 현재 구현이 매우 효율적입니다")
        
        # 복잡도 기반 추천
        if benchmark_result.algorithm_complexity == 'O(n^2)':
            recommendations.append("📊 O(n log n) 또는 O(n) 복잡도 알고리즘 사용을 고려하세요")
        elif benchmark_result.algorithm_complexity == 'O(n^3)':
            recommendations.append("🚨 큐빅 시간 복잡도는 대용량 데이터에서 문제가 될 수 있습니다")
        elif benchmark_result.algorithm_complexity == 'O(2^n)':
            recommendations.append("⚠️ 지수 시간 복잡도입니다. 동적 프로그래밍이나 메모이제이션을 고려하세요")
        
        # 메모리 사용량 기반 추천
        if benchmark_result.memory_usage > 1000:  # 1GB 이상
            recommendations.append("💾 메모리 사용량이 매우 높습니다. 스트리밍 처리나 압축을 고려하세요")
        elif benchmark_result.memory_usage > 500:  # 500MB 이상
            recommendations.append("🗂️ 메모리 효율적인 데이터 구조 사용을 고려하세요")
        
        return recommendations
    
    async def run_performance_benchmark_suite(self, language: str, 
                                            test_cases: List[Dict[str, str]]) -> Dict[str, Any]:
        """성능 벤치마크 테스트 스위트 실행"""
        
        print(f"🧪 {language} 성능 벤치마크 스위트 실행 시작")
        print(f"📝 총 {len(test_cases)}개의 테스트 케이스")
        
        results = []
        total_execution_time = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔬 테스트 케이스 {i}/{len(test_cases)}: {test_case.get('name', f'Test_{i}')}")
            
            try:
                execution_result, benchmark_result, suggestions = await self.execute_code_with_performance_analysis(
                    code=test_case['code'],
                    language=language,
                    user_id=f"benchmark_user_{i}"
                )
                
                total_execution_time += execution_result.execution_time
                
                test_result = {
                    "test_name": test_case.get('name', f'Test_{i}'),
                    "execution_result": asdict(execution_result),
                    "benchmark_result": asdict(benchmark_result) if benchmark_result else None,
                    "optimization_suggestions": [asdict(s) for s in suggestions],
                    "insights": self.get_performance_insights(test_case['code'], language, benchmark_result) if benchmark_result else None
                }
                
                results.append(test_result)
                
                print(f"   ✅ 완료 - 성능 점수: {benchmark_result.performance_score:.1f}/100" if benchmark_result else "   ✅ 완료")
                
            except Exception as e:
                print(f"   ❌ 실패: {e}")
                results.append({
                    "test_name": test_case.get('name', f'Test_{i}'),
                    "error": str(e),
                    "execution_result": None,
                    "benchmark_result": None
                })
        
        # 전체 결과 분석
        successful_results = [r for r in results if r.get('benchmark_result')]
        
        suite_summary = {
            "total_tests": len(test_cases),
            "successful_tests": len(successful_results),
            "failed_tests": len(test_cases) - len(successful_results),
            "total_execution_time": total_execution_time,
            "average_performance_score": 0,
            "best_performance": None,
            "worst_performance": None,
            "results": results
        }
        
        if successful_results:
            scores = [r['benchmark_result']['performance_score'] for r in successful_results]
            suite_summary["average_performance_score"] = sum(scores) / len(scores)
            suite_summary["best_performance"] = max(successful_results, key=lambda x: x['benchmark_result']['performance_score'])
            suite_summary["worst_performance"] = min(successful_results, key=lambda x: x['benchmark_result']['performance_score'])
        
        print(f"\n🏁 벤치마크 스위트 완료")
        print(f"   📊 성공률: {len(successful_results)}/{len(test_cases)} ({len(successful_results)/len(test_cases)*100:.1f}%)")
        if suite_summary["average_performance_score"] > 0:
            print(f"   🎯 평균 성능: {suite_summary['average_performance_score']:.1f}/100")
        
        return suite_summary
    
    def get_language_performance_comparison(self, languages: List[str]) -> Dict[str, Any]:
        """언어별 성능 비교 분석"""
        
        comparison_data = {}
        
        for language in languages:
            try:
                stats = self.performance_benchmark.get_benchmark_statistics(language=language)
                comparison_data[language] = {
                    "total_benchmarks": stats.get("total_benchmarks", 0),
                    "average_performance": stats.get("performance_statistics", {}).get("average", 0),
                    "average_execution_time": stats.get("execution_time_statistics", {}).get("average", 0),
                    "average_memory_usage": stats.get("memory_statistics", {}).get("average", 0),
                    "optimization_distribution": stats.get("distributions", {}).get("by_optimization_level", {})
                }
            except Exception as e:
                print(f"⚠️ {language} 통계 조회 실패: {e}")
                comparison_data[language] = {"error": str(e)}
        
        # 전체 비교 인사이트
        valid_data = {lang: data for lang, data in comparison_data.items() if "error" not in data and data.get("total_benchmarks", 0) > 0}
        
        insights = []
        if len(valid_data) > 1:
            # 성능 순위
            performance_ranking = sorted(valid_data.items(), key=lambda x: x[1]["average_performance"], reverse=True)
            performance_text = ' > '.join([f'{lang}({data["average_performance"]:.1f})' for lang, data in performance_ranking])
            insights.append(f"🏆 성능 순위: {performance_text}")
            
            # 실행 속도 순위
            speed_ranking = sorted(valid_data.items(), key=lambda x: x[1]["average_execution_time"])
            speed_text = ' > '.join([f'{lang}({data["average_execution_time"]:.3f}s)' for lang, data in speed_ranking])
            insights.append(f"⚡ 속도 순위: {speed_text}")
            
            # 메모리 효율성 순위
            memory_ranking = sorted(valid_data.items(), key=lambda x: x[1]["average_memory_usage"])
            memory_text = ' > '.join([f'{lang}({data["average_memory_usage"]:.1f}MB)' for lang, data in memory_ranking])
            insights.append(f"💾 메모리 효율성: {memory_text}")
        
        return {
            "language_comparison": comparison_data,
            "insights": insights,
            "summary": {
                "total_languages_analyzed": len(valid_data),
                "best_performance_language": performance_ranking[0][0] if len(valid_data) > 0 else None,
                "fastest_language": speed_ranking[0][0] if len(valid_data) > 0 else None,
                "most_memory_efficient": memory_ranking[0][0] if len(valid_data) > 0 else None
            }
        }
    
    def generate_performance_report(self, user_id: str = "default_user", 
                                  time_period_days: int = 30) -> Dict[str, Any]:
        """사용자별 성능 보고서 생성"""
        
        report = {
            "user_id": user_id,
            "report_period": f"최근 {time_period_days}일",
            "generated_at": time.time()
        }
        
        try:
            # 사용자 실행 히스토리 조회
            if self.history_enabled:
                user_history = self.history_manager.get_user_execution_history(user_id)
                
                if user_history:
                    # 성능 트렌드 분석
                    performance_scores = []
                    execution_times = []
                    languages_used = set()
                    
                    for record in user_history:
                        if record.success and hasattr(record, 'performance_score'):
                            performance_scores.append(record.performance_score)
                            execution_times.append(record.execution_time)
                            languages_used.add(record.language)
                    
                    if performance_scores:
                        report["performance_trends"] = {
                            "average_score": sum(performance_scores) / len(performance_scores),
                            "best_score": max(performance_scores),
                            "improvement_trend": "개선됨" if len(performance_scores) > 1 and performance_scores[-1] > performance_scores[0] else "유지",
                            "total_executions": len(performance_scores),
                            "languages_explored": list(languages_used)
                        }
                
                # 성장 추적 정보
                growth_metrics = self.history_manager.get_user_growth_metrics(user_id)
                if growth_metrics:
                    report["growth_analysis"] = growth_metrics
            
            # 벤치마크 통계 (전체 대비 사용자 위치)
            if self.benchmark_enabled:
                overall_stats = self.performance_benchmark.get_benchmark_statistics()
                report["comparative_analysis"] = {
                    "system_average": overall_stats.get("performance_statistics", {}).get("average", 0),
                    "user_vs_system": "시스템 히스토리 데이터 부족으로 비교 불가"
                }
            
            # 추천사항
            report["recommendations"] = self._generate_user_recommendations(report)
            
        except Exception as e:
            report["error"] = f"보고서 생성 중 오류: {e}"
        
        return report
    
    def _generate_user_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """사용자별 추천사항 생성"""
        recommendations = []
        
        performance_trends = report.get("performance_trends", {})
        
        if performance_trends:
            avg_score = performance_trends.get("average_score", 0)
            
            if avg_score < 50:
                recommendations.append("🎯 기본 알고리즘과 데이터 구조 학습에 집중하세요")
                recommendations.append("📚 코딩 테스트 기초 문제부터 차근차근 연습하세요")
            elif avg_score < 70:
                recommendations.append("⚡ 시간 복잡도를 의식한 코딩 연습을 늘려보세요")
                recommendations.append("🔍 코드 리뷰를 통해 최적화 포인트를 찾아보세요")
            elif avg_score < 90:
                recommendations.append("🌟 고급 알고리즘과 최적화 기법을 학습해보세요")
                recommendations.append("💡 다양한 언어로 같은 문제를 해결해보세요")
            else:
                recommendations.append("🏆 훌륭한 성능입니다! 다른 개발자들에게 지식을 공유해보세요")
                recommendations.append("🚀 오픈소스 프로젝트 기여나 알고리즘 경진대회 참여를 고려해보세요")
            
            languages_count = len(performance_trends.get("languages_explored", []))
            if languages_count < 3:
                recommendations.append(f"🌈 다양한 언어 경험을 위해 새로운 언어를 시도해보세요 (현재: {languages_count}개 언어)")
        
        return recommendations

# 전역 인스턴스 (필요시 사용)
enhanced_performance_executor = None

def get_enhanced_performance_executor(ai_handler=None):
    """필요시 EnhancedPerformanceExecutor 인스턴스를 생성하여 반환"""
    global enhanced_performance_executor
    if enhanced_performance_executor is None and MODULES_AVAILABLE:
        try:
            enhanced_performance_executor = EnhancedPerformanceExecutor(ai_handler)
        except Exception as e:
            print(f"⚠️ EnhancedPerformanceExecutor 인스턴스 생성 실패: {e}")
    return enhanced_performance_executor