"""
homework_manager.py - 팜솔라 AI 교육과정 과제 관리 시스템 (완전 클라우드 기반)
구글 드라이브 전용 - 로컬 파일 접근 없음
"""

import json
import io
from datetime import datetime
from typing import Dict, List, Optional
from src.google_drive_handler import drive_handler
from src.user_drive_manager import user_drive_manager

class HomeworkManager:
    def __init__(self):
        # 완전 클라우드 기반: 구글 드라이브에만 데이터 저장
        self.homework_folder_name = "팜솔라_과제관리_시스템"
        self.homework_data_file = "homework_data.json"
        self.homework_data = None
        
    def ensure_homework_folder(self) -> str:
        """과제 관리 폴더 확인/생성"""
        try:
            if not drive_handler.authenticate():
                raise Exception("구글 드라이브 인증 실패")
            
            # 기존 폴더 검색
            query = f"name='{self.homework_folder_name}' and mimeType='application/vnd.google-apps.folder'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # 폴더 생성
            folder_metadata = {
                'name': self.homework_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive_handler.service.files().create(body=folder_metadata, fields='id').execute()
            return folder.get('id')
            
        except Exception as e:
            raise Exception(f"과제 폴더 생성 실패: {str(e)}")
    
    def load_homework_data(self) -> Dict:
        """구글 드라이브에서 과제 데이터 로드"""
        try:
            folder_id = self.ensure_homework_folder()
            
            # 데이터 파일 검색
            query = f"name='{self.homework_data_file}' and parents in '{folder_id}'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                # 기존 파일 읽기
                file_id = files[0]['id']
                content = drive_handler.service.files().get_media(fileId=file_id).execute()
                return json.loads(content.decode('utf-8'))
            else:
                # 초기 데이터 생성
                return self.initialize_homework_data()
                
        except Exception as e:
            print(f"과제 데이터 로드 실패: {e}")
            return self.initialize_homework_data()
    
    def save_homework_data(self):
        """구글 드라이브에 과제 데이터 저장"""
        try:
            folder_id = self.ensure_homework_folder()
            content = json.dumps(self.homework_data, ensure_ascii=False, indent=2)
            
            # 기존 파일 검색
            query = f"name='{self.homework_data_file}' and parents in '{folder_id}'"
            results = drive_handler.service.files().list(q=query, fields='files(id, name)').execute()
            files = results.get('files', [])
            
            if files:
                # 기존 파일 업데이트
                file_id = files[0]['id']
                media_body = drive_handler.MediaIoBaseUpload(
                    io.BytesIO(content.encode('utf-8')),
                    mimetype='application/json'
                )
                drive_handler.service.files().update(
                    fileId=file_id,
                    media_body=media_body
                ).execute()
            else:
                # 새 파일 생성
                file_metadata = {
                    'name': self.homework_data_file,
                    'parents': [folder_id]
                }
                media_body = drive_handler.MediaIoBaseUpload(
                    io.BytesIO(content.encode('utf-8')),
                    mimetype='application/json'
                )
                drive_handler.service.files().create(
                    body=file_metadata,
                    media_body=media_body,
                    fields='id'
                ).execute()
                
        except Exception as e:
            print(f"과제 데이터 저장 실패: {e}")
    
    def get_homework_data(self) -> Dict:
        """과제 데이터 반환 (캐시 사용)"""
        if self.homework_data is None:
            self.homework_data = self.load_homework_data()
        return self.homework_data
    
    def initialize_homework_data(self) -> Dict:
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
        
        # 구글 드라이브에 초기 데이터 저장
        self.homework_data = data
        self.save_homework_data()
        return data
    
    def get_current_homework(self) -> dict:
        """현재 과제 반환"""
        data = self.get_homework_data()
        week = str(data["current_week"])
        lesson = str(data["current_lesson"])
        
        if week in data["weekly_homework"]:
            if lesson in data["weekly_homework"][week]:
                homework = data["weekly_homework"][week][lesson]
                return {
                    "week": week,
                    "lesson": lesson,
                    "homework": homework
                }
        
        return None
    
    def advance_week(self) -> str:
        """진도 진행 - 1번째 → 2번째 → 다음주 1번째"""
        data = self.get_homework_data()
        current_week = data["current_week"]
        current_lesson = data["current_lesson"]
        
        if current_lesson == 1:
            data["current_lesson"] = 2
        else:
            data["current_week"] += 1
            data["current_lesson"] = 1
        
        self.save_homework_data()
        
        new_week = data["current_week"]
        new_lesson = data["current_lesson"]
        
        lesson_name = "1번째" if new_lesson == 1 else "2번째"
        prev_lesson_name = "1번째" if current_lesson == 1 else "2번째"
        
        return f"📅 진도 업데이트: {current_week}주차 {prev_lesson_name} → {new_week}주차 {lesson_name}"
    
    def submit_homework(self, user_id: str, user_name: str, homework_content: str) -> str:
        """과제 제출"""
        data = self.get_homework_data()
        
        if user_id not in data["student_progress"]:
            data["student_progress"][user_id] = {
                "name": user_name,
                "submissions": {},
                "total_submissions": 0
            }
        
        week = data["current_week"]
        lesson = data["current_lesson"]
        submission_key = f"{week}_{lesson}"
        lesson_name = "1번째" if lesson == 1 else "2번째"
        
        submission_data = {
            "content": homework_content,
            "submitted_at": datetime.now().isoformat(),
            "week": week,
            "lesson": lesson,
            "status": "submitted"
        }
        
        data["student_progress"][user_id]["submissions"][submission_key] = submission_data
        data["student_progress"][user_id]["total_submissions"] += 1
        
        self.save_homework_data()
        
        return f"""✅ **과제 제출 완료!**

👤 **제출자**: {user_name}
📅 **과제**: {week}주차 {lesson_name}
⏰ **제출 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
📝 **총 제출 횟수**: {data["student_progress"][user_id]["total_submissions"]}회

🎯 **다음 단계**: 
강사의 피드백을 기다려주세요! 
/progress 명령어로 진도를 확인할 수 있습니다."""

    def get_homework_by_week(self, week: int, lesson: int = None) -> dict:
        """특정 주차 과제 조회"""
        data = self.get_homework_data()
        week_str = str(week)
        
        if week_str in data["weekly_homework"]:
            if lesson is None:
                return {
                    "week": week,
                    "homework": data["weekly_homework"][week_str]
                }
            else:
                lesson_str = str(lesson)
                if lesson_str in data["weekly_homework"][week_str]:
                    return {
                        "week": week,
                        "lesson": lesson,
                        "homework": data["weekly_homework"][week_str][lesson_str]
                    }
        
        return None

    def get_student_progress(self, user_id: str) -> dict:
        """학생 진도 조회"""
        data = self.get_homework_data()
        return data["student_progress"].get(user_id, {
            "name": "Unknown",
            "submissions": {},
            "total_submissions": 0
        })

    def get_submission_stats(self) -> dict:
        """제출 통계"""
        data = self.get_homework_data()
        total_students = len(data["student_progress"])
        total_submissions = sum(
            student["total_submissions"] 
            for student in data["student_progress"].values()
        )
        
        current_week = data["current_week"]
        current_lesson = data["current_lesson"]
        current_key = f"{current_week}_{current_lesson}"
        
        current_submissions = sum(
            1 for student in data["student_progress"].values()
            if current_key in student["submissions"]
        )
        
        return {
            "total_students": total_students,
            "total_submissions": total_submissions,
            "current_week": current_week,
            "current_lesson": current_lesson,
            "current_submissions": current_submissions,
            "submission_rate": (current_submissions / total_students * 100) if total_students > 0 else 0
        }

    def get_random_practice_homework(self) -> dict:
        """연습용 랜덤 과제"""
        import random
        
        practice_homeworks = [
            {
                "title": "AI 활용 아이디어 브레인스토밍",
                "description": """💡 **창의적 사고 연습**

🎯 목표: AI를 활용한 혁신적 아이디어 발굴

📝 실습:
1. 본인 업무/관심 분야에서 AI 활용 가능한 영역 3가지 찾기
2. 각 영역별로 구체적인 AI 솔루션 아이디어 제시
3. 실현 가능성과 기대 효과 분석

⏰ 예상 시간: 45분""",
                "difficulty": "중급",
                "estimated_time": "45분"
            },
            {
                "title": "프롬프트 엔지니어링 마스터",
                "description": """🚀 **고급 프롬프트 기법 연습**

🎯 목표: 효과적인 프롬프트 작성 능력 향상

📝 실습:
1. 체인 오브 쏘트(Chain-of-Thought) 프롬프트 작성
2. 퓨샷 러닝(Few-shot Learning) 예제 설계
3. 역할 기반 프롬프트 최적화

⏰ 예상 시간: 60분""",
                "difficulty": "고급",
                "estimated_time": "60분"
            }
        ]
        
        return random.choice(practice_homeworks)

# 전역 인스턴스 (구글 드라이브 기반)
homework_manager = HomeworkManager()
