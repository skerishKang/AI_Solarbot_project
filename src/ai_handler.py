"""
AI_Solarbot - Gemini/ChatGPT 통합 AI 핸들러
Gemini 우선 사용, 무료 한도 초과시 ChatGPT로 자동 전환
"""

import os
import openai
import google.generativeai as genai
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# 사용량 추적 파일
current_dir = os.path.dirname(os.path.abspath(__file__))
USAGE_FILE = os.path.join(current_dir, "usage_tracker.json")

class AIHandler:
    def __init__(self):
        self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        self.usage_data = self.load_usage_data()
        
    def load_usage_data(self):
        """사용량 데이터 로드"""
        try:
            with open(USAGE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "daily_gemini_calls": 0,
                "daily_chatgpt_calls": 0,
                "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
                "total_gemini_calls": 0,
                "total_chatgpt_calls": 0
            }
    
    def save_usage_data(self):
        """사용량 데이터 저장"""
        with open(USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.usage_data, f, ensure_ascii=False, indent=2)
    
    def reset_daily_usage_if_needed(self):
        """날짜가 바뀌면 일일 사용량 리셋"""
        today = datetime.now().strftime("%Y-%m-%d")
        if self.usage_data["last_reset_date"] != today:
            self.usage_data["daily_gemini_calls"] = 0
            self.usage_data["daily_chatgpt_calls"] = 0
            self.usage_data["last_reset_date"] = today
            self.save_usage_data()
    
    async def chat_with_ai(self, message: str, user_name: str = "사용자") -> tuple:
        """AI와 대화 (Gemini 우선, 실패시 ChatGPT)"""
        self.reset_daily_usage_if_needed()
        
        system_prompt = f"""당신은 AI_Solarbot입니다. 
ChatGPT 실무 강의와 팜솔라(태양광) 업무를 도와주는 전문 AI 어시스턴트입니다.

사용자 정보: {user_name}님

응답 가이드라인:
1. 친근하고 전문적인 톤으로 답변
2. 태양광 관련 질문에는 구체적이고 실용적인 정보 제공
3. ChatGPT 실무 활용에 대해서는 실전 경험을 바탕으로 조언
4. 필요시 관련 명령어(/prompt, /solar 등) 안내
5. 답변은 간결하되 충분한 정보 포함
6. 이모지를 적절히 사용하여 친근한 분위기 조성
"""
        
        # 1차: Gemini 시도 (일일 한도: 1500회)
        if self.usage_data["daily_gemini_calls"] < 1400:  # 여유분 100개 남김
            try:
                response = self.gemini_model.generate_content(f"{system_prompt}\n\n사용자 질문: {message}")
                self.usage_data["daily_gemini_calls"] += 1
                self.usage_data["total_gemini_calls"] += 1
                self.save_usage_data()
                
                return response.text.strip(), "🧠 Padiem"
                
            except Exception as e:
                print(f"Gemini API 오류: {str(e)}")
                # Gemini 실패시 ChatGPT로 전환
        
        # 2차: ChatGPT 백업 시도
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",  # 최신 멀티모달 모델 사용
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            self.usage_data["daily_chatgpt_calls"] += 1
            self.usage_data["total_chatgpt_calls"] += 1
            self.save_usage_data()
            
            return response.choices[0].message.content.strip(), "🤖 ChatGPT"
            
        except Exception as e:
            return f"""죄송합니다. AI 서비스에 일시적인 문제가 발생했습니다.

오류 내용: {str(e)}

🔄 잠시 후 다시 시도해주세요.
또는 다음 명령어를 사용해보세요:
• /help - 도움말
• /status - 시스템 상태 확인""", "❌ 오류"

    async def calculate_solar_power(self, capacity_kw: float, location: str = "서울", angle: int = 30) -> tuple:
        """태양광 발전량 계산"""
        prompt = f"""
태양광 발전 전문가로서 다음 조건의 태양광 시스템을 상세히 분석해주세요:

🔧 설치 조건:
- 설치 용량: {capacity_kw}kW
- 설치 지역: {location}
- 설치 각도: {angle}도
- 방향: 남향 (최적)

📊 분석 요청 사항:
1. 연간 예상 발전량 (kWh)
2. 월별 발전량 분포 (계절별 특성 포함)
3. 경제성 분석 (초기 투자비, 연간 수익, 회수 기간)
4. 효율 최적화 방안 3가지
5. 지역별 특성 고려사항

실무에 바로 활용할 수 있도록 구체적인 숫자와 실용적인 조언을 포함해주세요.
"""
        
        try:
            if self.usage_data["daily_gemini_calls"] < 1400:
                response = self.gemini_model.generate_content(prompt)
                self.usage_data["daily_gemini_calls"] += 1
                self.usage_data["total_gemini_calls"] += 1
                self.save_usage_data()
                
                return f"🌞 태양광 발전량 분석 결과\n\n{response.text.strip()}", "🧠 Padiem"
            else:
                # ChatGPT 백업
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "당신은 태양광 발전 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1200,
                    temperature=0.3
                )
                
                self.usage_data["daily_chatgpt_calls"] += 1
                self.usage_data["total_chatgpt_calls"] += 1
                self.save_usage_data()
                
                return f"🌞 태양광 발전량 분석 결과\n\n{response.choices[0].message.content.strip()}", "🤖 ChatGPT"
                
        except Exception as e:
            return f"""태양광 계산 중 오류가 발생했습니다: {str(e)}

📊 기본 계산 (근사치):
• {capacity_kw}kW 시스템
• {location} 기준 예상 발전량
• 연간: {capacity_kw * 1300:,.0f}kWh
• 월평균: {capacity_kw * 1300/12:,.0f}kWh
• 예상 연간 수익: {capacity_kw * 1300 * 150:,.0f}원

더 정확한 계산은 시스템 복구 후 가능합니다.""", "❌ 오류"

    async def generate_prompt_template(self, topic: str) -> tuple:
        """주제별 프롬프트 템플릿 생성"""
        prompt = f"""
"{topic}" 관련 업무에 사용할 수 있는 효과적인 ChatGPT 프롬프트 템플릿을 3개 만들어주세요.

각 템플릿은 다음 구조로 작성해주세요:
1. 🎯 역할 설정 - "당신은 ~전문가입니다"
2. 📝 구체적 지시사항 - "다음 작업을 해주세요"
3. 📋 출력 형식 지정 - "결과를 ~형태로 정리해주세요"
4. ⚙️ 추가 조건 (필요시)

실무에서 바로 복사해서 사용할 수 있도록 완성된 형태로 제공해주세요.
각 템플릿에는 사용 예시도 포함해주세요.
"""
        
        try:
            if self.usage_data["daily_gemini_calls"] < 1400:
                response = self.gemini_model.generate_content(prompt)
                self.usage_data["daily_gemini_calls"] += 1
                self.usage_data["total_gemini_calls"] += 1
                self.save_usage_data()
                
                return f"📝 '{topic}' 프롬프트 템플릿\n\n{response.text.strip()}", "🧠 Padiem"
            else:
                # ChatGPT 백업
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "당신은 ChatGPT 프롬프트 엔지니어링 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1200,
                    temperature=0.5
                )
                
                self.usage_data["daily_chatgpt_calls"] += 1
                self.usage_data["total_chatgpt_calls"] += 1
                self.save_usage_data()
                
                return f"📝 '{topic}' 프롬프트 템플릿\n\n{response.choices[0].message.content.strip()}", "🤖 ChatGPT"
                
        except Exception as e:
            return f"""프롬프트 템플릿 생성 중 오류가 발생했습니다: {str(e)}

📋 기본 '{topic}' 템플릿:
당신은 {topic} 전문가입니다.
다음 작업을 도와주세요: [구체적 요청]
결과를 다음 형식으로 정리해주세요:
1. 핵심 요약
2. 상세 내용  
3. 실행 방안

/template 명령어로 더 많은 템플릿을 확인하세요.""", "❌ 오류"
    
    async def explain_homework(self, homework_content: str, user_name: str = "사용자") -> tuple:
        """과제 내용을 분석하여 자세한 설명 생성"""
        self.reset_daily_usage_if_needed()
        
        system_prompt = f"""당신은 팜솔라 ChatGPT 실무 교육 전문 강사입니다.
주어진 과제 내용을 분석하여 학생들이 이해하기 쉽도록 자세한 설명을 제공해주세요.

사용자 정보: {user_name}님

설명 가이드라인:
1. 과제의 목적과 학습 목표 명확히 설명
2. 단계별 풀이 방법 제시
3. 실무 활용 예시 포함
4. 주의사항과 팁 제공
5. 예상 소요시간과 난이도 안내
6. 친근하고 격려적인 톤 유지

출력 형식:
📚 과제 개요
🎯 학습 목표  
📋 단계별 가이드
💡 실무 활용 팁
⚠️ 주의사항
⏱️ 예상 소요시간
🌟 성공 포인트
"""
        
        # 1차: Gemini 시도
        if self.usage_data["daily_gemini_calls"] < 1400:
            try:
                prompt = f"{system_prompt}\n\n분석할 과제 내용:\n{homework_content}"
                response = self.gemini_model.generate_content(prompt)
                self.usage_data["daily_gemini_calls"] += 1
                self.usage_data["total_gemini_calls"] += 1
                self.save_usage_data()
                
                return response.text.strip(), "🧠 Padiem"
                
            except Exception as e:
                print(f"Gemini API 오류: {str(e)}")
        
        # 2차: ChatGPT 백업
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"다음 과제를 자세히 설명해주세요:\n\n{homework_content}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            self.usage_data["daily_chatgpt_calls"] += 1
            self.usage_data["total_chatgpt_calls"] += 1
            self.save_usage_data()
            
            return response.choices[0].message.content.strip(), "🤖 ChatGPT"
            
        except Exception as e:
            return f"""과제 설명 생성 중 오류가 발생했습니다: {str(e)}

📚 기본 과제 가이드:
1. 과제 내용을 천천히 읽어보세요
2. 요구사항을 정확히 파악하세요  
3. 단계별로 차근차근 진행하세요
4. 실무 상황을 상상하며 작성하세요
5. 완료 후 검토해보세요

💡 도움이 필요하면 /help 명령어를 사용하세요.""", "❌ 오류"

    def get_usage_stats(self) -> dict:
        """사용량 통계 반환"""
        self.reset_daily_usage_if_needed()
        return {
            "daily_gemini": self.usage_data["daily_gemini_calls"],
            "daily_chatgpt": self.usage_data["daily_chatgpt_calls"],
            "total_gemini": self.usage_data["total_gemini_calls"],
            "total_chatgpt": self.usage_data["total_chatgpt_calls"],
            "gemini_remaining": max(0, 1400 - self.usage_data["daily_gemini_calls"]),
            "date": self.usage_data["last_reset_date"]
        }

def test_api_connection() -> dict:
    """API 연결 상태 테스트"""
    results = {
        "gemini": False,
        "openai": False,
        "error_messages": []
    }
    
    # Gemini 테스트
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Hello")
        results["gemini"] = True
    except Exception as e:
        results["error_messages"].append(f"Gemini 오류: {str(e)}")
    
    # OpenAI 테스트
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        results["openai"] = True
    except Exception as e:
        results["error_messages"].append(f"OpenAI 오류: {str(e)}")
    
    return results

# 전역 AI 핸들러 인스턴스
ai_handler = AIHandler()
