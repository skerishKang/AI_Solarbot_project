"""
성능 벤치마크 및 최적화 제안 시스템
언어별 성능 패턴 분석, 알고리즘 복잡도 측정, 메모리 사용량 최적화 제안
"""

import os
import re
import json
import time
import hashlib
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import ast
import keyword

@dataclass
class BenchmarkResult:
    """벤치마크 결과 데이터 클래스"""
    execution_id: str
    language: str
    code_hash: str
    execution_time: float
    memory_usage: int
    cpu_usage: float
    performance_score: float
    complexity_score: int
    algorithm_complexity: str  # O(1), O(n), O(n^2), etc.
    optimization_level: str  # 'optimal', 'good', 'needs_improvement', 'poor'
    benchmark_category: str  # 'basic', 'algorithm', 'data_structure', 'io_intensive'
    comparative_ranking: float  # 0-100, 언어별 비교 순위
    timestamp: str

@dataclass
class OptimizationSuggestion:
    """최적화 제안 데이터 클래스"""
    suggestion_id: str
    category: str  # 'algorithm', 'memory', 'syntax', 'style', 'performance'
    severity: str  # 'critical', 'major', 'minor', 'info'
    title: str
    description: str
    code_example: Optional[str]
    estimated_improvement: str  # e.g., "20% faster", "50% less memory"
    difficulty: str  # 'easy', 'medium', 'hard'

@dataclass
class LanguageBenchmarkData:
    """언어별 벤치마크 기준 데이터"""
    language: str
    baseline_execution_time: Dict[str, float]  # complexity -> baseline time
    baseline_memory_usage: Dict[str, int]     # complexity -> baseline memory
    performance_multipliers: Dict[str, float] # feature -> multiplier
    common_patterns: List[str]
    optimization_rules: List[Dict[str, Any]]

class PerformanceBenchmark:
    """성능 벤치마크 및 최적화 제안 시스템"""
    
    def __init__(self, data_dir: str = "data/benchmark"):
        self.data_dir = data_dir
        self.benchmark_results = []
        self.language_baselines = self._initialize_language_baselines()
        self.optimization_patterns = self._initialize_optimization_patterns()
        self.complexity_patterns = self._initialize_complexity_patterns()
        
        # 데이터 로딩
        self._ensure_data_directory()
        self._load_benchmark_data()
    
    def _ensure_data_directory(self):
        """데이터 디렉토리 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _initialize_language_baselines(self) -> Dict[str, LanguageBenchmarkData]:
        """언어별 성능 기준선 초기화"""
        return {
            'python': LanguageBenchmarkData(
                language='python',
                baseline_execution_time={
                    'O(1)': 0.001,
                    'O(n)': 0.01,
                    'O(n^2)': 0.1,
                    'O(n^3)': 1.0,
                    'O(2^n)': 5.0
                },
                baseline_memory_usage={
                    'O(1)': 10,
                    'O(n)': 50,
                    'O(n^2)': 200,
                    'O(n^3)': 1000
                },
                performance_multipliers={
                    'list_comprehension': 0.8,
                    'generator': 0.6,
                    'numpy': 0.3,
                    'nested_loop': 2.0,
                    'recursion': 1.5
                },
                common_patterns=[
                    'for_loop', 'list_comprehension', 'dictionary_access',
                    'function_call', 'class_instantiation'
                ],
                optimization_rules=[
                    {
                        'pattern': r'for\s+\w+\s+in\s+range\(len\(',
                        'suggestion': 'enumerate() 사용을 고려하세요',
                        'improvement': '10-20% 성능 향상'
                    },
                    {
                        'pattern': r'\+\s*str\(',
                        'suggestion': 'f-string 사용을 권장합니다',
                        'improvement': '20-30% 성능 향상'
                    }
                ]
            ),
            'javascript': LanguageBenchmarkData(
                language='javascript',
                baseline_execution_time={
                    'O(1)': 0.0005,
                    'O(n)': 0.005,
                    'O(n^2)': 0.05,
                    'O(n^3)': 0.5,
                    'O(2^n)': 3.0
                },
                baseline_memory_usage={
                    'O(1)': 5,
                    'O(n)': 30,
                    'O(n^2)': 150,
                    'O(n^3)': 800
                },
                performance_multipliers={
                    'arrow_function': 0.9,
                    'const_let': 0.95,
                    'strict_equality': 0.98,
                    'var_declaration': 1.1
                },
                common_patterns=['function_declaration', 'arrow_function', 'array_methods'],
                optimization_rules=[
                    {
                        'pattern': r'var\s+',
                        'suggestion': 'let 또는 const 사용을 권장합니다',
                        'improvement': '5-10% 성능 향상'
                    },
                    {
                        'pattern': r'==\s',
                        'suggestion': '=== 사용을 권장합니다',
                        'improvement': '타입 안전성 향상'
                    }
                ]
            ),
            'java': LanguageBenchmarkData(
                language='java',
                baseline_execution_time={
                    'O(1)': 0.0002,
                    'O(n)': 0.002,
                    'O(n^2)': 0.02,
                    'O(n^3)': 0.2,
                    'O(2^n)': 2.0
                },
                baseline_memory_usage={
                    'O(1)': 20,
                    'O(n)': 80,
                    'O(n^2)': 300,
                    'O(n^3)': 1500
                },
                performance_multipliers={
                    'stringbuilder': 0.5,
                    'arraylist_presized': 0.8,
                    'primitive_types': 0.7,
                    'boxing_unboxing': 1.3
                },
                common_patterns=['loop', 'string_concatenation', 'collection_usage'],
                optimization_rules=[
                    {
                        'pattern': r'String\s+\w+\s*=\s*.*\+',
                        'suggestion': 'StringBuilder 사용을 고려하세요',
                        'improvement': '50-80% 성능 향상'
                    }
                ]
            ),
            'cpp': LanguageBenchmarkData(
                language='cpp',
                baseline_execution_time={
                    'O(1)': 0.0001,
                    'O(n)': 0.001,
                    'O(n^2)': 0.01,
                    'O(n^3)': 0.1,
                    'O(2^n)': 1.0
                },
                baseline_memory_usage={
                    'O(1)': 8,
                    'O(n)': 40,
                    'O(n^2)': 160,
                    'O(n^3)': 800
                },
                performance_multipliers={
                    'vector_reserve': 0.8,
                    'smart_pointers': 1.05,
                    'raw_pointers': 0.95,
                    'virtual_functions': 1.1
                },
                common_patterns=['memory_management', 'stl_usage', 'template_usage'],
                optimization_rules=[]
            ),
            'go': LanguageBenchmarkData(
                language='go',
                baseline_execution_time={
                    'O(1)': 0.0003,
                    'O(n)': 0.003,
                    'O(n^2)': 0.03,
                    'O(n^3)': 0.3,
                    'O(2^n)': 2.5
                },
                baseline_memory_usage={
                    'O(1)': 12,
                    'O(n)': 60,
                    'O(n^2)': 240,
                    'O(n^3)': 1200
                },
                performance_multipliers={
                    'goroutines': 0.7,
                    'channels': 0.9,
                    'slice_capacity': 0.8
                },
                common_patterns=['goroutine_usage', 'channel_operations', 'slice_operations'],
                optimization_rules=[]
            ),
            'rust': LanguageBenchmarkData(
                language='rust',
                baseline_execution_time={
                    'O(1)': 0.0001,
                    'O(n)': 0.001,
                    'O(n^2)': 0.01,
                    'O(n^3)': 0.1,
                    'O(2^n)': 1.0
                },
                baseline_memory_usage={
                    'O(1)': 6,
                    'O(n)': 30,
                    'O(n^2)': 120,
                    'O(n^3)': 600
                },
                performance_multipliers={
                    'zero_cost_abstractions': 1.0,
                    'ownership_system': 0.95,
                    'iterators': 0.8
                },
                common_patterns=['ownership', 'borrowing', 'iterator_chains'],
                optimization_rules=[]
            ),
            'php': LanguageBenchmarkData(
                language='php',
                baseline_execution_time={
                    'O(1)': 0.002,
                    'O(n)': 0.02,
                    'O(n^2)': 0.2,
                    'O(n^3)': 2.0,
                    'O(2^n)': 10.0
                },
                baseline_memory_usage={
                    'O(1)': 15,
                    'O(n)': 75,
                    'O(n^2)': 300,
                    'O(n^3)': 1500
                },
                performance_multipliers={
                    'array_functions': 0.8,
                    'opcache': 0.6,
                    'string_operations': 1.2
                },
                common_patterns=['array_operations', 'string_manipulation'],
                optimization_rules=[]
            ),
            'ruby': LanguageBenchmarkData(
                language='ruby',
                baseline_execution_time={
                    'O(1)': 0.003,
                    'O(n)': 0.03,
                    'O(n^2)': 0.3,
                    'O(n^3)': 3.0,
                    'O(2^n)': 15.0
                },
                baseline_memory_usage={
                    'O(1)': 20,
                    'O(n)': 100,
                    'O(n^2)': 400,
                    'O(n^3)': 2000
                },
                performance_multipliers={
                    'blocks': 0.9,
                    'symbols': 0.85,
                    'string_interpolation': 1.1
                },
                common_patterns=['block_usage', 'metaprogramming'],
                optimization_rules=[]
            ),
            'typescript': LanguageBenchmarkData(
                language='typescript',
                baseline_execution_time={
                    'O(1)': 0.0006,
                    'O(n)': 0.006,
                    'O(n^2)': 0.06,
                    'O(n^3)': 0.6,
                    'O(2^n)': 3.5
                },
                baseline_memory_usage={
                    'O(1)': 8,
                    'O(n)': 40,
                    'O(n^2)': 160,
                    'O(n^3)': 800
                },
                performance_multipliers={
                    'type_annotations': 1.0,
                    'generics': 1.0,
                    'interfaces': 1.0
                },
                common_patterns=['type_usage', 'interface_implementation'],
                optimization_rules=[]
            ),
            'csharp': LanguageBenchmarkData(
                language='csharp',
                baseline_execution_time={
                    'O(1)': 0.0002,
                    'O(n)': 0.002,
                    'O(n^2)': 0.02,
                    'O(n^3)': 0.2,
                    'O(2^n)': 2.0
                },
                baseline_memory_usage={
                    'O(1)': 16,
                    'O(n)': 64,
                    'O(n^2)': 256,
                    'O(n^3)': 1280
                },
                performance_multipliers={
                    'linq': 1.1,
                    'generics': 0.95,
                    'value_types': 0.9
                },
                common_patterns=['linq_usage', 'generic_collections'],
                optimization_rules=[]
            )
        }
    
    def _initialize_optimization_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """최적화 패턴 초기화"""
        return {
            'algorithm': [
                {
                    'pattern': 'nested_loop',
                    'detection': r'for.*for.*',
                    'suggestion': '중첩 루프를 단일 루프나 다른 알고리즘으로 최적화',
                    'severity': 'major'
                },
                {
                    'pattern': 'inefficient_search',
                    'detection': r'for.*in.*if.*==',
                    'suggestion': '선형 검색 대신 해시 테이블이나 이진 검색 사용',
                    'severity': 'minor'
                }
            ],
            'memory': [
                {
                    'pattern': 'memory_leak',
                    'detection': r'new|malloc.*(?!free|delete)',
                    'suggestion': '메모리 해제를 확인하세요',
                    'severity': 'critical'
                },
                {
                    'pattern': 'large_data_structure',
                    'detection': r'.*\[.*\d{4,}.*\]',
                    'suggestion': '큰 데이터 구조의 필요성을 재검토하세요',
                    'severity': 'minor'
                }
            ],
            'syntax': [
                {
                    'pattern': 'inefficient_string_concat',
                    'detection': r'\+.*str\(',
                    'suggestion': '문자열 포맷팅 최적화',
                    'severity': 'minor'
                }
            ]
        }
    
    def _initialize_complexity_patterns(self) -> Dict[str, str]:
        """알고리즘 복잡도 패턴 초기화"""
        return {
            r'for.*for.*for': 'O(n^3)',
            r'for.*for(?!.*for)': 'O(n^2)',
            r'for(?!.*for)': 'O(n)',
            r'while.*while': 'O(n^2)',
            r'while(?!.*while)': 'O(n)',
            r'\.sort\(|sorted\(': 'O(n log n)',
            r'recursive|recursion': 'O(2^n)',
            r'binary.*search|bisect': 'O(log n)',
            r'^(?!.*for|.*while|.*recursive).*$': 'O(1)'
        }
    
    def analyze_performance(self, code: str, language: str, execution_time: float, 
                          memory_usage: int, cpu_usage: float = 0.0) -> BenchmarkResult:
        """종합 성능 분석"""
        
        # 코드 해시 생성
        code_hash = hashlib.md5(code.encode()).hexdigest()
        
        # 알고리즘 복잡도 분석
        algorithm_complexity = self._analyze_algorithm_complexity(code, language)
        
        # 복잡도 점수 계산
        complexity_score = self._calculate_complexity_score(code, language)
        
        # 성능 점수 계산 (기존 방식 개선)
        performance_score = self._calculate_advanced_performance_score(
            execution_time, memory_usage, complexity_score, language, algorithm_complexity
        )
        
        # 최적화 레벨 결정
        optimization_level = self._determine_optimization_level(performance_score, complexity_score)
        
        # 벤치마크 카테고리 분류
        benchmark_category = self._categorize_benchmark(code, language)
        
        # 언어별 상대 순위 계산
        comparative_ranking = self._calculate_comparative_ranking(
            performance_score, language, algorithm_complexity
        )
        
        # 벤치마크 결과 생성
        result = BenchmarkResult(
            execution_id=f"bench_{int(time.time() * 1000)}",
            language=language,
            code_hash=code_hash,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            performance_score=performance_score,
            complexity_score=complexity_score,
            algorithm_complexity=algorithm_complexity,
            optimization_level=optimization_level,
            benchmark_category=benchmark_category,
            comparative_ranking=comparative_ranking,
            timestamp=datetime.now().isoformat()
        )
        
        # 결과 저장
        self.benchmark_results.append(result)
        self._save_benchmark_data()
        
        return result
    
    def _analyze_algorithm_complexity(self, code: str, language: str) -> str:
        """알고리즘 복잡도 분석"""
        code_lower = code.lower()
        
        # 패턴 매칭으로 복잡도 추정
        for pattern, complexity in self.complexity_patterns.items():
            if re.search(pattern, code_lower, re.MULTILINE):
                return complexity
        
        return 'O(1)'  # 기본값
    
    def _calculate_complexity_score(self, code: str, language: str) -> int:
        """코드 복잡도 점수 계산 (1-100)"""
        score = 0
        
        # 코드 길이 기반 점수
        lines = len([line for line in code.split('\n') if line.strip()])
        score += min(lines * 2, 30)
        
        # 제어 구조 복잡도
        control_structures = len(re.findall(r'\b(if|for|while|switch|case)\b', code.lower()))
        score += control_structures * 5
        
        # 함수/클래스 정의
        functions = len(re.findall(r'\b(def|function|class|struct)\b', code.lower()))
        score += functions * 3
        
        # 중첩 구조
        nested_structures = len(re.findall(r'for.*for|if.*if', code.lower()))
        score += nested_structures * 10
        
        return min(score, 100)
    
    def _calculate_advanced_performance_score(self, execution_time: float, memory_usage: int, 
                                           complexity_score: int, language: str, 
                                           algorithm_complexity: str) -> float:
        """향상된 성능 점수 계산"""
        
        baseline = self.language_baselines.get(language)
        if not baseline:
            return 50.0  # 기본값
        
        # 기준선 대비 성능 계산
        baseline_time = baseline.baseline_execution_time.get(algorithm_complexity, 0.01)
        baseline_memory = baseline.baseline_memory_usage.get(algorithm_complexity, 50)
        
        # 시간 점수 (70% 가중치)
        time_ratio = execution_time / baseline_time
        time_score = max(0, 100 - (time_ratio - 1) * 50)
        
        # 메모리 점수 (20% 가중치)
        memory_ratio = memory_usage / baseline_memory
        memory_score = max(0, 100 - (memory_ratio - 1) * 40)
        
        # 복잡도 보정 (10% 가중치)
        complexity_penalty = min(complexity_score / 100 * 20, 20)
        
        # 가중 평균
        total_score = (
            time_score * 0.7 +
            memory_score * 0.2 +
            (100 - complexity_penalty) * 0.1
        )
        
        return round(max(0, min(100, total_score)), 2)
    
    def _determine_optimization_level(self, performance_score: float, complexity_score: int) -> str:
        """최적화 레벨 결정"""
        if performance_score >= 90 and complexity_score <= 30:
            return 'optimal'
        elif performance_score >= 70 and complexity_score <= 50:
            return 'good'
        elif performance_score >= 50:
            return 'needs_improvement'
        else:
            return 'poor'
    
    def _categorize_benchmark(self, code: str, language: str) -> str:
        """벤치마크 카테고리 분류"""
        code_lower = code.lower()
        
        if any(keyword in code_lower for keyword in ['sort', 'search', 'tree', 'graph']):
            return 'algorithm'
        elif any(keyword in code_lower for keyword in ['list', 'array', 'dict', 'map']):
            return 'data_structure'
        elif any(keyword in code_lower for keyword in ['file', 'read', 'write', 'input', 'output']):
            return 'io_intensive'
        else:
            return 'basic'
    
    def _calculate_comparative_ranking(self, performance_score: float, language: str, 
                                     algorithm_complexity: str) -> float:
        """언어별 상대 순위 계산"""
        # 같은 언어의 비슷한 복잡도 코드들과 비교
        similar_results = [
            r for r in self.benchmark_results 
            if r.language == language and r.algorithm_complexity == algorithm_complexity
        ]
        
        if len(similar_results) < 2:
            return 50.0  # 충분한 데이터가 없으면 중간값
        
        scores = [r.performance_score for r in similar_results]
        percentile = sum(1 for score in scores if score <= performance_score) / len(scores) * 100
        
        return round(percentile, 1)
    
    def generate_optimization_suggestions(self, code: str, language: str, 
                                        benchmark_result: BenchmarkResult) -> List[OptimizationSuggestion]:
        """최적화 제안 생성"""
        suggestions = []
        suggestion_counter = 0
        
        # 1. 성능 기반 제안
        if benchmark_result.performance_score < 70:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"perf_{suggestion_counter}",
                category='performance',
                severity='major' if benchmark_result.performance_score < 50 else 'minor',
                title='성능 최적화 필요',
                description=f'현재 성능 점수 {benchmark_result.performance_score:.1f}점. 알고리즘이나 데이터 구조 개선을 고려하세요.',
                code_example=None,
                estimated_improvement='20-50% 성능 향상 가능',
                difficulty='medium'
            ))
            suggestion_counter += 1
        
        # 2. 알고리즘 복잡도 기반 제안
        if benchmark_result.algorithm_complexity in ['O(n^2)', 'O(n^3)', 'O(2^n)']:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"algo_{suggestion_counter}",
                category='algorithm',
                severity='major',
                title='알고리즘 복잡도 개선',
                description=f'현재 {benchmark_result.algorithm_complexity} 복잡도. 더 효율적인 알고리즘 사용을 고려하세요.',
                code_example=self._get_algorithm_example(benchmark_result.algorithm_complexity, language),
                estimated_improvement='n배 성능 향상 가능',
                difficulty='hard'
            ))
            suggestion_counter += 1
        
        # 3. 언어별 특화 제안
        language_suggestions = self._get_language_specific_suggestions(code, language)
        for lang_sugg in language_suggestions:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"lang_{suggestion_counter}",
                category='syntax',
                severity='minor',
                title=lang_sugg['title'],
                description=lang_sugg['description'],
                code_example=lang_sugg.get('example'),
                estimated_improvement=lang_sugg.get('improvement', '10-20% 성능 향상'),
                difficulty='easy'
            ))
            suggestion_counter += 1
        
        # 4. 메모리 사용량 기반 제안
        if benchmark_result.memory_usage > 500:  # 500MB 이상
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"mem_{suggestion_counter}",
                category='memory',
                severity='major',
                title='메모리 사용량 최적화',
                description=f'현재 {benchmark_result.memory_usage}MB 사용. 메모리 효율적인 데이터 구조나 알고리즘 고려하세요.',
                code_example=None,
                estimated_improvement='50-80% 메모리 절약 가능',
                difficulty='medium'
            ))
            suggestion_counter += 1
        
        # 5. 복잡도 점수 기반 제안
        if benchmark_result.complexity_score > 70:
            suggestions.append(OptimizationSuggestion(
                suggestion_id=f"complex_{suggestion_counter}",
                category='style',
                severity='minor',
                title='코드 복잡도 감소',
                description=f'복잡도 점수 {benchmark_result.complexity_score}점. 코드를 더 간단하고 읽기 쉽게 리팩토링하세요.',
                code_example=None,
                estimated_improvement='가독성 및 유지보수성 향상',
                difficulty='easy'
            ))
        
        return suggestions[:5]  # 최대 5개 제안
    
    def _get_algorithm_example(self, complexity: str, language: str) -> Optional[str]:
        """알고리즘 개선 예제 코드"""
        examples = {
            'python': {
                'O(n^2)': '''# 개선 전: O(n^2)
for i in range(len(arr)):
    for j in range(len(arr)):
        if arr[i] == target:
            return i

# 개선 후: O(n)
try:
    return arr.index(target)
except ValueError:
    return -1''',
                'O(n^3)': '''# 개선 전: O(n^3) 삼중 루프
# 개선 후: 해시맵이나 더 효율적인 알고리즘 사용''',
                'O(2^n)': '''# 개선 전: O(2^n) 재귀
def fibonacci(n):
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)

# 개선 후: O(n) 동적 프로그래밍
def fibonacci(n):
    if n <= 1: return n
    a, b = 0, 1
    for _ in range(2, n+1):
        a, b = b, a + b
    return b'''
            }
        }
        
        return examples.get(language, {}).get(complexity)
    
    def _get_language_specific_suggestions(self, code: str, language: str) -> List[Dict[str, str]]:
        """언어별 특화 제안"""
        suggestions = []
        baseline = self.language_baselines.get(language)
        
        if not baseline:
            return suggestions
        
        # 언어별 최적화 규칙 적용
        for rule in baseline.optimization_rules:
            if re.search(rule['pattern'], code):
                suggestions.append({
                    'title': '언어별 최적화',
                    'description': rule['suggestion'],
                    'improvement': rule['improvement']
                })
        
        # 추가 언어별 제안
        if language == 'python':
            if 'for i in range(len(' in code:
                suggestions.append({
                    'title': 'enumerate 사용 권장',
                    'description': 'range(len()) 대신 enumerate() 사용',
                    'example': 'for i, item in enumerate(items):',
                    'improvement': '10-15% 성능 향상'
                })
            
            if code.count('print(') > 5:
                suggestions.append({
                    'title': 'logging 모듈 사용',
                    'description': '많은 print문 대신 logging 모듈 사용 권장',
                    'improvement': '성능 및 유지보수성 향상'
                })
        
        elif language == 'javascript':
            if 'var ' in code:
                suggestions.append({
                    'title': 'const/let 사용',
                    'description': 'var 대신 const 또는 let 사용 권장',
                    'example': 'const value = 10; // or let value = 10;',
                    'improvement': '스코프 안전성 향상'
                })
        
        return suggestions
    
    def get_benchmark_statistics(self, language: Optional[str] = None, 
                               category: Optional[str] = None) -> Dict[str, Any]:
        """벤치마크 통계 조회"""
        filtered_results = self.benchmark_results
        
        if language:
            filtered_results = [r for r in filtered_results if r.language == language]
        
        if category:
            filtered_results = [r for r in filtered_results if r.benchmark_category == category]
        
        if not filtered_results:
            return {"message": "해당 조건의 벤치마크 결과가 없습니다."}
        
        # 통계 계산
        performance_scores = [r.performance_score for r in filtered_results]
        execution_times = [r.execution_time for r in filtered_results]
        memory_usages = [r.memory_usage for r in filtered_results]
        
        # 언어별 분포
        language_distribution = Counter([r.language for r in filtered_results])
        
        # 카테고리별 분포
        category_distribution = Counter([r.benchmark_category for r in filtered_results])
        
        # 최적화 레벨 분포
        optimization_distribution = Counter([r.optimization_level for r in filtered_results])
        
        return {
            "total_benchmarks": len(filtered_results),
            "performance_statistics": {
                "average": round(statistics.mean(performance_scores), 2),
                "median": round(statistics.median(performance_scores), 2),
                "best": max(performance_scores),
                "worst": min(performance_scores),
                "std_dev": round(statistics.stdev(performance_scores) if len(performance_scores) > 1 else 0, 2)
            },
            "execution_time_statistics": {
                "average": round(statistics.mean(execution_times), 4),
                "median": round(statistics.median(execution_times), 4),
                "fastest": min(execution_times),
                "slowest": max(execution_times)
            },
            "memory_statistics": {
                "average": round(statistics.mean(memory_usages), 1),
                "median": round(statistics.median(memory_usages), 1),
                "least": min(memory_usages),
                "most": max(memory_usages)
            },
            "distributions": {
                "by_language": dict(language_distribution),
                "by_category": dict(category_distribution),
                "by_optimization_level": dict(optimization_distribution)
            },
            "insights": self._generate_statistical_insights(filtered_results)
        }
    
    def _generate_statistical_insights(self, results: List[BenchmarkResult]) -> List[str]:
        """통계적 인사이트 생성"""
        insights = []
        
        if not results:
            return insights
        
        # 언어별 성능 비교
        language_performance = defaultdict(list)
        for result in results:
            language_performance[result.language].append(result.performance_score)
        
        if len(language_performance) > 1:
            avg_scores = {lang: statistics.mean(scores) for lang, scores in language_performance.items()}
            best_lang = max(avg_scores, key=avg_scores.get)
            worst_lang = min(avg_scores, key=avg_scores.get)
            
            insights.append(f"🏆 {best_lang}이 평균 {avg_scores[best_lang]:.1f}점으로 최고 성능을 보입니다.")
            insights.append(f"📈 {worst_lang}은 평균 {avg_scores[worst_lang]:.1f}점으로 개선이 필요합니다.")
        
        # 최적화 레벨 분포
        optimization_counts = Counter([r.optimization_level for r in results])
        total = len(results)
        
        optimal_ratio = optimization_counts.get('optimal', 0) / total * 100
        if optimal_ratio > 50:
            insights.append(f"✨ {optimal_ratio:.1f}%의 코드가 최적화된 상태입니다.")
        elif optimal_ratio < 20:
            insights.append(f"⚠️ 최적화된 코드가 {optimal_ratio:.1f}%에 불과합니다. 성능 개선이 필요합니다.")
        
        # 복잡도 분석
        complexity_counts = Counter([r.algorithm_complexity for r in results])
        if complexity_counts.get('O(n^2)', 0) + complexity_counts.get('O(n^3)', 0) > total * 0.3:
            insights.append("🔄 높은 복잡도 알고리즘이 많습니다. 효율적인 알고리즘 사용을 고려하세요.")
        
        return insights
    
    def compare_with_baseline(self, benchmark_result: BenchmarkResult) -> Dict[str, Any]:
        """기준선과 비교 분석"""
        baseline = self.language_baselines.get(benchmark_result.language)
        if not baseline:
            return {"error": "해당 언어의 기준선 데이터가 없습니다."}
        
        baseline_time = baseline.baseline_execution_time.get(
            benchmark_result.algorithm_complexity, 0.01
        )
        baseline_memory = baseline.baseline_memory_usage.get(
            benchmark_result.algorithm_complexity, 50
        )
        
        time_ratio = benchmark_result.execution_time / baseline_time
        memory_ratio = benchmark_result.memory_usage / baseline_memory
        
        return {
            "execution_time_comparison": {
                "result": benchmark_result.execution_time,
                "baseline": baseline_time,
                "ratio": round(time_ratio, 2),
                "status": "faster" if time_ratio < 1 else "slower" if time_ratio > 1.5 else "normal"
            },
            "memory_usage_comparison": {
                "result": benchmark_result.memory_usage,
                "baseline": baseline_memory,
                "ratio": round(memory_ratio, 2),
                "status": "efficient" if memory_ratio < 1 else "heavy" if memory_ratio > 2 else "normal"
            },
            "overall_assessment": self._assess_overall_performance(time_ratio, memory_ratio),
            "ranking_percentile": benchmark_result.comparative_ranking
        }
    
    def _assess_overall_performance(self, time_ratio: float, memory_ratio: float) -> str:
        """전체 성능 평가"""
        if time_ratio < 0.8 and memory_ratio < 0.8:
            return "excellent"
        elif time_ratio < 1.2 and memory_ratio < 1.5:
            return "good"
        elif time_ratio < 2.0 and memory_ratio < 3.0:
            return "acceptable"
        else:
            return "needs_improvement"
    
    def _load_benchmark_data(self):
        """벤치마크 데이터 로딩"""
        try:
            file_path = os.path.join(self.data_dir, 'benchmark_results.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.benchmark_results = [
                        BenchmarkResult(**item) for item in data
                    ]
        except Exception as e:
            print(f"벤치마크 데이터 로딩 실패: {e}")
            self.benchmark_results = []
    
    def _save_benchmark_data(self):
        """벤치마크 데이터 저장"""
        try:
            file_path = os.path.join(self.data_dir, 'benchmark_results.json')
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(result) for result in self.benchmark_results], f, 
                         ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"벤치마크 데이터 저장 실패: {e}")

# 전역 인스턴스 (필요시 사용)
performance_benchmark = None

def get_performance_benchmark(data_dir: str = "data/benchmark"):
    """필요시 PerformanceBenchmark 인스턴스를 생성하여 반환"""
    global performance_benchmark
    if performance_benchmark is None:
        try:
            performance_benchmark = PerformanceBenchmark(data_dir)
        except Exception as e:
            print(f"⚠️ PerformanceBenchmark 인스턴스 생성 실패: {e}")
    return performance_benchmark 