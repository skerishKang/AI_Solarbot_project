"""
팜솔라 교육용 코드 가이드 시스템 테스트
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from educational_code_guide import EducationalCodeGuide, LearningLevel
import json

def test_educational_guide():
    """교육용 가이드 시스템 테스트"""
    print("=" * 60)
    print("🎓 팜솔라 교육용 코드 가이드 시스템 테스트")
    print("=" * 60)
    
    # 시스템 초기화
    guide = EducationalCodeGuide()
    print(f"✅ 시스템 초기화 완료")
    print(f"📚 지원 언어: {', '.join(guide.supported_languages)}")
    print()
    
    # 1. Python 초급 학습 경로 테스트
    print("1️⃣ Python 초급 학습 경로 테스트")
    print("-" * 40)
    
    python_beginner = guide.get_learning_path('python', '초급')
    if python_beginner:
        print(f"✅ 학습 경로 조회 성공")
        print(f"📖 개념 수: {len(python_beginner.concepts)}")
        print(f"💻 예제 수: {len(python_beginner.examples)}")
        print(f"🎯 실습 과제 수: {len(python_beginner.exercises)}")
        print(f"⏰ 예상 시간: {python_beginner.estimated_hours}시간")
        print(f"🎯 첫 번째 개념: {python_beginner.concepts[0] if python_beginner.concepts else 'None'}")
    else:
        print("❌ 학습 경로 조회 실패")
    print()
    
    # 2. 개인화된 콘텐츠 생성 테스트
    print("2️⃣ 개인화된 콘텐츠 생성 테스트")
    print("-" * 40)
    
    user_id = "test_user_001"
    personalized_content = guide.generate_personalized_content('python', '초급', user_id)
    
    if 'error' not in personalized_content:
        print(f"✅ 개인화 콘텐츠 생성 성공")
        print(f"👤 사용자: {personalized_content['user_id']}")
        print(f"🐍 언어: {personalized_content['language']}")
        print(f"📊 레벨: {personalized_content['level']}")
        print(f"📈 다음 개념 수: {len(personalized_content.get('next_concepts', []))}")
    else:
        print(f"❌ 개인화 콘텐츠 생성 실패: {personalized_content['error']}")
    print()
    
    # 3. 코드 복잡도 평가 테스트
    print("3️⃣ 코드 복잡도 평가 테스트")
    print("-" * 40)
    
    test_codes = [
        ("초급 코드", "print('Hello World')"),
        ("중급 코드", """
class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
"""),
        ("고급 코드", """
import asyncio
import aiohttp
from typing import List, Dict

class AsyncWebScraper:
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def fetch_url(self, session: aiohttp.ClientSession, url: str) -> Dict:
        async with self.semaphore:
            try:
                async with session.get(url) as response:
                    return {
                        'url': url,
                        'status': response.status,
                        'content': await response.text()
                    }
            except Exception as e:
                return {'url': url, 'error': str(e)}
""")
    ]
    
    for code_type, code in test_codes:
        level = guide.assess_user_level('python', code)
        print(f"📝 {code_type}: {level.value}")
    print()
    
    # 4. 실습 문제 생성 테스트
    print("4️⃣ 실습 문제 생성 테스트")
    print("-" * 40)
    
    exercise = guide.generate_practice_exercise('python', '초급', '변수와 데이터 타입')
    if exercise:
        print(f"✅ 실습 문제 생성 성공")
        print(f"🎯 제목: {exercise['title']}")
        print(f"📝 설명: {exercise['description'][:50]}...")
        print(f"💻 시작 코드 길이: {len(exercise['starter_code'])} 문자")
    else:
        print("❌ 실습 문제 생성 실패")
    print()
    
    # 5. 학습 진도 추적 테스트
    print("5️⃣ 학습 진도 추적 테스트")
    print("-" * 40)
    
    # 사용자 진도 기록
    progress_result = guide.track_user_progress(user_id, 'python', '변수와 데이터 타입', True)
    print(f"✅ 진도 기록 완료: {progress_result['language']} - {len(progress_result['progress']['completed_concepts'])}개 개념 완료")
    
    # 추가 진도 기록
    guide.track_user_progress(user_id, 'python', '기본 연산자', True)
    guide.track_user_progress(user_id, 'python', '조건문 (if, elif, else)', True)
    
    # 학습 추천 생성
    recommendations = guide.get_learning_recommendations(user_id, 'python')
    if 'error' not in recommendations:
        print(f"📊 진행률: {recommendations['progress_percentage']:.1f}%")
        print(f"📖 다음 개념: {recommendations['next_concept']}")
        print(f"⏰ 남은 예상 시간: {recommendations['estimated_remaining_hours']}시간")
    print()
    
    # 6. WorkspaceTemplate 통합 테스트
    print("6️⃣ WorkspaceTemplate 통합 테스트")
    print("-" * 40)
    
    workspace_integration = guide.integrate_with_workspace_template(user_id, 'python', '초급')
    if workspace_integration.get('success'):
        print(f"✅ 워크스페이스 통합 성공")
        structure = workspace_integration['workspace_structure']
        print(f"📁 생성된 폴더 구조: {len(structure)} 개 최상위 폴더")
        info = workspace_integration['integration_info']
        print(f"📚 포함된 개념: {info['total_concepts']}개")
        print(f"💻 포함된 예제: {info['examples_included']}개")
        print(f"🎯 포함된 실습: {info['exercises_included']}개")
    else:
        print(f"❌ 워크스페이스 통합 실패: {workspace_integration.get('error', '알 수 없는 오류')}")
    print()
    
    # 7. 전체 시스템 통계 테스트
    print("7️⃣ 시스템 통계 테스트")
    print("-" * 40)
    
    system_stats = guide.get_learning_statistics()
    print(f"👥 총 사용자 수: {system_stats['total_users']}")
    print(f"🌐 지원 언어 수: {system_stats['supported_languages']}")
    print(f"📚 총 학습 경로 수: {system_stats['total_learning_paths']}")
    print(f"⭐ 인기 언어: {system_stats['system_statistics']['most_popular_language']}")
    print(f"📊 평균 진도율: {system_stats['system_statistics']['average_progress']:.1f}%")
    print()
    
    # 8. 사용자별 통계 테스트
    print("8️⃣ 사용자별 통계 테스트")
    print("-" * 40)
    
    user_stats = guide.get_learning_statistics(user_id)
    if 'error' not in user_stats:
        print(f"👤 사용자: {user_stats['user_id']}")
        print(f"📚 학습 중인 언어: {', '.join(user_stats['languages_studied'])}")
        print(f"✅ 완료한 총 개념: {user_stats['total_concepts_completed']}개")
        
        for lang, details in user_stats['language_details'].items():
            print(f"  🐍 {lang}: {details['progress_percentage']:.1f}% ({details['completed_concepts']}/{details['total_concepts']})")
    print()
    
    print("=" * 60)
    print("🎉 모든 테스트 완료!")
    print("=" * 60)

if __name__ == "__main__":
    test_educational_guide() 