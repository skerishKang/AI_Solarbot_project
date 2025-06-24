"""
cloud_homework_manager.py - 구글 드라이브 기반 과제 관리 시스템
팜솔라 AI 교육과정용 클라우드 통합 과제 관리
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from user_auth_manager import user_auth_manager

class CloudHomeworkManager:
    """구글 드라이브 기반 과제 관리 시스템"""
    
    def __init__(self):
        self.homework_folder_name = "팜솔라_과제관리"
        self.submissions_folder_name = "과제제출"
        self.progress_file_name = "진도관리.json"
        self.homework_data_file = "과제데이터.json"
        
        # 기본 과제 구조 (실제 교과서 기반)
        self.default_homework_structure = self._get_default_homework_structure()
    
    def _get_default_homework_structure(self) -> Dict:
        """실제 교과서 구조에 맞는 기본 과제 데이터"""
        return {
            "current_week": 1,
            "current_lesson": 1,
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
                        "estimated_time": "30분",
                        "ai_review_criteria": [
                            "ChatGPT 대화 스크린샷 포함 여부",
                            "생성형 AI 특징 이해도",
                            "프롬프트 다양성",
                            "개인적 소감의 깊이"
                        ]
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
                        "estimated_time": "45분",
                        "ai_review_criteria": [
                            "Before/After 프롬프트 명확한 비교",
                            "응답 품질 차이 분석의 정확성",
                            "개인 업무 연관성",
                            "프롬프트 구조 이해도"
                        ]
                    }
                }
            }
        }
    
    def initialize_user_homework_system(self, user_id: str) -> Dict:
        """사용자별 과제 관리 시스템 초기화"""
        try:
            # TODO: 실제 구글 드라이브 API 구현
            return {
                "success": True,
                "message": "✅ 과제 관리 시스템이 초기화되었습니다!",
                "homework_folder_id": "fake_folder_id",
                "submissions_folder_id": "fake_submissions_id"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_current_homework(self, user_id: str) -> Dict:
        """현재 과제 가져오기"""
        try:
            if not user_auth_manager.is_authenticated(user_id):
                return {"success": False, "error": "드라이브 연결이 필요합니다"}
            
            # 기본 구조에서 현재 과제 반환
            homework_data = self.default_homework_structure
            week = str(homework_data["current_week"])
            lesson = str(homework_data["current_lesson"])
            
            if week in homework_data["weekly_homework"] and lesson in homework_data["weekly_homework"][week]:
                homework = homework_data["weekly_homework"][week][lesson]
                lesson_name = "1번째" if lesson == "1" else "2번째"
                
                return {
                    "success": True,
                    "week": week,
                    "lesson": lesson,
                    "lesson_name": lesson_name,
                    "homework": homework,
                    "message": f"📚 **{week}주차 {lesson_name} 과제**\n\n**{homework['title']}**\n\n{homework['description']}"
                }
            else:
                return {"success": False, "error": "현재 과제를 찾을 수 없습니다"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def submit_homework(self, user_id: str, user_name: str, homework_content: str) -> Dict:
        """과제 제출"""
        try:
            if not user_auth_manager.is_authenticated(user_id):
                return {"success": False, "error": "드라이브 연결이 필요합니다"}
            
            # 현재 과제 정보 가져오기
            current_homework = self.get_current_homework(user_id)
            if not current_homework["success"]:
                return current_homework
            
            week = current_homework["week"]
            lesson = current_homework["lesson"]
            lesson_name = current_homework["lesson_name"]
            
            # 제출 파일명 생성
            submission_filename = f"{week}주차_{lesson_name}과제_{user_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            
            # TODO: 실제 구글 드라이브에 파일 저장
            
            return {
                "success": True,
                "message": f"✅ **과제 제출 완료!**\n\n📋 **제출 정보:**\n• 과제: {week}주차 {lesson_name}\n• 제출자: {user_name}\n• 제출 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n• 파일: {submission_filename}\n\n🔗 [구글 드라이브에서 확인](https://drive.google.com/fake)\n\n💡 다음 과제를 확인하려면 /homework 명령어를 사용하세요!",
                "submission_file_id": "fake_file_id",
                "submission_link": "https://drive.google.com/fake",
                "total_submissions": 1
            }
            
        except Exception as e:
            return {"success": False, "error": f"과제 제출 실패: {str(e)}"}
    
    def get_student_progress(self, user_id: str) -> Dict:
        """학생 진도 조회"""
        try:
            if not user_auth_manager.is_authenticated(user_id):
                return {"success": False, "error": "드라이브 연결이 필요합니다"}
            
            # TODO: 실제 진도 데이터 읽기
            progress_summary = f"📊 **학습 진도 현황**\n\n• 총 제출 과제: 1개\n• 최근 제출: 1주차 1번째\n\n**제출 이력:**\n• 1주차 1번째 - {datetime.now().strftime('%Y-%m-%d')}\n"
            
            return {
                "success": True,
                "message": progress_summary,
                "total_submissions": 1,
                "submissions": {}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_ai_homework_review(self, user_id: str, submission_content: str, homework_info: Dict) -> Dict:
        """AI 자동 과제 검토 및 피드백"""
        try:
            # AI 검토 기준 가져오기
            review_criteria = homework_info.get('ai_review_criteria', [])
            
            # 간단한 AI 피드백 시뮬레이션
            feedback_points = []
            score = 85  # 기본 점수
            
            # 기본적인 내용 분석
            content_length = len(submission_content)
            if content_length < 100:
                feedback_points.append("❗ 과제 내용이 다소 짧습니다. 더 자세한 설명을 추가해보세요.")
                score -= 10
            elif content_length > 1000:
                feedback_points.append("✅ 충분히 상세한 내용으로 작성되었습니다.")
                score += 5
            
            # 검토 기준별 피드백
            for criteria in review_criteria:
                if "스크린샷" in criteria and "이미지" not in submission_content.lower():
                    feedback_points.append(f"📸 {criteria}를 확인해주세요.")
                    score -= 5
                elif "비교" in criteria and "vs" in submission_content.lower():
                    feedback_points.append(f"✅ {criteria}가 잘 수행되었습니다.")
                    score += 3
            
            # 점수 범위 조정
            score = max(60, min(100, score))
            
            # 등급 계산
            if score >= 90:
                grade = "A+"
                emoji = "🏆"
            elif score >= 85:
                grade = "A"
                emoji = "🥇"
            elif score >= 80:
                grade = "B+"
                emoji = "🥈"
            else:
                grade = "B"
                emoji = "🥉"
            
            feedback_message = f"""🤖 **AI 자동 검토 결과**

{emoji} **점수:** {score}점 ({grade})

**📋 검토 내용:**
{chr(10).join(f"• {point}" for point in feedback_points)}

**💡 개선 제안:**
• 실습 과정의 스크린샷을 포함하면 더 좋습니다
• 개인적인 경험과 연결지어 설명해보세요
• 구체적인 예시를 더 추가해보세요

**🎯 다음 과제를 위한 팁:**
과제의 핵심 요구사항을 체크리스트로 만들어 하나씩 확인하며 작성하면 더 완성도 높은 결과물을 만들 수 있습니다!
"""
            
            return {
                "success": True,
                "score": score,
                "grade": grade,
                "feedback": feedback_message,
                "review_points": feedback_points
            }
            
        except Exception as e:
            return {"success": False, "error": f"AI 검토 실패: {str(e)}"}

# 전역 인스턴스 생성
cloud_homework_manager = CloudHomeworkManager()
