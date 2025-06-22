"""
AI_Solarbot - 팜솔라 과제 관리 시스템 (실제 교과서 구조 반영)
"""

import os
import json
from datetime import datetime, timedelta
import random

class HomeworkManager:
    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.homework_file = os.path.join(current_dir, "homework_data.json")
        self.base_path = "G:\\Ddrive\\BatangD\\task\\workdiary\\36. 팜솔라\\수업"
        self.homework_data = self.load_homework_data()
        
    def load_homework_data(self):
        """과제 데이터 로드"""
        try:
            with open(self.homework_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.initialize_homework_data()
    
    def save_homework_data(self):
        """과제 데이터 저장"""
        with open(self.homework_file, 'w', encoding='utf-8') as f:
            json.dump(self.homework_data, f, ensure_ascii=False, indent=2)
    
    def initialize_homework_data(self):
        """실제 교과서 구조에 맞는 초기 과제 데이터"""
        data = {
            "current_week": 1,
            "current_lesson": 1,  # 1번째, 2번째 방식
            "student_progress": {},
            "weekly_homework": {
                "1": {
                    "1": {
                        "title": "생성형 AI와 ChatGPT 기초 이해",
                        "description": """🎯 1주차 1번째 과제

📚 실제 교과서 기반 과제

📝 실습 내용:
1. ChatGPT 계정 생성 및 첫 대화
   - ChatGPT 무료/유료 차이 체험
   - 기본 인터페이스 익히기

2. 생성형 AI vs 기존 AI 차이점 정리
   - 분류/예측 AI와 생성 AI 비교
   - 실제 사용해본 경험 작성

3. 첫 프롬프트 실습
   - 자기소개서 도움 요청
   - 저녁 메뉴 추천 요청
   - 반말/존댓말 차이 체험

📤 제출 방법:
1. 실습한 프롬프트와 ChatGPT 응답 복사
2. 생성형 AI에 대한 소감 3줄 작성
3. /submit 명령어로 제출

⏰ 난이도: 기초
⏰ 예상 시간: 30분""",
                        "difficulty": "기초",
                        "estimated_time": "30분"
                    },
                    "2": {
                        "title": "ChatGPT와 대화 잘하기",
                        "description": """🎯 1주차 2번째 과제

📚 실제 교과서 기반 과제

📝 실습 내용:
1. 좋은 질문 vs 나쁜 질문 비교
   - "회의 정리해줘" vs 구체적 요청
   - 역할/작업/출력 형식 3요소 실습

2. 프롬프트 품질 비교 실험
   - 같은 주제로 3가지 방식 질문
   - 응답 품질 차이 분석

3. 개인 업무 맞춤 프롬프트 작성
   - 본인 업무에 적용 가능한 프롬프트 설계
   - 역할 설정의 중요성 체험

📤 제출 방법:
1. Before/After 프롬프트 비교 (3세트)
2. 각 응답의 차이점 분석
3. 가장 효과적이었던 프롬프트 1개 선정

⏰ 난이도: 기초
⏰ 예상 시간: 45분""",
                        "difficulty": "기초",
                        "estimated_time": "45분"
                    }
                },
                "2": {
                    "1": {
                        "title": "고급 프롬프트 구조 설계",
                        "description": """🎯 2주차 1번째 과제

📝 실습 내용:
1. 2단계 프롬프트 체인 설계
2. 조건부 응답 프롬프트 작성
3. 복잡한 업무 상황 해결 프롬프트

💡 도전 과제:
회사에서 실제 발생할 수 있는 복잡한 상황을 설정하고, 이를 해결하는 다단계 프롬프트를 설계해보세요.

📤 제출: 실무 적용 프롬프트와 결과

⏰ 난이도: 중급
⏰ 예상 시간: 60분""",
                        "difficulty": "중급",
                        "estimated_time": "60분"
                    },
                    "2": {
                        "title": "프롬프트 마스터 대결 준비",
                        "description": """🎯 2주차 2번째 과제

📝 실습 내용:
1. 창의적인 프롬프트 기법 연구
2. 팀 대결을 위한 전략 수립
3. 다양한 업무 시나리오 대응 프롬프트 준비

🏆 대결 준비:
수업 시간에 진행될 '프롬프트 마스터 대결'을 위해 자신만의 필살기 프롬프트를 준비해오세요!

📤 제출: 자신만의 프롬프트 기법과 예시

⏰ 난이도: 중급
⏰ 예상 시간: 90분""",
                        "difficulty": "중급",
                        "estimated_time": "90분"
                    }
                }
            }
        }
        
        with open(self.homework_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return data
    
    def get_current_homework(self) -> dict:
        """현재 과제 반환"""
        week = str(self.homework_data["current_week"])
        lesson = str(self.homework_data["current_lesson"])
        
        if week in self.homework_data["weekly_homework"]:
            if lesson in self.homework_data["weekly_homework"][week]:
                homework = self.homework_data["weekly_homework"][week][lesson]
                return {
                    "week": week,
                    "lesson": lesson,
                    "homework": homework
                }
        
        return None
    
    def advance_week(self) -> str:
        """진도 진행 - 1번째 → 2번째 → 다음주 1번째"""
        current_week = self.homework_data["current_week"]
        current_lesson = self.homework_data["current_lesson"]
        
        if current_lesson == 1:
            self.homework_data["current_lesson"] = 2
        else:
            self.homework_data["current_week"] += 1
            self.homework_data["current_lesson"] = 1
        
        self.save_homework_data()
        
        new_week = self.homework_data["current_week"]
        new_lesson = self.homework_data["current_lesson"]
        
        lesson_name = "1번째" if new_lesson == 1 else "2번째"
        prev_lesson_name = "1번째" if current_lesson == 1 else "2번째"
        
        return f"📅 진도 업데이트: {current_week}주차 {prev_lesson_name} → {new_week}주차 {lesson_name}"
    
    def submit_homework(self, user_id: str, user_name: str, homework_content: str) -> str:
        """과제 제출"""
        if user_id not in self.homework_data["student_progress"]:
            self.homework_data["student_progress"][user_id] = {
                "name": user_name,
                "submissions": {},
                "total_submissions": 0
            }
        
        week = self.homework_data["current_week"]
        lesson = self.homework_data["current_lesson"]
        submission_key = f"{week}_{lesson}"
        lesson_name = "1번째" if lesson == 1 else "2번째"
        
        submission_data = {
            "content": homework_content,
            "submitted_at": datetime.now().isoformat(),
            "week": week,
            "lesson": lesson,
            "status": "submitted"
        }
        
        self.homework_data["student_progress"][user_id]["submissions"][submission_key] = submission_data
        self.homework_data["student_progress"][user_id]["total_submissions"] += 1
        
        self.save_homework_data()
        
        return f"""✅ 과제 제출 완료!

📚 제출 정보:
• 과제: {week}주차 {lesson_name}
• 제출 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}
• 총 제출 횟수: {self.homework_data["student_progress"][user_id]["total_submissions"]}회

🎉 수고하셨습니다! 피드백은 강사님 확인 후 제공드립니다."""
    
    def get_homework_by_week(self, week: int, lesson: int = None) -> dict:
        """특정 주차 과제 반환"""
        week_str = str(week)
        
        if week_str not in self.homework_data["weekly_homework"]:
            return {"error": f"{week}주차 과제가 없습니다."}
        
        if lesson:
            lesson_str = str(lesson)
            lesson_name = "1번째" if lesson == 1 else "2번째"
            if lesson_str in self.homework_data["weekly_homework"][week_str]:
                return {
                    "week": week_str,
                    "lesson": lesson_str,
                    "lesson_name": lesson_name,
                    "homework": self.homework_data["weekly_homework"][week_str][lesson_str]
                }
            else:
                return {"error": f"{week}주차 {lesson_name} 과제가 없습니다."}
        else:
            return {
                "week": week_str,
                "all_lessons": self.homework_data["weekly_homework"][week_str]
            }
    
    def get_student_progress(self, user_id: str) -> dict:
        """학생 진도 확인"""
        if user_id not in self.homework_data["student_progress"]:
            return {"error": "아직 제출한 과제가 없습니다."}
        
        return self.homework_data["student_progress"][user_id]
    
    def get_submission_stats(self) -> dict:
        """전체 제출 통계 (관리자용)"""
        total_students = len(self.homework_data["student_progress"])
        current_week = self.homework_data["current_week"]
        current_lesson = self.homework_data["current_lesson"]
        current_key = f"{current_week}_{current_lesson}"
        
        submitted_count = 0
        for user_data in self.homework_data["student_progress"].values():
            if current_key in user_data["submissions"]:
                submitted_count += 1
        
        submission_rate = (submitted_count / total_students * 100) if total_students > 0 else 0
        lesson_name = "1번째" if current_lesson == 1 else "2번째"
        
        return {
            "total_students": total_students,
            "current_homework": f"{current_week}주차 {lesson_name}",
            "submitted_count": submitted_count,
            "submission_rate": round(submission_rate, 1)
        }
    
    def get_random_practice_homework(self) -> dict:
        """랜덤 연습 과제 생성"""
        practice_topics = [
            {
                "title": "태양광 발전량 계산 프롬프트",
                "description": """🌞 연습: 태양광 전문가 되어보기

📝 과제:
태양광 발전 전문가 역할로 발전량 계산 프롬프트를 작성하세요:
- 용량: 100kW
- 지역: 본인 거주 지역
- 설치조건: 자유 설정

💡 포함사항:
1. 전문가 역할 설정
2. 구체적 계산 요청  
3. 결과 형식 지정
4. 경제성 분석 요청

📤 제출: 프롬프트와 AI 응답""",
                "difficulty": "실전",
                "estimated_time": "45분"
            }
        ]
        
        return random.choice(practice_topics)
