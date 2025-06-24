"""
코드 실행 히스토리 관리 및 성장 추적 시스템
사용자별 코드 실행 포트폴리오, 성장 추적, 우수 코드 큐레이션 기능 제공
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics

@dataclass
class CodeExecution:
    """개별 코드 실행 기록"""
    execution_id: str
    user_id: str
    timestamp: str
    language: str
    code: str
    code_hash: str
    success: bool
    execution_time: float
    memory_usage: int
    performance_score: float
    complexity_level: str  # 'beginner', 'intermediate', 'advanced'
    code_length: int
    dependencies: List[str]
    optimization_suggestions: List[str]
    ai_review_score: Optional[float] = None
    ai_review_grade: Optional[str] = None
    tags: List[str] = None

@dataclass
class SkillProgressMetrics:
    """언어별 실력 진척 지표"""
    language: str
    total_executions: int
    successful_executions: int
    success_rate: float
    avg_performance_score: float
    complexity_progression: List[str]  # 시간순 복잡도 레벨
    skill_level: str  # 'novice', 'beginner', 'intermediate', 'advanced', 'expert'
    estimated_hours: float
    best_performance_score: float
    recent_trend: str  # 'improving', 'stable', 'declining'

@dataclass
class LearningMilestone:
    """학습 마일스톤"""
    milestone_id: str
    user_id: str
    language: str
    milestone_type: str  # 'first_success', 'complexity_upgrade', 'performance_achievement'
    description: str
    achieved_date: str
    related_execution_id: str

@dataclass
class CodePortfolioItem:
    """우수 코드 포트폴리오 항목"""
    portfolio_id: str
    user_id: str
    execution_id: str
    language: str
    title: str
    description: str
    code: str
    performance_score: float
    ai_review_score: float
    complexity_level: str
    featured_date: str
    tags: List[str]

class CodeHistoryManager:
    """코드 실행 히스토리 및 성장 추적 관리자"""
    
    def __init__(self, data_dir: str = "data/history"):
        self.data_dir = data_dir
        self.executions_file = os.path.join(data_dir, "code_executions.json")
        self.portfolios_file = os.path.join(data_dir, "code_portfolios.json")
        self.milestones_file = os.path.join(data_dir, "learning_milestones.json")
        self.user_stats_file = os.path.join(data_dir, "user_statistics.json")
        
        # 데이터 저장소 초기화
        self._ensure_data_directory()
        self.executions: List[CodeExecution] = self._load_executions()
        self.portfolios: List[CodePortfolioItem] = self._load_portfolios()
        self.milestones: List[LearningMilestone] = self._load_milestones()
        self.user_stats: Dict[str, Any] = self._load_user_stats()
        
        # 성능 기준점
        self.performance_thresholds = {
            'excellent': 85.0,
            'good': 70.0,
            'average': 50.0,
            'poor': 30.0
        }
        
        # 스킬 레벨 기준
        self.skill_level_criteria = {
            'novice': {'min_executions': 0, 'min_success_rate': 0.0, 'min_avg_score': 0.0},
            'beginner': {'min_executions': 5, 'min_success_rate': 0.4, 'min_avg_score': 40.0},
            'intermediate': {'min_executions': 20, 'min_success_rate': 0.6, 'min_avg_score': 60.0},
            'advanced': {'min_executions': 50, 'min_success_rate': 0.8, 'min_avg_score': 75.0},
            'expert': {'min_executions': 100, 'min_success_rate': 0.9, 'min_avg_score': 85.0}
        }
    
    def _ensure_data_directory(self):
        """데이터 디렉토리 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_executions(self) -> List[CodeExecution]:
        """실행 기록 로드"""
        if os.path.exists(self.executions_file):
            try:
                with open(self.executions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [CodeExecution(**item) for item in data]
            except Exception as e:
                print(f"실행 기록 로드 오류: {e}")
        return []
    
    def _load_portfolios(self) -> List[CodePortfolioItem]:
        """포트폴리오 로드"""
        if os.path.exists(self.portfolios_file):
            try:
                with open(self.portfolios_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [CodePortfolioItem(**item) for item in data]
            except Exception as e:
                print(f"포트폴리오 로드 오류: {e}")
        return []
    
    def _load_milestones(self) -> List[LearningMilestone]:
        """마일스톤 로드"""
        if os.path.exists(self.milestones_file):
            try:
                with open(self.milestones_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [LearningMilestone(**item) for item in data]
            except Exception as e:
                print(f"마일스톤 로드 오류: {e}")
        return []
    
    def _load_user_stats(self) -> Dict[str, Any]:
        """사용자 통계 로드"""
        if os.path.exists(self.user_stats_file):
            try:
                with open(self.user_stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"사용자 통계 로드 오류: {e}")
        return {}
    
    def _save_executions(self):
        """실행 기록 저장"""
        try:
            with open(self.executions_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(execution) for execution in self.executions], f, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"실행 기록 저장 오류: {e}")
    
    def _save_portfolios(self):
        """포트폴리오 저장"""
        try:
            with open(self.portfolios_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(portfolio) for portfolio in self.portfolios], f, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"포트폴리오 저장 오류: {e}")
    
    def _save_milestones(self):
        """마일스톤 저장"""
        try:
            with open(self.milestones_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(milestone) for milestone in self.milestones], f, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"마일스톤 저장 오류: {e}")
    
    def _save_user_stats(self):
        """사용자 통계 저장"""
        try:
            with open(self.user_stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"사용자 통계 저장 오류: {e}")
    
    def _generate_code_hash(self, code: str) -> str:
        """코드 해시 생성 (중복 검사용)"""
        return hashlib.md5(code.encode('utf-8')).hexdigest()
    
    def _determine_complexity_level(self, code: str, language: str, performance_score: float) -> str:
        """코드 복잡도 레벨 판정"""
        code_length = len(code)
        
        # 기본 복잡도 계산 요소들
        complexity_indicators = {
            'length': code_length,
            'lines': len(code.split('\n')),
            'functions': len([line for line in code.split('\n') if 'def ' in line or 'function ' in line or 'class ' in line]),
            'loops': len([line for line in code.split('\n') if any(keyword in line for keyword in ['for ', 'while ', 'forEach'])]),
            'conditionals': len([line for line in code.split('\n') if any(keyword in line for keyword in ['if ', 'else', 'switch'])]),
            'imports': len([line for line in code.split('\n') if any(keyword in line for keyword in ['import ', 'require(', '#include'])])
        }
        
        # 언어별 가중치 적용
        language_weights = {
            'python': {'length': 1.0, 'functions': 2.0, 'loops': 1.5, 'conditionals': 1.5},
            'javascript': {'length': 1.2, 'functions': 2.5, 'loops': 1.8, 'conditionals': 1.6},
            'java': {'length': 0.8, 'functions': 3.0, 'loops': 2.0, 'conditionals': 1.8},
            'cpp': {'length': 0.9, 'functions': 2.8, 'loops': 2.2, 'conditionals': 2.0},
        }
        
        weights = language_weights.get(language, {'length': 1.0, 'functions': 2.0, 'loops': 1.5, 'conditionals': 1.5})
        
        # 복잡도 점수 계산
        complexity_score = (
            complexity_indicators['length'] * weights.get('length', 1.0) / 100 +
            complexity_indicators['functions'] * weights.get('functions', 2.0) +
            complexity_indicators['loops'] * weights.get('loops', 1.5) +
            complexity_indicators['conditionals'] * weights.get('conditionals', 1.5) +
            complexity_indicators['imports'] * 0.5
        )
        
        # 성능 점수도 고려
        adjusted_score = complexity_score * (1 + performance_score / 100)
        
        # 복잡도 레벨 결정
        if adjusted_score < 5:
            return 'beginner'
        elif adjusted_score < 15:
            return 'intermediate'
        else:
            return 'advanced'
    
    def add_execution_record(self, user_id: str, language: str, code: str, 
                           execution_result: Dict[str, Any], ai_review_result: Optional[Dict[str, Any]] = None) -> str:
        """새로운 코드 실행 기록 추가"""
        
        execution_id = f"{user_id}_{language}_{int(time.time())}_{len(self.executions)}"
        code_hash = self._generate_code_hash(code)
        
        # 복잡도 레벨 판정
        complexity_level = self._determine_complexity_level(code, language, execution_result.get('performance_score', 0))
        
        # AI 리뷰 결과 추출
        ai_review_score = None
        ai_review_grade = None
        if ai_review_result and ai_review_result.get('ai_review_available', False):
            ai_review_score = ai_review_result.get('ai_overall_quality', 0)
            ai_review_grade = ai_review_result.get('ai_code_grade', 'Unknown')
        
        # 실행 기록 생성
        execution = CodeExecution(
            execution_id=execution_id,
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            language=language,
            code=code,
            code_hash=code_hash,
            success=execution_result.get('success', False),
            execution_time=execution_result.get('execution_time', 0.0),
            memory_usage=execution_result.get('memory_usage', 0),
            performance_score=execution_result.get('performance_score', 0.0),
            complexity_level=complexity_level,
            code_length=len(code),
            dependencies=execution_result.get('dependencies_detected', []),
            optimization_suggestions=execution_result.get('optimization_suggestions', []),
            ai_review_score=ai_review_score,
            ai_review_grade=ai_review_grade,
            tags=[]
        )
        
        # 기록 추가
        self.executions.append(execution)
        
        # 마일스톤 확인 및 생성
        self._check_and_create_milestones(user_id, execution)
        
        # 우수 코드 자동 선별
        self._evaluate_for_portfolio(execution)
        
        # 사용자 통계 업데이트
        self._update_user_statistics(user_id)
        
        # 데이터 저장
        self._save_executions()
        self._save_milestones()
        self._save_portfolios()
        self._save_user_stats()
        
        return execution_id
    
    def _check_and_create_milestones(self, user_id: str, execution: CodeExecution):
        """마일스톤 확인 및 생성"""
        user_executions = [e for e in self.executions if e.user_id == user_id]
        language_executions = [e for e in user_executions if e.language == execution.language]
        
        # 첫 번째 성공적 실행
        if execution.success and len([e for e in language_executions if e.success]) == 1:
            milestone = LearningMilestone(
                milestone_id=f"first_success_{user_id}_{execution.language}_{int(time.time())}",
                user_id=user_id,
                language=execution.language,
                milestone_type="first_success",
                description=f"{execution.language} 첫 번째 성공적 코드 실행",
                achieved_date=execution.timestamp,
                related_execution_id=execution.execution_id
            )
            self.milestones.append(milestone)
        
        # 복잡도 승급
        previous_complexity_levels = [e.complexity_level for e in language_executions[:-1]]
        if execution.complexity_level == 'intermediate' and 'intermediate' not in previous_complexity_levels:
            milestone = LearningMilestone(
                milestone_id=f"complexity_intermediate_{user_id}_{execution.language}_{int(time.time())}",
                user_id=user_id,
                language=execution.language,
                milestone_type="complexity_upgrade",
                description=f"{execution.language} 중급 레벨 코드 작성 달성",
                achieved_date=execution.timestamp,
                related_execution_id=execution.execution_id
            )
            self.milestones.append(milestone)
        elif execution.complexity_level == 'advanced' and 'advanced' not in previous_complexity_levels:
            milestone = LearningMilestone(
                milestone_id=f"complexity_advanced_{user_id}_{execution.language}_{int(time.time())}",
                user_id=user_id,
                language=execution.language,
                milestone_type="complexity_upgrade",
                description=f"{execution.language} 고급 레벨 코드 작성 달성",
                achieved_date=execution.timestamp,
                related_execution_id=execution.execution_id
            )
            self.milestones.append(milestone)
        
        # 성능 달성
        if execution.performance_score >= self.performance_thresholds['excellent']:
            excellent_count = len([e for e in language_executions if e.performance_score >= self.performance_thresholds['excellent']])
            if excellent_count == 1:  # 첫 번째 우수 성능
                milestone = LearningMilestone(
                    milestone_id=f"performance_excellent_{user_id}_{execution.language}_{int(time.time())}",
                    user_id=user_id,
                    language=execution.language,
                    milestone_type="performance_achievement",
                    description=f"{execution.language} 우수 성능 점수 ({execution.performance_score:.1f}점) 달성",
                    achieved_date=execution.timestamp,
                    related_execution_id=execution.execution_id
                )
                self.milestones.append(milestone)
    
    def _evaluate_for_portfolio(self, execution: CodeExecution):
        """우수 코드 포트폴리오 선별 평가"""
        # 포트폴리오 선별 기준
        criteria_met = 0
        total_criteria = 4
        
        # 1. 성능 점수 기준
        if execution.performance_score >= self.performance_thresholds['good']:
            criteria_met += 1
        
        # 2. 성공적 실행
        if execution.success:
            criteria_met += 1
        
        # 3. 복잡도 기준 (중급 이상)
        if execution.complexity_level in ['intermediate', 'advanced']:
            criteria_met += 1
        
        # 4. AI 리뷰 점수 기준
        if execution.ai_review_score and execution.ai_review_score >= 70:
            criteria_met += 1
        
        # 기준의 75% 이상 충족 시 포트폴리오에 추가
        if criteria_met >= total_criteria * 0.75:
            # 중복 확인 (같은 사용자의 동일한 코드)
            existing = [p for p in self.portfolios 
                       if p.user_id == execution.user_id and 
                       self._generate_code_hash(p.code) == execution.code_hash]
            
            if not existing:
                portfolio_item = CodePortfolioItem(
                    portfolio_id=f"portfolio_{execution.user_id}_{execution.language}_{int(time.time())}",
                    user_id=execution.user_id,
                    execution_id=execution.execution_id,
                    language=execution.language,
                    title=f"{execution.language} 우수 코드 #{len(self.portfolios) + 1}",
                    description=f"성능 점수: {execution.performance_score:.1f}, 복잡도: {execution.complexity_level}",
                    code=execution.code,
                    performance_score=execution.performance_score,
                    ai_review_score=execution.ai_review_score or 0,
                    complexity_level=execution.complexity_level,
                    featured_date=execution.timestamp,
                    tags=[execution.complexity_level, execution.language, f"score_{int(execution.performance_score)}"]
                )
                self.portfolios.append(portfolio_item)
    
    def _update_user_statistics(self, user_id: str):
        """사용자 통계 업데이트"""
        user_executions = [e for e in self.executions if e.user_id == user_id]
        
        if not user_executions:
            return
        
        # 언어별 통계
        language_stats = {}
        for language in set(e.language for e in user_executions):
            lang_executions = [e for e in user_executions if e.language == language]
            successful_executions = [e for e in lang_executions if e.success]
            
            if lang_executions:
                language_stats[language] = {
                    'total_executions': len(lang_executions),
                    'successful_executions': len(successful_executions),
                    'success_rate': len(successful_executions) / len(lang_executions),
                    'avg_performance_score': statistics.mean([e.performance_score for e in lang_executions]),
                    'best_performance_score': max([e.performance_score for e in lang_executions]),
                    'complexity_progression': [e.complexity_level for e in lang_executions[-10:]],  # 최근 10개
                    'estimated_hours': len(lang_executions) * 0.5,  # 실행당 평균 30분 추정
                    'recent_trend': self._calculate_trend([e.performance_score for e in lang_executions[-5:]]),
                    'skill_level': self._determine_skill_level(language_stats.get(language, {}))
                }
        
        # 전체 사용자 통계
        self.user_stats[user_id] = {
            'total_executions': len(user_executions),
            'total_successful_executions': len([e for e in user_executions if e.success]),
            'overall_success_rate': len([e for e in user_executions if e.success]) / len(user_executions),
            'languages_used': list(set(e.language for e in user_executions)),
            'avg_performance_score': statistics.mean([e.performance_score for e in user_executions]),
            'language_statistics': language_stats,
            'milestones_achieved': len([m for m in self.milestones if m.user_id == user_id]),
            'portfolio_items': len([p for p in self.portfolios if p.user_id == user_id]),
            'last_activity': max([e.timestamp for e in user_executions]),
            'updated_at': datetime.now().isoformat()
        }
    
    def _calculate_trend(self, recent_scores: List[float]) -> str:
        """최근 성능 트렌드 계산"""
        if len(recent_scores) < 3:
            return 'insufficient_data'
        
        # 선형 회귀를 통한 트렌드 분석
        n = len(recent_scores)
        x_values = list(range(n))
        
        # 기울기 계산
        slope = (n * sum(x * y for x, y in zip(x_values, recent_scores)) - sum(x_values) * sum(recent_scores)) / \
                (n * sum(x * x for x in x_values) - sum(x_values) ** 2)
        
        if slope > 2:
            return 'improving'
        elif slope < -2:
            return 'declining'
        else:
            return 'stable'
    
    def _determine_skill_level(self, language_stats: Dict[str, Any]) -> str:
        """언어별 스킬 레벨 결정"""
        if not language_stats:
            return 'novice'
        
        total_executions = language_stats.get('total_executions', 0)
        success_rate = language_stats.get('success_rate', 0.0)
        avg_score = language_stats.get('avg_performance_score', 0.0)
        
        for level in ['expert', 'advanced', 'intermediate', 'beginner', 'novice']:
            criteria = self.skill_level_criteria[level]
            if (total_executions >= criteria['min_executions'] and
                success_rate >= criteria['min_success_rate'] and
                avg_score >= criteria['min_avg_score']):
                return level
        
        return 'novice'
    
    def get_user_progress_report(self, user_id: str, language: Optional[str] = None) -> Dict[str, Any]:
        """사용자 성장 리포트 생성"""
        user_executions = [e for e in self.executions if e.user_id == user_id]
        
        if language:
            user_executions = [e for e in user_executions if e.language == language]
        
        if not user_executions:
            return {"error": "해당 사용자의 실행 기록이 없습니다."}
        
        # 기본 통계
        successful_executions = [e for e in user_executions if e.success]
        
        # 시간별 진행 상황
        executions_by_month = defaultdict(list)
        for execution in user_executions:
            month_key = execution.timestamp[:7]  # YYYY-MM
            executions_by_month[month_key].append(execution)
        
        # 복잡도별 분포
        complexity_distribution = Counter([e.complexity_level for e in user_executions])
        
        # 성능 향상 추이
        performance_trend = [e.performance_score for e in user_executions[-20:]]  # 최근 20개
        
        # 언어별 숙련도
        language_proficiency = {}
        if not language:  # 전체 언어 분석
            for lang in set(e.language for e in user_executions):
                lang_executions = [e for e in user_executions if e.language == lang]
                language_proficiency[lang] = SkillProgressMetrics(
                    language=lang,
                    total_executions=len(lang_executions),
                    successful_executions=len([e for e in lang_executions if e.success]),
                    success_rate=len([e for e in lang_executions if e.success]) / len(lang_executions),
                    avg_performance_score=statistics.mean([e.performance_score for e in lang_executions]),
                    complexity_progression=[e.complexity_level for e in lang_executions],
                    skill_level=self._determine_skill_level({
                        'total_executions': len(lang_executions),
                        'success_rate': len([e for e in lang_executions if e.success]) / len(lang_executions),
                        'avg_performance_score': statistics.mean([e.performance_score for e in lang_executions])
                    }),
                    estimated_hours=len(lang_executions) * 0.5,
                    best_performance_score=max([e.performance_score for e in lang_executions]),
                    recent_trend=self._calculate_trend([e.performance_score for e in lang_executions[-5:]])
                )
        
        # 마일스톤 달성 현황
        user_milestones = [m for m in self.milestones if m.user_id == user_id]
        if language:
            user_milestones = [m for m in user_milestones if m.language == language]
        
        return {
            "user_id": user_id,
            "report_language": language or "all",
            "report_generated": datetime.now().isoformat(),
            "summary": {
                "total_executions": len(user_executions),
                "successful_executions": len(successful_executions),
                "success_rate": len(successful_executions) / len(user_executions) * 100,
                "avg_performance_score": statistics.mean([e.performance_score for e in user_executions]),
                "languages_explored": len(set(e.language for e in user_executions)),
                "estimated_total_hours": len(user_executions) * 0.5
            },
            "progress_metrics": {
                "complexity_distribution": dict(complexity_distribution),
                "performance_trend": performance_trend,
                "monthly_activity": {month: len(execs) for month, execs in executions_by_month.items()},
                "recent_improvement": self._calculate_trend(performance_trend)
            },
            "language_proficiency": {lang: asdict(metrics) for lang, metrics in language_proficiency.items()},
            "milestones_achieved": [asdict(m) for m in user_milestones],
            "portfolio_highlights": [asdict(p) for p in self.portfolios if p.user_id == user_id][:5],
            "recommendations": self._generate_learning_recommendations(user_id, language)
        }
    
    def _generate_learning_recommendations(self, user_id: str, language: Optional[str] = None) -> List[Dict[str, str]]:
        """개인화된 학습 추천 생성"""
        user_executions = [e for e in self.executions if e.user_id == user_id]
        if language:
            user_executions = [e for e in user_executions if e.language == language]
        
        recommendations = []
        
        if not user_executions:
            return [{"type": "general", "message": "첫 번째 코드를 실행해보세요!"}]
        
        # 성공률 기반 추천
        success_rate = len([e for e in user_executions if e.success]) / len(user_executions)
        if success_rate < 0.5:
            recommendations.append({
                "type": "skill_improvement",
                "message": "기본 문법을 더 연습해보세요. 성공률을 높이는 것이 우선입니다."
            })
        
        # 복잡도 기반 추천
        recent_complexity = [e.complexity_level for e in user_executions[-5:]]
        if all(level == 'beginner' for level in recent_complexity) and len(user_executions) > 10:
            recommendations.append({
                "type": "complexity_upgrade",
                "message": "더 복잡한 문제에 도전해보세요. 함수나 클래스를 사용한 코드를 작성해보세요."
            })
        
        # 성능 기반 추천
        avg_performance = statistics.mean([e.performance_score for e in user_executions])
        if avg_performance < 60:
            recommendations.append({
                "type": "performance_improvement",
                "message": "코드 최적화에 신경써보세요. 알고리즘의 효율성을 개선해보세요."
            })
        
        # 언어 다양성 추천
        languages_used = set(e.language for e in user_executions)
        if len(languages_used) == 1 and len(user_executions) > 15:
            recommendations.append({
                "type": "language_diversification",
                "message": "새로운 프로그래밍 언어를 시도해보세요. 다른 패러다임을 경험할 수 있습니다."
            })
        
        return recommendations
    
    def get_featured_code_portfolio(self, user_id: Optional[str] = None, language: Optional[str] = None, 
                                  limit: int = 10) -> List[Dict[str, Any]]:
        """우수 코드 포트폴리오 조회"""
        filtered_portfolios = self.portfolios
        
        if user_id:
            filtered_portfolios = [p for p in filtered_portfolios if p.user_id == user_id]
        
        if language:
            filtered_portfolios = [p for p in filtered_portfolios if p.language == language]
        
        # 성능 점수 기준으로 정렬
        sorted_portfolios = sorted(filtered_portfolios, 
                                 key=lambda p: (p.performance_score, p.ai_review_score), 
                                 reverse=True)
        
        return [asdict(portfolio) for portfolio in sorted_portfolios[:limit]]
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """전체 시스템 통계"""
        if not self.executions:
            return {
                "total_executions": 0,
                "active_users": 0,
                "supported_languages": 0,
                "language_distribution": {}
            }
        
        # 기본 통계
        total_executions = len(self.executions)
        successful_executions = len([e for e in self.executions if e.success])
        unique_users = len(set(e.user_id for e in self.executions))
        
        # 언어별 통계
        language_usage = Counter([e.language for e in self.executions])
        
        # 복잡도별 분포
        complexity_distribution = Counter([e.complexity_level for e in self.executions])
        
        # 성능 분포
        performance_scores = [e.performance_score for e in self.executions]
        
        return {
            "total_executions": total_executions,
            "active_users": unique_users,
            "supported_languages": len(language_usage),
            "language_distribution": dict(language_usage),
            "system_overview": {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "success_rate": successful_executions / total_executions * 100,
                "unique_users": unique_users,
                "total_milestones": len(self.milestones),
                "portfolio_items": len(self.portfolios)
            },
            "language_statistics": dict(language_usage),
            "complexity_distribution": dict(complexity_distribution),
            "performance_statistics": {
                "average_score": statistics.mean(performance_scores),
                "median_score": statistics.median(performance_scores),
                "highest_score": max(performance_scores),
                "lowest_score": min(performance_scores)
            },
            "recent_activity": {
                "last_24h": len([e for e in self.executions 
                               if (datetime.now() - datetime.fromisoformat(e.timestamp)).days < 1]),
                "last_week": len([e for e in self.executions 
                                if (datetime.now() - datetime.fromisoformat(e.timestamp)).days < 7]),
                "last_month": len([e for e in self.executions 
                                 if (datetime.now() - datetime.fromisoformat(e.timestamp)).days < 30])
            }
        }
    
    def get_global_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """글로벌 리더보드 생성"""
        if not self.executions:
            return []
        
        # 사용자별 통계 계산
        user_stats = {}
        for execution in self.executions:
            user_id = execution.user_id
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "user_id": user_id,
                    "total_executions": 0,
                    "successful_executions": 0,
                    "total_score": 0.0,
                    "best_score": 0.0,
                    "languages_used": set(),
                    "milestones_count": 0
                }
            
            stats = user_stats[user_id]
            stats["total_executions"] += 1
            if execution.success:
                stats["successful_executions"] += 1
            stats["total_score"] += execution.performance_score
            stats["best_score"] = max(stats["best_score"], execution.performance_score)
            stats["languages_used"].add(execution.language)
        
        # 마일스톤 카운트 추가
        for milestone in self.milestones:
            if milestone.user_id in user_stats:
                user_stats[milestone.user_id]["milestones_count"] += 1
        
        # 리더보드 점수 계산 및 정렬
        leaderboard = []
        for user_id, stats in user_stats.items():
            success_rate = (stats["successful_executions"] / stats["total_executions"]) * 100 if stats["total_executions"] > 0 else 0
            avg_score = stats["total_score"] / stats["total_executions"] if stats["total_executions"] > 0 else 0
            
            # 종합 점수 계산 (성공률 + 평균 점수 + 보너스)
            composite_score = (
                avg_score * 0.4 +
                success_rate * 0.3 +
                len(stats["languages_used"]) * 5 +  # 언어 다양성 보너스
                stats["milestones_count"] * 3 +      # 마일스톤 보너스
                min(stats["total_executions"] / 10, 10)  # 활동량 보너스 (최대 10점)
            )
            
            leaderboard.append({
                "user_id": user_id,
                "total_score": composite_score,
                "execution_count": stats["total_executions"],
                "success_rate": success_rate,
                "avg_performance": avg_score,
                "best_score": stats["best_score"],
                "languages_mastered": len(stats["languages_used"]),
                "milestones_achieved": stats["milestones_count"]
            })
        
        # 점수순 정렬
        leaderboard.sort(key=lambda x: x["total_score"], reverse=True)
        
        return leaderboard[:limit]
    
    def get_curated_excellent_codes(self, limit: int = 10, language: Optional[str] = None, 
                                  min_performance_score: float = 80.0) -> List[Dict[str, Any]]:
        """우수 코드 큐레이션"""
        # 우수 코드 기준에 맞는 실행 결과 필터링
        excellent_executions = []
        
        for execution in self.executions:
            # 기본 조건: 성공적 실행 + 높은 성능 점수
            if (execution.success and 
                execution.performance_score >= min_performance_score):
                
                # 언어 필터링
                if language and execution.language != language:
                    continue
                
                # AI 리뷰 점수가 있으면 추가 고려
                ai_bonus = 0
                if execution.ai_review_score and execution.ai_review_score >= 80:
                    ai_bonus = 10
                
                # 복잡도 보너스
                complexity_bonus = {
                    'advanced': 15,
                    'intermediate': 10,
                    'beginner': 5
                }.get(execution.complexity_level, 0)
                
                # 코드 길이 적정성 (너무 짧거나 길지 않은 코드)
                length_score = 0
                if 20 <= execution.code_length <= 200:
                    length_score = 5
                elif 200 < execution.code_length <= 500:
                    length_score = 3
                
                # 종합 점수 계산
                total_score = (
                    execution.performance_score +
                    ai_bonus +
                    complexity_bonus +
                    length_score
                )
                
                excellent_executions.append({
                    "execution_id": execution.execution_id,
                    "user_id": execution.user_id,
                    "language": execution.language,
                    "code": execution.code,
                    "performance_score": execution.performance_score,
                    "ai_review_score": execution.ai_review_score,
                    "complexity_level": execution.complexity_level,
                    "code_length": execution.code_length,
                    "timestamp": execution.timestamp,
                    "total_score": total_score,
                    "optimization_suggestions": execution.optimization_suggestions,
                    "dependencies": execution.dependencies
                })
        
        # 종합 점수순으로 정렬
        excellent_executions.sort(key=lambda x: x["total_score"], reverse=True)
        
        return excellent_executions[:limit]

# 전역 인스턴스
history_manager = CodeHistoryManager()