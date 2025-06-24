#!/usr/bin/env python3
"""
팜솔라 교육용 언어별 학습 가이드 시스템
10개 언어별 초급-중급-고급 단계별 학습 경로 제공
예제 코드와 실습 과제 자동 생성
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class LearningLevel(Enum):
    """학습 레벨 정의"""
    BEGINNER = "초급"
    INTERMEDIATE = "중급"
    ADVANCED = "고급"

@dataclass
class LearningPath:
    """학습 경로 데이터 클래스"""
    level: LearningLevel
    language: str
    concepts: List[str]
    examples: List[Dict]
    exercises: List[Dict]
    prerequisites: List[str]
    estimated_hours: int
    learning_objectives: List[str]

@dataclass
class CodeExample:
    """코드 예제 데이터 클래스"""
    title: str
    description: str
    code: str
    explanation: str
    difficulty: LearningLevel
    concepts_covered: List[str]
    output_example: str

class EducationalCodeGuide:
    """교육용 코드 가이드 시스템"""
    
    def __init__(self):
        self.supported_languages = [
            'python', 'javascript', 'typescript', 'java', 'cpp',
            'go', 'rust', 'php', 'ruby', 'csharp'
        ]
        self.learning_paths = self._initialize_learning_paths()
        self.code_examples = self._initialize_code_examples()
        self.user_progress = {}
        
    def _initialize_learning_paths(self) -> Dict[str, Dict[str, LearningPath]]:
        """언어별 학습 경로 초기화"""
        paths = {}
        for language in self.supported_languages:
            paths[language] = {
                level.value: self._create_learning_path(language, level)
                for level in LearningLevel
            }
        return paths
    
    def _create_learning_path(self, language: str, level: LearningLevel) -> LearningPath:
        """언어별 레벨별 학습 경로 생성"""
        if language == 'python':
            return self._create_python_learning_path(level)
        elif language == 'javascript':
            return self._create_javascript_learning_path(level)
        elif language == 'java':
            return self._create_java_learning_path(level)
        elif language == 'cpp':
            return self._create_cpp_learning_path(level)
        elif language == 'typescript':
            return self._create_typescript_learning_path(level)
        else:
            return self._create_default_learning_path(language, level)
    
    def _create_python_learning_path(self, level: LearningLevel) -> LearningPath:
        """Python 학습 경로 생성"""
        if level == LearningLevel.BEGINNER:
            return LearningPath(
                level=level,
                language='python',
                concepts=[
                    "변수와 데이터 타입", "기본 연산자", "조건문 (if, elif, else)",
                    "반복문 (for, while)", "리스트와 튜플", "딕셔너리와 집합",
                    "함수 정의와 호출", "문자열 처리", "파일 입출력", "예외 처리 기초"
                ],
                examples=[
                    {
                        "title": "Hello World와 변수",
                        "code": """# 기본 출력과 변수 사용
print("Hello, 팜솔라!")
name = "학습자"
age = 25
print(f"안녕하세요, {name}님! 나이는 {age}세입니다.")""",
                        "explanation": "Python의 기본 출력과 변수 할당, f-string 사용법을 배웁니다."
                    },
                    {
                        "title": "조건문 활용",
                        "code": """# 점수에 따른 등급 판정
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

print(f"점수: {score}, 등급: {grade}")""",
                        "explanation": "if-elif-else 구문을 사용한 조건부 실행을 학습합니다."
                    }
                ],
                exercises=[
                    {
                        "title": "계산기 만들기",
                        "description": "두 숫자를 입력받아 사칙연산을 수행하는 간단한 계산기를 만드세요.",
                        "starter_code": """# 계산기 프로그램
def calculator(a, b, operation):
    # 여기에 코드를 작성하세요
    pass

# 테스트
print(calculator(10, 5, '+'))  # 15
print(calculator(10, 5, '-'))  # 5""",
                        "difficulty": "초급"
                    }
                ],
                prerequisites=[],
                estimated_hours=20,
                learning_objectives=[
                    "Python 기본 문법 이해",
                    "간단한 프로그램 작성 능력",
                    "조건문과 반복문 활용",
                    "기본 데이터 구조 사용"
                ]
            )
        elif level == LearningLevel.INTERMEDIATE:
            return LearningPath(
                level=level,
                language='python',
                concepts=[
                    "클래스와 객체", "상속과 다형성", "모듈과 패키지",
                    "리스트 컴프리헨션", "제네레이터와 이터레이터",
                    "데코레이터", "컨텍스트 매니저", "정규표현식",
                    "외부 라이브러리 사용", "API 호출과 JSON 처리"
                ],
                examples=[
                    {
                        "title": "클래스 정의와 사용",
                        "code": """class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.grades = []
    
    def add_grade(self, grade):
        self.grades.append(grade)
    
    def get_average(self):
        if self.grades:
            return sum(self.grades) / len(self.grades)
        return 0

# 사용 예시
student = Student("김철수", 20)
student.add_grade(85)
student.add_grade(92)
print(f"{student.name}의 평균: {student.get_average():.1f}")""",
                        "explanation": "클래스 정의, 생성자, 메서드 구현을 학습합니다."
                    }
                ],
                exercises=[
                    {
                        "title": "도서관 관리 시스템",
                        "description": "Book 클래스와 Library 클래스를 만들어 도서 대출/반납 시스템을 구현하세요.",
                        "starter_code": """class Book:
    def __init__(self, title, author):
        # 여기에 코드를 작성하세요
        pass

class Library:
    def __init__(self):
        # 여기에 코드를 작성하세요
        pass""",
                        "difficulty": "중급"
                    }
                ],
                prerequisites=["Python 초급 과정 완료"],
                estimated_hours=30,
                learning_objectives=[
                    "객체지향 프로그래밍 이해",
                    "모듈화된 코드 작성",
                    "외부 라이브러리 활용",
                    "중급 수준의 프로젝트 구현"
                ]
            )
        else:  # ADVANCED
            return LearningPath(
                level=level,
                language='python',
                concepts=[
                    "메타클래스", "비동기 프로그래밍 (async/await)",
                    "멀티스레딩과 멀티프로세싱", "타입 힌트",
                    "성능 최적화", "메모리 관리", "디자인 패턴",
                    "테스트 주도 개발", "패키지 배포", "웹 프레임워크"
                ],
                examples=[
                    {
                        "title": "비동기 웹 스크래핑",
                        "code": """import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_multiple_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# 사용 예시
urls = ["http://example.com", "http://google.com"]
# results = asyncio.run(fetch_multiple_urls(urls))""",
                        "explanation": "비동기 프로그래밍과 동시성 처리를 학습합니다."
                    }
                ],
                exercises=[
                    {
                        "title": "웹 API 서버 구축",
                        "description": "FastAPI를 사용하여 RESTful API 서버를 구축하고 데이터베이스와 연동하세요.",
                        "starter_code": """from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    # 여기에 코드를 작성하세요
    pass""",
                        "difficulty": "고급"
                    }
                ],
                prerequisites=["Python 중급 과정 완료", "웹 개발 기초 지식"],
                estimated_hours=40,
                learning_objectives=[
                    "고급 Python 기법 활용",
                    "비동기 프로그래밍 구현",
                    "실무급 프로젝트 개발",
                    "성능 최적화 기법 적용"
                ]
            )
    
    def _create_javascript_learning_path(self, level: LearningLevel) -> LearningPath:
        """JavaScript 학습 경로 생성"""
        if level == LearningLevel.BEGINNER:
            return LearningPath(
                level=level,
                language='javascript',
                concepts=[
                    "변수 선언 (var, let, const)", "데이터 타입", "연산자",
                    "조건문과 반복문", "함수 선언과 표현식", "배열과 객체",
                    "DOM 조작", "이벤트 처리", "기본 에러 핸들링"
                ],
                examples=[
                    {
                        "title": "기본 함수와 DOM 조작",
                        "code": """// 기본 함수 정의
function greetUser(name) {
    return `안녕하세요, ${name}님!`;
}

// DOM 요소 조작
document.addEventListener('DOMContentLoaded', function() {
    const button = document.getElementById('myButton');
    button.addEventListener('click', function() {
        alert(greetUser('팜솔라 학습자'));
    });
});

console.log(greetUser('JavaScript'));""",
                        "explanation": "JavaScript 함수 정의와 DOM 이벤트 처리를 학습합니다."
                    }
                ],
                exercises=[
                    {
                        "title": "할 일 목록 만들기",
                        "description": "HTML과 JavaScript를 사용하여 할 일을 추가/삭제할 수 있는 간단한 앱을 만드세요.",
                        "starter_code": """// 할 일 목록 관리
const todos = [];

function addTodo(text) {
    // 여기에 코드를 작성하세요
}

function removeTodo(index) {
    // 여기에 코드를 작성하세요
}""",
                        "difficulty": "초급"
                    }
                ],
                prerequisites=[],
                estimated_hours=25,
                learning_objectives=[
                    "JavaScript 기본 문법 이해",
                    "웹 페이지 상호작용 구현",
                    "DOM 조작 능력",
                    "이벤트 기반 프로그래밍"
                ]
            )
        # 중급, 고급도 유사하게 구현...
        return self._create_default_learning_path('javascript', level)
    
    def _create_java_learning_path(self, level: LearningLevel) -> LearningPath:
        """Java 학습 경로 생성 - 기본 구조"""
        return LearningPath(
            level=level,
            language='java',
            concepts=["클래스와 객체", "상속", "인터페이스", "컬렉션"],
            examples=[],
            exercises=[],
            prerequisites=[],
            estimated_hours=30,
            learning_objectives=["Java 객체지향 프로그래밍 이해"]
        )
    
    def _create_cpp_learning_path(self, level: LearningLevel) -> LearningPath:
        """C++ 학습 경로 생성 - 기본 구조"""
        return LearningPath(
            level=level,
            language='cpp',
            concepts=["포인터", "메모리 관리", "STL", "템플릿"],
            examples=[],
            exercises=[],
            prerequisites=[],
            estimated_hours=35,
            learning_objectives=["C++ 시스템 프로그래밍 이해"]
        )
    
    def _create_typescript_learning_path(self, level: LearningLevel) -> LearningPath:
        """TypeScript 학습 경로 생성 - 기본 구조"""
        return LearningPath(
            level=level,
            language='typescript',
            concepts=["타입 시스템", "인터페이스", "제네릭", "모듈"],
            examples=[],
            exercises=[],
            prerequisites=["JavaScript 기초"],
            estimated_hours=25,
            learning_objectives=["타입 안전한 JavaScript 개발"]
        )
    
    def _create_default_learning_path(self, language: str, level: LearningLevel) -> LearningPath:
        """기본 학습 경로 생성"""
        return LearningPath(
            level=level,
            language=language,
            concepts=[f"{language} 기본 문법", f"{language} 고급 기능"],
            examples=[],
            exercises=[],
            prerequisites=[],
            estimated_hours=20,
            learning_objectives=[f"{language} 프로그래밍 기초 이해"]
        )
    
    def _initialize_code_examples(self) -> Dict[str, List[CodeExample]]:
        """언어별 코드 예제 초기화"""
        examples = {}
        for language in self.supported_languages:
            examples[language] = []
        return examples
    
    def get_learning_path(self, language: str, level: str) -> Optional[LearningPath]:
        """특정 언어와 레벨의 학습 경로 반환"""
        if language in self.learning_paths and level in self.learning_paths[language]:
            return self.learning_paths[language][level]
        return None
    
    def assess_user_level(self, language: str, user_code: str) -> LearningLevel:
        """사용자 실력 레벨 자동 판정"""
        complexity_score = self._calculate_code_complexity(user_code, language)
        
        if complexity_score >= 80:
            return LearningLevel.ADVANCED
        elif complexity_score >= 50:
            return LearningLevel.INTERMEDIATE
        else:
            return LearningLevel.BEGINNER
    
    def _calculate_code_complexity(self, code: str, language: str) -> int:
        """코드 복잡도 계산"""
        score = 0
        
        # 기본 복잡도 지표들
        advanced_patterns = {
            'python': ['class ', 'def ', 'import ', 'async ', 'with ', 'try:', 'except:', 'lambda'],
            'javascript': ['class ', 'function', 'async ', 'await', 'Promise', '=> ', 'const', 'let']
        }
        
        if language in advanced_patterns:
            for pattern in advanced_patterns[language]:
                score += code.count(pattern) * 10
        
        # 코드 길이 보정
        score += min(len(code.split('\n')), 50)
        
        return min(score, 100)
    
    def generate_personalized_content(self, language: str, level: str, user_id: str) -> Dict[str, Any]:
        """개인화된 학습 콘텐츠 생성"""
        learning_path = self.get_learning_path(language, level)
        if not learning_path:
            return {"error": "지원하지 않는 언어 또는 레벨입니다."}
        
        # 사용자 진도 확인
        user_progress = self._get_user_progress(user_id, language)
        
        # 추천 예제와 연습문제 선택
        recommended_examples = self._select_recommended_examples(learning_path, user_progress)
        recommended_exercises = self._select_recommended_exercises(learning_path, user_progress)
        
        return {
            "language": language,
            "level": level,
            "user_id": user_id,
            "learning_path": asdict(learning_path),
            "user_progress": user_progress,
            "recommended_examples": recommended_examples,
            "recommended_exercises": recommended_exercises,
            "next_concepts": self._get_next_concepts(learning_path, user_progress),
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_practice_exercise(self, language: str, level: str, concept: str) -> Dict[str, Any]:
        """특정 개념에 대한 실습 문제 자동 생성"""
        exercise_templates = {
            'python': {
                '변수와 데이터 타입': {
                    'title': '변수 활용 연습',
                    'description': '다양한 데이터 타입을 사용하여 개인 정보를 저장하고 출력하는 프로그램을 작성하세요.',
                    'starter_code': '''# 개인 정보 관리 프로그램
name = ""  # 문자열
age = 0    # 정수
height = 0.0  # 실수
is_student = False  # 불린

# 여기에 코드를 작성하세요
def display_info():
    pass''',
                    'expected_output': '이름: 홍길동, 나이: 25세, 키: 175.5cm, 학생여부: True'
                },
                '조건문': {
                    'title': '등급 판별 시스템',
                    'description': '점수를 입력받아 A, B, C, D, F 등급을 판별하는 프로그램을 작성하세요.',
                    'starter_code': '''def grade_calculator(score):
    # 여기에 조건문을 작성하세요
    pass

# 테스트 케이스
print(grade_calculator(95))  # A
print(grade_calculator(82))  # B
print(grade_calculator(65))  # D''',
                    'expected_output': 'A\\nB\\nD'
                }
            },
            'javascript': {
                '함수': {
                    'title': 'JavaScript 함수 연습',
                    'description': '배열의 합계를 계산하는 함수를 작성하세요.',
                    'starter_code': '''function calculateSum(numbers) {
    // 여기에 코드를 작성하세요
}

// 테스트
console.log(calculateSum([1, 2, 3, 4, 5])); // 15''',
                    'expected_output': '15'
                }
            }
        }
        
        if language in exercise_templates and concept in exercise_templates[language]:
            exercise = exercise_templates[language][concept].copy()
            exercise['language'] = language
            exercise['level'] = level
            exercise['concept'] = concept
            exercise['generated_at'] = datetime.now().isoformat()
            return exercise
        
        # 기본 연습문제 생성
        return {
            'title': f'{concept} 연습',
            'description': f'{concept}에 대한 기본 연습 문제입니다.',
            'starter_code': f'// {concept} 연습 코드를 작성하세요',
            'language': language,
            'level': level,
            'concept': concept,
            'generated_at': datetime.now().isoformat()
        }
    
    def track_user_progress(self, user_id: str, language: str, concept: str, completed: bool = True) -> Dict[str, Any]:
        """사용자 학습 진도 추적"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        
        if language not in self.user_progress[user_id]:
            self.user_progress[user_id][language] = {
                'completed_concepts': [],
                'current_level': LearningLevel.BEGINNER.value,
                'last_activity': None,
                'total_study_time': 0
            }
        
        user_lang_progress = self.user_progress[user_id][language]
        
        if completed and concept not in user_lang_progress['completed_concepts']:
            user_lang_progress['completed_concepts'].append(concept)
            user_lang_progress['last_activity'] = datetime.now().isoformat()
            
            # 레벨 자동 승급 확인
            new_level = self._check_level_promotion(user_id, language)
            if new_level:
                user_lang_progress['current_level'] = new_level.value
        
        return {
            'user_id': user_id,
            'language': language,
            'progress': user_lang_progress,
            'updated_at': datetime.now().isoformat()
        }
    
    def get_learning_recommendations(self, user_id: str, language: str) -> Dict[str, Any]:
        """사용자별 학습 추천"""
        user_progress = self._get_user_progress(user_id, language)
        current_level = user_progress.get('current_level', LearningLevel.BEGINNER.value)
        completed_concepts = user_progress.get('completed_concepts', [])
        
        learning_path = self.get_learning_path(language, current_level)
        if not learning_path:
            return {"error": "학습 경로를 찾을 수 없습니다."}
        
        # 다음 학습할 개념 찾기
        remaining_concepts = [
            concept for concept in learning_path.concepts
            if concept not in completed_concepts
        ]
        
        # 추천 생성
        recommendations = {
            'next_concept': remaining_concepts[0] if remaining_concepts else None,
            'progress_percentage': (len(completed_concepts) / len(learning_path.concepts)) * 100 if learning_path.concepts else 0,
            'remaining_concepts': remaining_concepts[:3],  # 다음 3개 개념
            'estimated_remaining_hours': len(remaining_concepts) * 2,  # 개념당 2시간 추정
            'suggested_exercise': None
        }
        
        # 다음 개념에 대한 연습문제 추천
        if recommendations['next_concept']:
            recommendations['suggested_exercise'] = self.generate_practice_exercise(
                language, current_level, recommendations['next_concept']
            )
        
        return recommendations
    
    def _get_user_progress(self, user_id: str, language: str) -> Dict[str, Any]:
        """사용자 진도 정보 반환"""
        if user_id in self.user_progress and language in self.user_progress[user_id]:
            return self.user_progress[user_id][language]
        
        return {
            'completed_concepts': [],
            'current_level': LearningLevel.BEGINNER.value,
            'last_activity': None,
            'total_study_time': 0
        }
    
    def _select_recommended_examples(self, learning_path: LearningPath, user_progress: Dict) -> List[Dict]:
        """추천 예제 선택"""
        completed_concepts = user_progress.get('completed_concepts', [])
        
        # 아직 완료하지 않은 개념의 예제들을 추천
        recommended = []
        for example in learning_path.examples[:3]:  # 최대 3개
            if any(concept not in completed_concepts for concept in learning_path.concepts):
                recommended.append(example)
        
        return recommended
    
    def _select_recommended_exercises(self, learning_path: LearningPath, user_progress: Dict) -> List[Dict]:
        """추천 연습문제 선택"""
        completed_concepts = user_progress.get('completed_concepts', [])
        
        # 아직 완료하지 않은 개념의 연습문제들을 추천
        recommended = []
        for exercise in learning_path.exercises[:2]:  # 최대 2개
            if any(concept not in completed_concepts for concept in learning_path.concepts):
                recommended.append(exercise)
        
        return recommended
    
    def _get_next_concepts(self, learning_path: LearningPath, user_progress: Dict) -> List[str]:
        """다음 학습할 개념들 반환"""
        completed_concepts = user_progress.get('completed_concepts', [])
        
        remaining = [
            concept for concept in learning_path.concepts
            if concept not in completed_concepts
        ]
        
        return remaining[:3]  # 다음 3개 개념
    
    def _check_level_promotion(self, user_id: str, language: str) -> Optional[LearningLevel]:
        """레벨 승급 확인"""
        user_progress = self._get_user_progress(user_id, language)
        current_level = user_progress.get('current_level', LearningLevel.BEGINNER.value)
        completed_concepts = user_progress.get('completed_concepts', [])
        
        current_learning_path = self.get_learning_path(language, current_level)
        if not current_learning_path:
            return None
        
        # 현재 레벨의 80% 이상 완료시 승급
        completion_rate = len(completed_concepts) / len(current_learning_path.concepts)
        
        if completion_rate >= 0.8:
            if current_level == LearningLevel.BEGINNER.value:
                return LearningLevel.INTERMEDIATE
            elif current_level == LearningLevel.INTERMEDIATE.value:
                return LearningLevel.ADVANCED
        
        return None
    
    def get_learning_statistics(self, user_id: str = None) -> Dict[str, Any]:
        """학습 통계 반환"""
        if user_id:
            # 특정 사용자 통계
            if user_id not in self.user_progress:
                return {"error": "사용자 진도 정보가 없습니다."}
            
            user_data = self.user_progress[user_id]
            stats = {
                'user_id': user_id,
                'languages_studied': list(user_data.keys()),
                'total_concepts_completed': sum(
                    len(lang_data.get('completed_concepts', []))
                    for lang_data in user_data.values()
                ),
                'language_details': {}
            }
            
            for language, lang_data in user_data.items():
                learning_path = self.get_learning_path(language, lang_data.get('current_level', '초급'))
                total_concepts = len(learning_path.concepts) if learning_path else 0
                completed = len(lang_data.get('completed_concepts', []))
                
                stats['language_details'][language] = {
                    'level': lang_data.get('current_level', '초급'),
                    'completed_concepts': completed,
                    'total_concepts': total_concepts,
                    'progress_percentage': (completed / total_concepts * 100) if total_concepts > 0 else 0,
                    'last_activity': lang_data.get('last_activity')
                }
            
            return stats
        else:
            # 전체 시스템 통계
            total_users = len(self.user_progress)
            total_languages = len(self.supported_languages)
            
            return {
                'total_users': total_users,
                'supported_languages': total_languages,
                'languages': self.supported_languages,
                'total_learning_paths': sum(len(lang_paths) for lang_paths in self.learning_paths.values()),
                'system_statistics': {
                    'most_popular_language': self._get_most_popular_language(),
                    'average_progress': self._calculate_average_progress()
                }
            }
    
    def _get_most_popular_language(self) -> str:
        """가장 인기 있는 언어 반환"""
        language_counts = {}
        for user_data in self.user_progress.values():
            for language in user_data.keys():
                language_counts[language] = language_counts.get(language, 0) + 1
        
        if language_counts:
            return max(language_counts, key=language_counts.get)
        return 'python'  # 기본값
    
    def _calculate_average_progress(self) -> float:
        """평균 진도율 계산"""
        if not self.user_progress:
            return 0.0
        
        total_progress = 0
        total_paths = 0
        
        for user_data in self.user_progress.values():
            for language, lang_data in user_data.items():
                learning_path = self.get_learning_path(language, lang_data.get('current_level', '초급'))
                if learning_path and learning_path.concepts:
                    completed = len(lang_data.get('completed_concepts', []))
                    total = len(learning_path.concepts)
                    total_progress += (completed / total) * 100
                    total_paths += 1
        
        return total_progress / total_paths if total_paths > 0 else 0.0
    
    def integrate_with_workspace_template(self, user_id: str, language: str, level: str) -> Dict[str, Any]:
        """WorkspaceTemplate 시스템과 통합하여 개인화된 학습 자료 생성"""
        try:
            learning_path = self.get_learning_path(language, level)
            
            if not learning_path:
                return {"error": "학습 경로를 찾을 수 없습니다."}
            
            # 언어별 학습 폴더 구조 생성
            learning_structure = {
                f"{language.upper()}_학습과정": {
                    "description": f"{language} 프로그래밍 {level} 과정",
                    "subfolders": {
                        "📚_개념학습": {
                            "description": "핵심 개념별 학습 자료",
                            "template_files": [
                                f"{concept.replace(' ', '_')}_학습노트.md" 
                                for concept in learning_path.concepts[:5]  # 처음 5개 개념
                            ]
                        },
                        "💻_코드예제": {
                            "description": "실행 가능한 예제 코드",
                            "template_files": [
                                f"예제_{i+1}_{example.get('title', 'example').replace(' ', '_')}.{self._get_file_extension(language)}"
                                for i, example in enumerate(learning_path.examples[:3])
                            ]
                        },
                        "🎯_실습과제": {
                            "description": "단계별 실습 과제",
                            "template_files": [
                                f"과제_{i+1}_{exercise.get('title', 'exercise').replace(' ', '_')}.md"
                                for i, exercise in enumerate(learning_path.exercises[:3])
                            ]
                        },
                        "📈_진도관리": {
                            "description": "학습 진도 및 성과 관리",
                            "template_files": [
                                "학습일지.md",
                                "진도현황.md", 
                                "성취목록.md",
                                "질문모음.md"
                            ]
                        },
                        "🔄_코드리뷰": {
                            "description": "AI 코드 리뷰 결과 저장",
                            "template_files": [
                                "리뷰_기록.md",
                                "개선사항.md",
                                "모범답안.md"
                            ]
                        }
                    }
                }
            }
            
            return {
                "success": True,
                "user_id": user_id,
                "language": language,
                "level": level,
                "workspace_structure": learning_structure,
                "integration_info": {
                    "total_concepts": len(learning_path.concepts),
                    "examples_included": len(learning_path.examples),
                    "exercises_included": len(learning_path.exercises)
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"워크스페이스 통합 오류: {str(e)}"}
    
    def _get_file_extension(self, language: str) -> str:
        """언어별 파일 확장자 반환"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'go': 'go',
            'rust': 'rs',
            'php': 'php',
            'ruby': 'rb',
            'csharp': 'cs'
        }
        return extensions.get(language, 'txt')

    def get_personalized_recommendation(self, user_id: str, language: str) -> Dict[str, Any]:
        """개인화된 추천 (누락된 메서드 추가)"""
        user_progress = self._get_user_progress(user_id, language)
        current_level = user_progress.get('current_level', LearningLevel.BEGINNER.value)
        
        return {
            "user_id": user_id,
            "language": language,
            "current_level": current_level,
            "recommendations": self.get_learning_recommendations(user_id, language),
            "personalized_content": self.generate_personalized_content(language, current_level, user_id)
        }

# 글로벌 인스턴스 생성
_educational_guide_instance = None

def get_educational_guide():
    """교육 가이드 싱글톤 인스턴스 반환"""
    global _educational_guide_instance
    if _educational_guide_instance is None:
        _educational_guide_instance = EducationalCodeGuide()
    return _educational_guide_instance 