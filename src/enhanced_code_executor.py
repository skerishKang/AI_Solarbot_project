"""
확장된 코드 실행기 - 히스토리 관리 및 성장 추적 기능 포함
OnlineCodeExecutor + CodeHistoryManager 통합 시스템
"""

import os
import sys
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

# ExecutionResult 클래스 정의 (import 실패에 대비)
@dataclass
class ExecutionResult:
    success: bool
    language: str
    output: str
    error: str
    execution_time: float
    memory_usage: int
    return_code: int
    performance_score: float
    optimization_suggestions: List[str]
    dependencies_detected: List[str]

# 기존 모듈들 import
try:
    # sys.path에 현재 디렉토리와 src 디렉토리 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, current_dir)
    sys.path.insert(0, parent_dir)
    
    from online_code_executor import OnlineCodeExecutor
    try:
        from online_code_executor import ExecutionResult as OriginalExecutionResult
        ExecutionResult = OriginalExecutionResult  # 원본을 사용
    except ImportError:
        pass  # 위에서 정의한 ExecutionResult 사용
    
    from code_history_manager import CodeHistoryManager, history_manager
    MODULES_AVAILABLE = True
    print("✅ 모든 필수 모듈이 성공적으로 로드되었습니다.")
except ImportError as e:
    print(f"⚠️ 필수 모듈을 로드할 수 없습니다: {e}")
    MODULES_AVAILABLE = False
    
    # 기본 클래스들을 임시로 정의
    class OnlineCodeExecutor:
        def __init__(self, ai_handler=None):
            pass
        
        async def execute_code(self, code: str, language: str, use_online_api: bool = False):
            return ExecutionResult(
                success=False,
                language=language,
                output="",
                error="모듈을 로드할 수 없습니다",
                execution_time=0.0,
                memory_usage=0,
                return_code=-1,
                performance_score=0.0,
                optimization_suggestions=[],
                dependencies_detected=[]
            )
    
    class CodeHistoryManager:
        def __init__(self):
            self.executions = []
            self.milestones = []
            self.portfolios = []
        
        def add_execution_record(self, user_id: str, language: str, code: str, execution_result: Dict[str, Any], ai_review_result: Optional[Dict[str, Any]] = None) -> str:
            return "dummy_id"
        
        def get_user_progress_report(self, user_id: str, language: Optional[str] = None) -> Dict[str, Any]:
            return {"error": "모듈을 로드할 수 없습니다"}
    
    history_manager = CodeHistoryManager()

class EnhancedCodeExecutor(OnlineCodeExecutor):
    """히스토리 관리 및 성장 추적 기능이 통합된 향상된 코드 실행기"""
    
    def __init__(self, ai_handler=None, history_manager_instance: Optional[CodeHistoryManager] = None):
        # 부모 클래스 초기화
        super().__init__(ai_handler)
        
        # 히스토리 매니저 설정
        self.history_manager = history_manager_instance or history_manager
        self.history_enabled = MODULES_AVAILABLE and self.history_manager is not None
        
        if self.history_enabled:
            print("✅ 코드 히스토리 관리 및 성장 추적 기능이 활성화되었습니다.")
        else:
            print("⚠️ 히스토리 관리 기능이 비활성화됩니다.")
    
    async def execute_code_with_tracking(self, code: str, language: str, user_id: str = "default_user", 
                                       use_online_api: bool = False, enable_ai_review: bool = True) -> Tuple[ExecutionResult, Optional[Dict[str, Any]], Optional[str]]:
        """코드 실행 + AI 리뷰 + 히스토리 추적을 모두 수행"""
        try:
            # 1. 기존 코드 실행 + AI 리뷰
            execution_result, ai_review_result = await self.execute_code_with_ai_review(
                code, language, use_online_api, enable_ai_review
            )
            
            execution_id = None
            
            # 2. 히스토리 관리 (성공/실패 무관하게 모든 실행 기록)
            if self.history_enabled:
                try:
                    # ExecutionResult를 딕셔너리로 변환
                    execution_data = asdict(execution_result)
                    
                    # 히스토리 매니저에 기록 추가
                    execution_id = self.history_manager.add_execution_record(
                        user_id=user_id,
                        language=language,
                        code=code,
                        execution_result=execution_data,
                        ai_review_result=ai_review_result
                    )
                    
                    print(f"📊 실행 기록이 저장되었습니다 (ID: {execution_id})")
                    
                except Exception as e:
                    print(f"⚠️ 히스토리 저장 중 오류 발생: {e}")
            
            return execution_result, ai_review_result, execution_id
            
        except Exception as e:
            # 실행 오류 시에도 기본 ExecutionResult 반환
            error_result = ExecutionResult(
                success=False,
                language=language,
                output="",
                error=f"통합 실행 중 오류 발생: {str(e)}",
                execution_time=0.0,
                memory_usage=0,
                return_code=-1,
                performance_score=0.0,
                optimization_suggestions=[],
                dependencies_detected=[]
            )
            return error_result, None, None
    
    def get_user_progress_dashboard(self, user_id: str, language: Optional[str] = None) -> Dict[str, Any]:
        """사용자 개인화 대시보드 생성"""
        if not self.history_enabled:
            return {"error": "히스토리 관리 기능이 비활성화되어 있습니다."}
        
        try:
            # 기본 진행 리포트
            progress_report = self.history_manager.get_user_progress_report(user_id, language)
            
            # 추가 대시보드 정보
            dashboard_data = {
                "user_dashboard": progress_report,
                "quick_stats": {
                    "total_executions": progress_report.get("summary", {}).get("total_executions", 0),
                    "success_rate": progress_report.get("summary", {}).get("success_rate", 0),
                    "current_streak": self._calculate_current_streak(user_id),
                    "favorite_language": self._get_favorite_language(user_id),
                    "skill_badges": self._get_skill_badges(user_id)
                },
                "recent_activity": self._get_recent_activity(user_id, limit=5),
                "goals_progress": self._calculate_goals_progress(user_id),
                "next_challenges": self._suggest_next_challenges(user_id, language)
            }
            
            return dashboard_data
            
        except Exception as e:
            return {"error": f"대시보드 생성 중 오류 발생: {str(e)}"}
    
    def _calculate_current_streak(self, user_id: str) -> int:
        """현재 성공 연속 횟수 계산"""
        if not self.history_enabled:
            return 0
        
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        if not user_executions:
            return 0
        
        # 최근 실행부터 역순으로 확인
        streak = 0
        for execution in reversed(user_executions):
            if execution.success:
                streak += 1
            else:
                break
        
        return streak
    
    def _get_favorite_language(self, user_id: str) -> str:
        """가장 많이 사용한 언어 반환"""
        if not self.history_enabled:
            return "Unknown"
        
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        if not user_executions:
            return "None"
        
        from collections import Counter
        language_count = Counter([e.language for e in user_executions])
        return language_count.most_common(1)[0][0] if language_count else "None"
    
    def _get_skill_badges(self, user_id: str) -> List[Dict[str, str]]:
        """스킬 배지 목록 생성"""
        if not self.history_enabled:
            return []
        
        badges = []
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        
        if not user_executions:
            return badges
        
        # 실행 횟수 배지
        total_executions = len(user_executions)
        if total_executions >= 100:
            badges.append({"name": "코딩 마스터", "description": "100회 이상 코드 실행", "level": "gold"})
        elif total_executions >= 50:
            badges.append({"name": "코딩 전문가", "description": "50회 이상 코드 실행", "level": "silver"})
        elif total_executions >= 10:
            badges.append({"name": "코딩 입문자", "description": "10회 이상 코드 실행", "level": "bronze"})
        
        # 성공률 배지
        success_rate = len([e for e in user_executions if e.success]) / len(user_executions)
        if success_rate >= 0.9:
            badges.append({"name": "정확도 킹", "description": "90% 이상 성공률", "level": "gold"})
        elif success_rate >= 0.7:
            badges.append({"name": "안정적 실행", "description": "70% 이상 성공률", "level": "silver"})
        
        # 언어 다양성 배지
        languages_used = len(set(e.language for e in user_executions))
        if languages_used >= 5:
            badges.append({"name": "다국어 개발자", "description": "5개 이상 언어 사용", "level": "gold"})
        elif languages_used >= 3:
            badges.append({"name": "언어 탐험가", "description": "3개 이상 언어 사용", "level": "silver"})
        
        # 성능 배지
        avg_performance = sum(e.performance_score for e in user_executions) / len(user_executions)
        if avg_performance >= 80:
            badges.append({"name": "성능 최적화 전문가", "description": "평균 80점 이상", "level": "gold"})
        elif avg_performance >= 60:
            badges.append({"name": "성능 개선자", "description": "평균 60점 이상", "level": "silver"})
        
        return badges
    
    def _get_recent_activity(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 활동 목록"""
        if not self.history_enabled:
            return []
        
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        recent_executions = sorted(user_executions, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        activities = []
        for execution in recent_executions:
            activities.append({
                "timestamp": execution.timestamp,
                "language": execution.language,
                "success": execution.success,
                "performance_score": execution.performance_score,
                "complexity_level": execution.complexity_level,
                "code_preview": execution.code[:100] + "..." if len(execution.code) > 100 else execution.code
            })
        
        return activities
    
    def _calculate_goals_progress(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """목표 달성 진행률 계산"""
        if not self.history_enabled:
            return {}
        
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        
        goals = {
            "execution_count": {
                "current": len(user_executions),
                "target": 50,
                "description": "50회 코드 실행 달성"
            },
            "success_rate": {
                "current": len([e for e in user_executions if e.success]) / len(user_executions) * 100 if user_executions else 0,
                "target": 80,
                "description": "80% 성공률 달성"
            },
            "language_diversity": {
                "current": len(set(e.language for e in user_executions)),
                "target": 5,
                "description": "5개 언어 마스터"
            },
            "performance_average": {
                "current": sum(e.performance_score for e in user_executions) / len(user_executions) if user_executions else 0,
                "target": 75,
                "description": "평균 75점 이상 달성"
            }
        }
        
        # 진행률 계산
        for goal in goals.values():
            goal["progress"] = min(100, (goal["current"] / goal["target"]) * 100)
            goal["completed"] = goal["current"] >= goal["target"]
        
        return goals
    
    def _suggest_next_challenges(self, user_id: str, language: Optional[str] = None) -> List[Dict[str, str]]:
        """다음 도전 과제 제안"""
        if not self.history_enabled:
            return []
        
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        if language:
            user_executions = [e for e in user_executions if e.language == language]
        
        challenges = []
        
        if not user_executions:
            challenges.append({
                "title": "첫 코드 실행하기",
                "description": "첫 번째 코드를 성공적으로 실행해보세요!",
                "difficulty": "beginner"
            })
            return challenges
        
        # 복잡도 기반 도전
        complexity_levels = [e.complexity_level for e in user_executions]
        if 'advanced' not in complexity_levels:
            challenges.append({
                "title": "고급 코드 작성하기",
                "description": "클래스나 복잡한 알고리즘을 사용한 코드를 작성해보세요",
                "difficulty": "advanced"
            })
        
        # 성능 개선 도전
        avg_performance = sum(e.performance_score for e in user_executions) / len(user_executions)
        if avg_performance < 70:
            challenges.append({
                "title": "성능 최적화 도전",
                "description": "코드 최적화를 통해 성능 점수 70점 이상을 달성해보세요",
                "difficulty": "intermediate"
            })
        
        # 새로운 언어 도전
        languages_used = set(e.language for e in user_executions)
        available_languages = {'python', 'javascript', 'java', 'cpp', 'go', 'rust', 'php', 'ruby', 'typescript', 'csharp'}
        unused_languages = available_languages - languages_used
        
        if unused_languages:
            suggested_lang = list(unused_languages)[0]
            challenges.append({
                "title": f"{suggested_lang.title()} 도전",
                "description": f"새로운 언어 {suggested_lang}로 코드를 작성해보세요",
                "difficulty": "beginner"
            })
        
        # 연속 성공 도전
        current_streak = self._calculate_current_streak(user_id)
        if current_streak < 5:
            challenges.append({
                "title": "연속 성공 도전",
                "description": "5회 연속 성공적인 코드 실행을 달성해보세요",
                "difficulty": "intermediate"
            })
        
        return challenges[:3]  # 최대 3개 제안
    
    def get_portfolio_showcase(self, user_id: str, language: Optional[str] = None) -> Dict[str, Any]:
        """사용자 포트폴리오 쇼케이스"""
        if not self.history_enabled:
            return {"error": "히스토리 관리 기능이 비활성화되어 있습니다."}
        
        try:
            portfolio_items = self.history_manager.get_featured_code_portfolio(user_id, language)
            
            showcase = {
                "user_id": user_id,
                "portfolio_count": len(portfolio_items),
                "featured_codes": portfolio_items,
                "statistics": {
                    "avg_performance_score": sum(item['performance_score'] for item in portfolio_items) / len(portfolio_items) if portfolio_items else 0,
                    "languages_featured": len(set(item['language'] for item in portfolio_items)),
                    "complexity_distribution": {
                        level: len([item for item in portfolio_items if item['complexity_level'] == level])
                        for level in ['beginner', 'intermediate', 'advanced']
                    }
                }
            }
            
            return showcase
            
        except Exception as e:
            return {"error": f"포트폴리오 쇼케이스 생성 중 오류 발생: {str(e)}"}
    
    def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """학습 인사이트 및 분석"""
        if not self.history_enabled:
            return {"error": "히스토리 관리 기능이 비활성화되어 있습니다."}
        
        try:
            # 기본 진행 리포트
            progress_report = self.history_manager.get_user_progress_report(user_id)
            
            # 추가 인사이트 계산
            insights = {
                "learning_velocity": self._calculate_learning_velocity(user_id),
                "strength_analysis": self._analyze_strengths(user_id),
                "improvement_areas": self._identify_improvement_areas(user_id),
                "time_investment": self._calculate_time_investment(user_id),
                "milestone_timeline": self._get_milestone_timeline(user_id)
            }
            
            # 전체 인사이트 패키지
            learning_insights = {
                "user_id": user_id,
                "analysis_date": progress_report.get("report_generated"),
                "overall_progress": progress_report.get("summary", {}),
                "detailed_insights": insights,
                "recommendations": progress_report.get("recommendations", [])
            }
            
            return learning_insights
            
        except Exception as e:
            return {"error": f"학습 인사이트 생성 중 오류 발생: {str(e)}"}
    
    def _calculate_learning_velocity(self, user_id: str) -> Dict[str, Any]:
        """학습 속도 분석"""
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        
        if len(user_executions) < 5:
            return {"status": "insufficient_data", "message": "분석을 위한 충분한 데이터가 없습니다."}
        
        # 최근 10개 실행의 성능 변화
        recent_executions = sorted(user_executions, key=lambda x: x.timestamp)[-10:]
        performance_scores = [e.performance_score for e in recent_executions]
        
        # 선형 추세 계산
        n = len(performance_scores)
        x_values = list(range(n))
        slope = (n * sum(x * y for x, y in zip(x_values, performance_scores)) - sum(x_values) * sum(performance_scores)) / \
                (n * sum(x * x for x in x_values) - sum(x_values) ** 2)
        
        velocity_status = "improving" if slope > 1 else "stable" if slope > -1 else "declining"
        
        return {
            "status": velocity_status,
            "slope": slope,
            "recent_trend": performance_scores,
            "message": f"최근 학습 속도가 {velocity_status} 상태입니다."
        }
    
    def _analyze_strengths(self, user_id: str) -> List[Dict[str, Any]]:
        """강점 분석"""
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        
        if not user_executions:
            return []
        
        strengths = []
        
        # 언어별 성과 분석
        from collections import defaultdict
        lang_performance = defaultdict(list)
        for execution in user_executions:
            lang_performance[execution.language].append(execution.performance_score)
        
        for language, scores in lang_performance.items():
            avg_score = sum(scores) / len(scores)
            if avg_score >= 75:
                strengths.append({
                    "category": "language_proficiency",
                    "description": f"{language} 언어에서 우수한 성과 (평균 {avg_score:.1f}점)",
                    "score": avg_score
                })
        
        # 복잡도별 성과
        complexity_performance = defaultdict(list)
        for execution in user_executions:
            complexity_performance[execution.complexity_level].append(execution.performance_score)
        
        for complexity, scores in complexity_performance.items():
            if len(scores) >= 3:  # 충분한 샘플
                avg_score = sum(scores) / len(scores)
                if avg_score >= 70:
                    strengths.append({
                        "category": "complexity_handling",
                        "description": f"{complexity} 레벨 코드 처리 능력 우수 (평균 {avg_score:.1f}점)",
                        "score": avg_score
                    })
        
        return sorted(strengths, key=lambda x: x['score'], reverse=True)
    
    def _identify_improvement_areas(self, user_id: str) -> List[Dict[str, Any]]:
        """개선 영역 식별"""
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        
        if not user_executions:
            return []
        
        improvements = []
        
        # 성공률 분석
        success_rate = len([e for e in user_executions if e.success]) / len(user_executions)
        if success_rate < 0.7:
            improvements.append({
                "category": "success_rate",
                "description": f"코드 성공률 개선 필요 (현재 {success_rate*100:.1f}%)",
                "priority": "high",
                "suggestion": "기본 문법과 디버깅 스킬을 더 연습해보세요."
            })
        
        # 성능 점수 분석
        avg_performance = sum(e.performance_score for e in user_executions) / len(user_executions)
        if avg_performance < 60:
            improvements.append({
                "category": "performance",
                "description": f"코드 성능 최적화 필요 (평균 {avg_performance:.1f}점)",
                "priority": "medium",
                "suggestion": "알고리즘 효율성과 메모리 사용량을 개선해보세요."
            })
        
        # 복잡도 다양성
        complexity_levels = set(e.complexity_level for e in user_executions)
        if 'advanced' not in complexity_levels and len(user_executions) > 10:
            improvements.append({
                "category": "complexity",
                "description": "더 복잡한 코드 도전 필요",
                "priority": "low",
                "suggestion": "객체지향 프로그래밍이나 고급 알고리즘에 도전해보세요."
            })
        
        return improvements
    
    def _calculate_time_investment(self, user_id: str) -> Dict[str, Any]:
        """시간 투자 분석"""
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        
        if not user_executions:
            return {"total_sessions": 0, "estimated_hours": 0}
        
        # 일별 활동 계산
        from collections import defaultdict
        daily_activity = defaultdict(int)
        for execution in user_executions:
            date = execution.timestamp[:10]  # YYYY-MM-DD
            daily_activity[date] += 1
        
        return {
            "total_sessions": len(user_executions),
            "estimated_hours": len(user_executions) * 0.5,  # 세션당 30분 추정
            "active_days": len(daily_activity),
            "avg_sessions_per_day": len(user_executions) / len(daily_activity) if daily_activity else 0,
            "consistency_score": min(100, len(daily_activity) * 2)  # 활동 일수 기반
        }
    
    def _get_milestone_timeline(self, user_id: str) -> List[Dict[str, Any]]:
        """마일스톤 타임라인"""
        user_milestones = [m for m in self.history_manager.milestones if m.user_id == user_id]
        
        timeline = []
        for milestone in sorted(user_milestones, key=lambda x: x.achieved_date):
            timeline.append({
                "date": milestone.achieved_date,
                "type": milestone.milestone_type,
                "description": milestone.description,
                "language": milestone.language
            })
        
        return timeline

    # 추가 필요한 메서드들
    async def execute_code_with_history(self, code: str, language: str, user_id: str = "default_user") -> ExecutionResult:
        """히스토리 추적이 포함된 코드 실행"""
        try:
            # 기본 코드 실행
            result = await self.execute_code(code, language)
            
            # 히스토리에 기록 (가능한 경우)
            if self.history_enabled:
                execution_data = {
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "memory_usage": result.memory_usage,
                    "performance_score": result.performance_score,
                    "output": result.output,
                    "error": result.error,
                    "return_code": result.return_code,
                    "optimization_suggestions": result.optimization_suggestions,
                    "dependencies_detected": result.dependencies_detected
                }
                
                self.history_manager.add_execution_record(
                    user_id=user_id,
                    language=language,
                    code=code,
                    execution_result=execution_data
                )
            
            return result
            
        except Exception as e:
            # 실패한 경우에도 기본 ExecutionResult 반환
            return ExecutionResult(
                success=False,
                language=language,
                output="",
                error=str(e),
                execution_time=0.0,
                memory_usage=0,
                return_code=-1,
                performance_score=0.0,
                optimization_suggestions=[],
                dependencies_detected=[]
            )
    
    def get_user_execution_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """사용자별 실행 히스토리 조회"""
        if not self.history_enabled:
            return []
        
        user_executions = [e for e in self.history_manager.executions if e.user_id == user_id]
        recent_executions = sorted(user_executions, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        return [asdict(execution) for execution in recent_executions]
    
    def get_user_growth_report(self, user_id: str, language: Optional[str] = None) -> Dict[str, Any]:
        """사용자 성장 리포트 생성"""
        if not self.history_enabled:
            return {"error": "히스토리 관리 기능이 비활성화되어 있습니다."}
        
        return self.history_manager.get_user_progress_report(user_id, language)

# 전역 인스턴스
enhanced_executor = EnhancedCodeExecutor() if MODULES_AVAILABLE else None